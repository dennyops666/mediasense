from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.decorators import method_decorator
from asgiref.sync import async_to_sync, sync_to_async
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from django.views.decorators.csrf import csrf_exempt
import asyncio
import json
import openai
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSetMixin
from rest_framework.parsers import JSONParser
import logging
from django.db import transaction

from news.models import NewsArticle

from .models import (
    AnalysisNotification,
    AnalysisResult,
    AnalysisRule,
    AnalysisSchedule,
    AnalysisVisualization,
    BatchAnalysisResult,
    BatchAnalysisTask,
    NotificationSubscription,
    ScheduleExecution,
)
from .serializers import (
    AnalysisNotificationSerializer,
    AnalysisResultSerializer,
    AnalysisRuleSerializer,
    AnalysisScheduleSerializer,
    AnalysisVisualizationSerializer,
    BatchAnalysisResultSerializer,
    BatchAnalysisTaskSerializer,
    NotificationSubscriptionSerializer,
    ScheduleExecutionSerializer,
)
from .services import AIService, RateLimitExceeded, VisualizationService
from .tasks import process_batch_analysis, process_schedule_execution

logger = logging.getLogger(__name__)

class AsyncViewSet(viewsets.GenericViewSet):
    renderer_classes = [JSONRenderer]
    parser_classes = [JSONParser]

    def initialize_request(self, request, *args, **kwargs):
        """
        初始化请求对象，确保它具有所需的属性
        """
        request = super().initialize_request(request, *args, **kwargs)
        if not hasattr(request, 'data'):
            request.data = {}
        return request

    def dispatch(self, request, *args, **kwargs):
        request = self.initialize_request(request, *args, **kwargs)
        if request.method.lower() in self.http_method_names:
            handler = getattr(self, request.method.lower(), self.http_method_not_allowed)
        else:
            handler = self.http_method_not_allowed

        if asyncio.iscoroutinefunction(handler):
            response = async_to_sync(handler)(request, *args, **kwargs)
        else:
            response = handler(request, *args, **kwargs)

        if asyncio.iscoroutine(response):
            response = async_to_sync(lambda: response)()

        if isinstance(response, (dict, list)):
            response = Response(response)
        elif isinstance(response, JsonResponse):
            response = Response(response.content)

        if not hasattr(response, 'accepted_renderer'):
            response.accepted_renderer = self.renderer_classes[0]()
            response.accepted_media_type = "application/json"
            response.renderer_context = {}

        return response

    def handle_exception(self, exc):
        """处理异常"""
        if isinstance(exc, NewsArticle.DoesNotExist):
            return Response(
                {'error': 'not_found', 'detail': '新闻不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
        elif isinstance(exc, RateLimitExceeded):
            return Response(
                {'error': 'rate_limit_exceeded', 'detail': str(exc)},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        elif isinstance(exc, openai.RateLimitError):
            return Response(
                {'error': 'rate_limit_exceeded', 'detail': 'API调用次数超限'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        elif isinstance(exc, openai.APIStatusError):
            if exc.response.status == 429:
                return Response(
                    {'error': 'rate_limit_exceeded', 'detail': str(exc)},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            return Response(
                {'error': 'openai_error', 'detail': str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        elif isinstance(exc, ValueError):
            return Response(
                {'error': 'invalid_input', 'detail': str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )
        else:
            return Response(
                {'error': 'internal_error', 'detail': str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@method_decorator(csrf_exempt, name='dispatch')
class AIServiceViewSet(AsyncViewSet):
    """AI服务视图集"""
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ai_service = AIService()
    
    async def list(self, request):
        """获取分析结果列表"""
        results = await sync_to_async(list)(AnalysisResult.objects.filter(news__created_by=request.user))
        serializer = AnalysisResultSerializer(results, many=True)
        return Response(serializer.data)
    
    async def retrieve(self, request, pk=None):
        """获取单个分析结果"""
        try:
            result = await sync_to_async(AnalysisResult.objects.get)(id=pk, news__created_by=request.user)
            serializer = AnalysisResultSerializer(result)
            return Response(serializer.data)
        except AnalysisResult.DoesNotExist:
            return Response({"error": "分析结果不存在"}, status=404)
    
    async def update(self, request, pk=None):
        """更新分析规则"""
        try:
            rule = await sync_to_async(AnalysisRule.objects.get)(id=pk)
            serializer = AnalysisRuleSerializer(rule, data=request.data, partial=True)
            if await sync_to_async(serializer.is_valid)():
                await sync_to_async(serializer.save)()
                return Response(serializer.data)
            return Response(serializer.errors, status=400)
        except AnalysisRule.DoesNotExist:
            return Response({"error": "规则不存在"}, status=404)
    
    async def partial_update(self, request, pk=None):
        """部分更新分析规则"""
        return await self.update(request, pk)
    
    @action(detail=False, methods=["post"])
    async def analyze_article(self, request):
        """分析文章"""
        try:
            article_id = request.data.get("article_id")
            if not article_id:
                return Response({"error": "文章ID不能为空"}, status=400)
            
            news = await sync_to_async(NewsArticle.objects.get)(id=article_id, created_by=request.user)
            if not news.content:
                return Response({"error": "文章内容为空"}, status=400)
            
            analysis_types = request.data.get("analysis_types", [])
            if not analysis_types:
                return Response({"error": "分析类型不能为空"}, status=400)
            
            results = {}
            result_ids = []
            
            for analysis_type in analysis_types:
                # 先检查缓存
                cached_result = await self.ai_service._get_cached_result(article_id, analysis_type)
                if cached_result:
                    results[analysis_type] = json.loads(cached_result)
                    continue
                
                # 调用相应的分析方法
                if analysis_type == 'sentiment':
                    result = await self.ai_service.analyze_sentiment(news.content)
                elif analysis_type == 'keywords':
                    result = await self.ai_service.extract_keywords(news.content)
                elif analysis_type == 'summary':
                    result = await self.ai_service.generate_summary(news.content)
                else:
                    continue
                
                # 缓存结果
                await self.ai_service._cache_result(article_id, analysis_type, json.dumps(result))
                results[analysis_type] = result
                
                # 保存分析结果
                analysis_result = await sync_to_async(AnalysisResult.objects.create)(
                    news=news,
                    analysis_type=analysis_type,
                    result=result,
                    created_by=request.user
                )
                result_ids.append(analysis_result.id)
            
            return Response({
                "message": "分析完成",
                "data": results,
                "result_ids": result_ids,
                "result_id": result_ids[0] if result_ids else None
            })
        except NewsArticle.DoesNotExist:
            return Response({"error": "文章不存在"}, status=404)
    
    @action(detail=True, methods=["get"])
    async def get_analysis_result(self, request, pk=None):
        """获取分析结果"""
        try:
            result = await sync_to_async(AnalysisResult.objects.get)(id=pk)
            return Response({
                "analysis_result": result.result
            })
        except AnalysisResult.DoesNotExist:
            return Response({"error": "分析结果不存在"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"获取分析结果失败: {str(e)}")
            return Response({"error": f"系统错误: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=["post"])
    async def analyze_with_rules(self, request, pk=None):
        """使用规则分析文章"""
        try:
            news = await sync_to_async(NewsArticle.objects.get)(id=pk)
            if not news.content:
                return Response({"error": "文章内容为空"}, status=400)
            
            rule_id = request.data.get("rule_id")
            if not rule_id:
                return Response({"error": "规则ID不能为空"}, status=400)
            
            try:
                rule = await sync_to_async(AnalysisRule.objects.get)(id=rule_id)
            except AnalysisRule.DoesNotExist:
                return Response({"error": "规则不存在"}, status=404)
            
            # 先检查缓存
            cache_key = f"rule_analysis_{pk}_{rule_id}"
            cached_result = await self.ai_service._get_cached_result(pk, cache_key)
            if cached_result:
                return Response(json.loads(cached_result))
            
            # 使用规则进行分析
            result = await self.ai_service.analyze_with_rule(news, rule)
            
            # 缓存结果
            await self.ai_service._cache_result(pk, cache_key, json.dumps(result))
            
            # 保存分析结果
            analysis_result = await sync_to_async(AnalysisResult.objects.create)(
                news=news,
                analysis_type=f"rule_{rule_id}",
                result=json.dumps(result)
            )
            
            return Response({
                "message": "规则分析完成",
                "data": {
                    rule_id: {
                        "success": True,
                        "data": {
                            "content": result,
                            "rule_id": rule.id,
                            "rule_name": rule.name
                        }
                    }
                }
            })
        except NewsArticle.DoesNotExist:
            return Response({"error": "文章不存在"}, status=404)
        except RateLimitExceeded as e:
            return Response({"error": str(e)}, status=429)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)
        except Exception as e:
            return Response({"error": f"系统错误: {str(e)}"}, status=500)
    
    @action(detail=False, methods=["post"])
    async def create_analysis_rule(self, request):
        """创建分析规则"""
        try:
            data = request.data
            if not data.get("name") or not data.get("rule_type"):
                return Response({"error": "规则名称和类型不能为空"}, status=400)
            
            # 创建规则
            rule = await sync_to_async(AnalysisRule.objects.create)(
                name=data["name"],
                description=data.get("description", ""),
                rule_type=data["rule_type"],
                system_prompt=data.get("system_prompt", ""),
                user_prompt_template=data.get("user_prompt_template", ""),
                parameters=data.get("parameters", {}),
                is_active=data.get("is_active", True)
            )
            
            serializer = AnalysisRuleSerializer(rule)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": f"系统错误: {str(e)}"}, status=500)
    
    @action(detail=True, methods=["put"])
    async def update_analysis_rule(self, request, pk=None):
        """更新分析规则"""
        try:
            rule = await sync_to_async(AnalysisRule.objects.get)(id=pk)
            data = request.data
            
            # 更新规则
            for field in ["name", "description", "rule_type", "system_prompt", 
                         "user_prompt_template", "parameters", "is_active"]:
                if field in data:
                    setattr(rule, field, data[field])
            
            await sync_to_async(rule.save)()
            
            serializer = AnalysisRuleSerializer(rule)
            return Response(serializer.data)
        except AnalysisRule.DoesNotExist:
            return Response({"error": "规则不存在"}, status=404)
        except Exception as e:
            return Response({"error": f"系统错误: {str(e)}"}, status=500)
    
    @action(detail=False, methods=["post"])
    async def create_batch_task(self, request):
        """创建批量分析任务"""
        try:
            data = request.data
            if not data.get("name"):
                return Response({"error": "任务名称不能为空"}, status=400)
            
            if not data.get("rule_id"):
                return Response({"error": "规则ID不能为空"}, status=400)
            
            try:
                rule = await sync_to_async(AnalysisRule.objects.get)(id=data["rule_id"])
            except AnalysisRule.DoesNotExist:
                return Response({"error": "规则不存在"}, status=404)
            
            # 创建批量任务
            task = await sync_to_async(BatchAnalysisTask.objects.create)(
                name=data["name"],
                rule=rule,
                status='pending',
                total_count=len(data.get("news_ids", [])),
                processed=0,
                success=0,
                failed=0,
                config={
                    'news_ids': data.get("news_ids", []),
                    'analysis_types': data.get("analysis_types", [])
                },
                created_by=request.user
            )
            
            # 启动异步任务
            process_batch_analysis.delay(task.id)
            
            serializer = BatchAnalysisTaskSerializer(task)
            return Response(serializer.data, status=201)
        except Exception as e:
            return Response({"error": f"系统错误: {str(e)}"}, status=500)
    
    @action(detail=True, methods=["post"])
    async def control(self, request, pk=None):
        """控制批量任务"""
        try:
            task = await sync_to_async(BatchAnalysisTask.objects.get)(id=pk)
            action = request.data.get("action")
            
            if action == "cancel":
                task.status = "cancelled"
                await sync_to_async(task.save)()
            elif action == "retry":
                task.status = "pending"
                await sync_to_async(task.save)()
                # 重新启动任务
                process_batch_analysis.delay(task.id)
            else:
                return Response({"error": "不支持的操作"}, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = BatchAnalysisTaskSerializer(task)
            return Response(serializer.data)
        except BatchAnalysisTask.DoesNotExist:
            return Response({"error": "任务不存在"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"系统错误: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=["post"])
    async def create_analysis_schedule(self, request):
        """创建分析计划"""
        try:
            data = request.data
            if not data.get("name") or not data.get("cron_expression"):
                return Response({"error": "计划名称和cron表达式不能为空"}, status=400)
            
            # 创建计划
            schedule = await sync_to_async(AnalysisSchedule.objects.create)(
                name=data["name"],
                description=data.get("description", ""),
                cron_expression=data["cron_expression"],
                analysis_types=data.get("analysis_types", []),
                rule_id=data.get("rule_id"),
                filter_criteria=data.get("filter_criteria", {}),
                is_active=data.get("is_active", True),
                created_by=request.user
            )
            
            serializer = AnalysisScheduleSerializer(schedule)
            return Response(serializer.data, status=201)
        except Exception as e:
            return Response({"error": f"系统错误: {str(e)}"}, status=500)
    
    @action(detail=True, methods=["post"])
    async def schedule_control(self, request, pk=None):
        """控制分析计划"""
        try:
            schedule = await sync_to_async(AnalysisSchedule.objects.get)(id=pk)
            action = request.data.get("action")
            
            if action == "enable":
                schedule.is_active = True
            elif action == "disable":
                schedule.is_active = False
            else:
                return Response({"error": "不支持的操作"}, status=status.HTTP_400_BAD_REQUEST)
            
            await sync_to_async(schedule.save)()
            
            serializer = AnalysisScheduleSerializer(schedule)
            return Response(serializer.data)
        except AnalysisSchedule.DoesNotExist:
            return Response({"error": "计划不存在"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"系统错误: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=["post"])
    async def notification_management(self, request):
        """管理通知"""
        try:
            if request.user.is_anonymous:
                return Response({"error": "用户未认证"}, status=status.HTTP_401_UNAUTHORIZED)
                
            data = request.data
            action = data.get("action")
            
            if action == "subscribe":
                # 创建订阅
                subscription = await sync_to_async(NotificationSubscription.objects.create)(
                    user=request.user,
                    email_enabled=bool(data.get('email_enabled', False)),
                    websocket_enabled=bool(data.get('websocket_enabled', False)),
                    notify_on_complete=bool(data.get('notify_on_complete', False)),
                    notify_on_error=bool(data.get('notify_on_error', False)),
                    notify_on_batch=bool(data.get('notify_on_batch', False)),
                    notify_on_schedule=bool(data.get('notify_on_schedule', False))
                )
                return Response(NotificationSubscriptionSerializer(subscription).data)
            elif action == "unsubscribe":
                # 删除订阅
                subscription = await sync_to_async(NotificationSubscription.objects.get)(user=request.user)
                await sync_to_async(subscription.delete)()
                return Response({"status": "success"})
            elif action == "mark_read":
                # 标记通知为已读
                if "notification_id" in data:
                    notification = await sync_to_async(AnalysisNotification.objects.get)(
                        id=data["notification_id"],
                        user=request.user
                    )
                    notification.is_read = True
                    await sync_to_async(notification.save)()
                    return Response(AnalysisNotificationSerializer(notification).data)
                else:
                    # 标记所有通知为已读
                    await sync_to_async(AnalysisNotification.objects.filter)(
                        user=request.user,
                        is_read=False
                    ).update(is_read=True)
                    return Response({"status": "success"})
            else:
                return Response({"error": "不支持的操作"}, status=status.HTTP_400_BAD_REQUEST)
        except NotificationSubscription.DoesNotExist:
            return Response({"error": "订阅不存在"}, status=status.HTTP_404_NOT_FOUND)
        except AnalysisNotification.DoesNotExist:
            return Response({"error": "通知不存在"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"通知管理失败: {str(e)}")
            return Response({"error": f"系统错误: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    async def perform_create(self, serializer):
        """创建时添加创建者"""
        try:
            user = self.request.user
            if user.is_anonymous:
                raise ValueError("用户未认证")
            instance = await sync_to_async(serializer.save)(created_by=user)
        except Exception as e:
            logger.error(f"创建分析规则失败: {str(e)}")
            raise

class AnalysisRuleViewSet(AsyncViewSet):
    """分析规则视图集"""
    
    queryset = AnalysisRule.objects.all()
    serializer_class = AnalysisRuleSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']
    format_kwarg = None  # 添加format_kwarg属性
    
    async def get_queryset(self):
        return await sync_to_async(list)(AnalysisRule.objects.filter(created_by=self.request.user))
    
    async def perform_create(self, serializer):
        """创建分析规则"""
        try:
            user = await sync_to_async(lambda: self.request.user)()
            instance = await sync_to_async(serializer.save)(created_by=user)
        except Exception as e:
            logger.error(f"创建分析规则失败: {str(e)}")
            raise
            
    async def perform_update(self, serializer):
        """更新分析规则"""
        try:
            instance = await sync_to_async(serializer.save)()
            instance.updated_at = timezone.now()
            await sync_to_async(instance.save)()
        except Exception as e:
            logger.error(f"更新分析规则失败: {str(e)}")
            raise

    async def list(self, request):
        """获取规则列表"""
        rules = await self.get_queryset()
        serializer = self.serializer_class(rules, many=True)
        return Response(serializer.data)

    async def create(self, request, *args, **kwargs):
        """创建分析规则"""
        try:
            # 验证用户认证
            if request.user.is_anonymous:
                return Response({"error": "用户未认证"}, status=status.HTTP_401_UNAUTHORIZED)
                
            # 创建规则
            serializer = self.get_serializer(data=request.data)
            if await sync_to_async(serializer.is_valid)():
                # 直接在创建时设置created_by字段
                instance = await sync_to_async(serializer.save)()
                instance.created_by = request.user
                await sync_to_async(instance.save)()
                return Response(self.get_serializer(instance).data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"创建分析规则失败: {str(e)}")
            return Response({"error": f"系统错误: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    async def update(self, request, pk=None):
        """更新规则"""
        try:
            rule = await sync_to_async(self.queryset.get)(id=pk)
            serializer = self.serializer_class(rule, data=request.data, partial=False)
            if await sync_to_async(serializer.is_valid)():
                await self.perform_update(serializer)
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except AnalysisRule.DoesNotExist:
            return Response({"error": "规则不存在"}, status=status.HTTP_404_NOT_FOUND)

    async def partial_update(self, request, pk=None):
        """部分更新规则"""
        try:
            rule = await sync_to_async(self.queryset.get)(id=pk)
            serializer = self.serializer_class(rule, data=request.data, partial=True)
            if await sync_to_async(serializer.is_valid)():
                await self.perform_update(serializer)
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except AnalysisRule.DoesNotExist:
            return Response({"error": "规则不存在"}, status=status.HTTP_404_NOT_FOUND)

    async def destroy(self, request, pk=None):
        """删除规则"""
        try:
            rule = await sync_to_async(self.queryset.get)(id=pk)
            await sync_to_async(rule.delete)()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except AnalysisRule.DoesNotExist:
            return Response({"error": "规则不存在"}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    async def toggle_active(self, request, pk=None):
        """切换规则的启用状态"""
        try:
            rule = await sync_to_async(self.queryset.get)(id=pk)
            rule.is_active = not rule.is_active
            await sync_to_async(rule.save)()
            
            return Response({
                'message': f"规则已{'启用' if rule.is_active else '禁用'}",
                'is_active': rule.is_active
            })
        except AnalysisRule.DoesNotExist:
            return Response({"error": "规则不存在"}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    async def test_rule(self, request, pk=None):
        """测试分析规则"""
        try:
            rule = await sync_to_async(self.queryset.get)(id=pk)
            news_id = request.data.get('news_id')
            
            if not news_id:
                return Response({
                    'message': '请提供要测试的新闻ID'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                news_article = await sync_to_async(NewsArticle.objects.get)(id=news_id)
            except NewsArticle.DoesNotExist:
                return Response({
                    'message': '未找到指定的新闻'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # 使用 AI 服务进行测试
            ai_service = AIService()
            result = await ai_service.analyze_with_rule(news_article, rule)
            
            return Response({
                'message': '测试成功',
                'result': result
            })
        except AnalysisRule.DoesNotExist:
            return Response({"error": "规则不存在"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"测试失败: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class BatchAnalysisTaskViewSet(AsyncViewSet):
    """批量分析任务视图集"""
    
    permission_classes = [IsAuthenticated]
    serializer_class = BatchAnalysisTaskSerializer
    queryset = BatchAnalysisTask.objects.all()

    async def list(self, request):
        """获取任务列表"""
        tasks = await sync_to_async(list)(self.queryset.filter(created_by=request.user))
        serializer = self.serializer_class(tasks, many=True)
        return Response(serializer.data)

    async def retrieve(self, request, pk=None):
        """获取单个任务"""
        try:
            task = await sync_to_async(self.queryset.get)(id=pk, created_by=request.user)
            serializer = self.serializer_class(task)
            return Response(serializer.data)
        except BatchAnalysisTask.DoesNotExist:
            return Response({"error": "任务不存在"}, status=status.HTTP_404_NOT_FOUND)
    
    async def create(self, request):
        """创建任务"""
        data = request.data.copy()
        data['created_by'] = request.user.id
        serializer = self.serializer_class(data=data)
        if await sync_to_async(serializer.is_valid)():
            task = await sync_to_async(serializer.save)()
            # 启动异步任务
            process_batch_analysis.delay(task.id)
            return Response(self.serializer_class(task).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    async def update(self, request, pk=None):
        """更新任务"""
        try:
            task = await sync_to_async(self.queryset.get)(id=pk, created_by=request.user)
            data = request.data
            
            # 只允许更新某些字段
            allowed_fields = ["name", "description"]
            for field in allowed_fields:
                if field in data:
                    setattr(task, field, data[field])
            
            await sync_to_async(task.save)()
            
            serializer = self.serializer_class(task)
            return Response(serializer.data)
        except BatchAnalysisTask.DoesNotExist:
            return Response({"error": "任务不存在"}, status=status.HTTP_404_NOT_FOUND)
    
    async def destroy(self, request, pk=None):
        """删除任务"""
        try:
            task = await sync_to_async(self.queryset.get)(id=pk, created_by=request.user)
            await sync_to_async(task.delete)()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except BatchAnalysisTask.DoesNotExist:
            return Response({"error": "任务不存在"}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=["post"])
    async def control(self, request, pk=None):
        """控制任务"""
        try:
            task = await sync_to_async(self.queryset.get)(id=pk)
            action = request.data.get("action")
            
            if action == "cancel":
                task.status = "cancelled"
                await sync_to_async(task.save)()
            elif action == "retry":
                task.status = "pending"
                await sync_to_async(task.save)()
                # 重新启动任务
                process_batch_analysis.delay(task.id)
            else:
                return Response({"error": "不支持的操作"}, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(self.serializer_class(task).data)
        except BatchAnalysisTask.DoesNotExist:
            return Response({"error": "任务不存在"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"系统错误: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AnalysisScheduleViewSet(AsyncViewSet):
    """分析计划视图集"""
    
    permission_classes = [IsAuthenticated]
    serializer_class = AnalysisScheduleSerializer
    queryset = AnalysisSchedule.objects.all()

    async def list(self, request):
        """获取计划列表"""
        schedules = await sync_to_async(list)(self.queryset.filter(created_by=request.user))
        serializer = self.serializer_class(schedules, many=True)
        return Response(serializer.data)
    
    async def retrieve(self, request, pk=None):
        """获取单个计划"""
        try:
            schedule = await sync_to_async(self.queryset.get)(id=pk, created_by=request.user)
            serializer = self.serializer_class(schedule)
            return Response(serializer.data)
        except AnalysisSchedule.DoesNotExist:
            return Response({"error": "计划不存在"}, status=status.HTTP_404_NOT_FOUND)
    
    async def create(self, request):
        """创建计划"""
        data = request.data.copy()
        data['created_by'] = request.user.id
        serializer = self.serializer_class(data=data)
        if await sync_to_async(serializer.is_valid)():
            schedule = await sync_to_async(serializer.save)()
            return Response(self.serializer_class(schedule).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    async def update(self, request, pk=None):
        """更新计划"""
        try:
            schedule = await sync_to_async(self.queryset.get)(id=pk, created_by=request.user)
            data = request.data
            
            # 更新计划
            for field in ["name", "description", "cron_expression", "analysis_types", 
                         "rule_id", "filter_criteria", "is_active"]:
                if field in data:
                    setattr(schedule, field, data[field])
            
            await sync_to_async(schedule.save)()
            
            serializer = self.serializer_class(schedule)
            return Response(serializer.data)
        except AnalysisSchedule.DoesNotExist:
            return Response({"error": "计划不存在"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"系统错误: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    async def destroy(self, request, pk=None):
        """删除计划"""
        try:
            schedule = await sync_to_async(self.queryset.get)(id=pk, created_by=request.user)
            await sync_to_async(schedule.delete)()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except AnalysisSchedule.DoesNotExist:
            return Response({"error": "计划不存在"}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=["post"])
    async def control(self, request, pk=None):
        """控制计划"""
        try:
            schedule = await sync_to_async(self.queryset.get)(id=pk, created_by=request.user)
            action = request.data.get("action")
            
            if action == "enable":
                schedule.is_active = True
            elif action == "disable":
                schedule.is_active = False
            else:
                return Response({"error": "不支持的操作"}, status=status.HTTP_400_BAD_REQUEST)
            
            await sync_to_async(schedule.save)()
            
            serializer = self.serializer_class(schedule)
            return Response(serializer.data)
        except AnalysisSchedule.DoesNotExist:
            return Response({"error": "计划不存在"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"系统错误: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=["get"])
    async def executions(self, request, pk=None):
        """获取计划执行历史"""
        try:
            schedule = await sync_to_async(self.queryset.get)(id=pk, created_by=request.user)
            executions = await sync_to_async(list)(ScheduleExecution.objects.filter(schedule=schedule))
            serializer = ScheduleExecutionSerializer(executions, many=True)
            return Response(serializer.data)
        except AnalysisSchedule.DoesNotExist:
            return Response({"error": "计划不存在"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"系统错误: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ScheduleExecutionViewSet(AsyncViewSet):
    """计划执行视图集"""
    
    permission_classes = [IsAuthenticated]
    
    async def list(self, request):
        """获取执行记录列表"""
        executions = await sync_to_async(list)(ScheduleExecution.objects.filter(schedule__created_by=request.user))
        serializer = ScheduleExecutionSerializer(executions, many=True)
        return Response(serializer.data)
    
    async def retrieve(self, request, pk=None):
        """获取单个执行记录"""
        try:
            execution = await sync_to_async(ScheduleExecution.objects.get)(id=pk, schedule__created_by=request.user)
            serializer = ScheduleExecutionSerializer(execution)
            return Response(serializer.data)
        except ScheduleExecution.DoesNotExist:
            return Response({"error": "执行记录不存在"}, status=status.HTTP_404_NOT_FOUND)
    
    async def create(self, request):
        """创建执行记录"""
        try:
            data = request.data
            if not data.get("schedule_id"):
                return Response({"error": "计划ID不能为空"}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                schedule = await sync_to_async(AnalysisSchedule.objects.get)(
                    id=data["schedule_id"],
                    created_by=request.user
                )
            except AnalysisSchedule.DoesNotExist:
                return Response({"error": "计划不存在"}, status=status.HTTP_404_NOT_FOUND)
            
            # 创建执行记录
            execution = await sync_to_async(ScheduleExecution.objects.create)(
                schedule=schedule,
                status='pending',
                total_count=0,
                processed=0,
                success=0,
                failed=0,
                config=data.get("config", {})
            )
            
            # 启动异步任务
            process_schedule_execution.delay(execution.id)
            
            serializer = ScheduleExecutionSerializer(execution)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": f"系统错误: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    async def update(self, request, pk=None):
        """更新执行记录"""
        try:
            execution = await sync_to_async(ScheduleExecution.objects.get)(id=pk, schedule__created_by=request.user)
            data = request.data
            
            # 只允许更新某些字段
            allowed_fields = ["status", "error_message"]
            for field in allowed_fields:
                if field in data:
                    setattr(execution, field, data[field])
            
            await sync_to_async(execution.save)()
            
            serializer = ScheduleExecutionSerializer(execution)
            return Response(serializer.data)
        except ScheduleExecution.DoesNotExist:
            return Response({"error": "执行记录不存在"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"系统错误: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    async def destroy(self, request, pk=None):
        """删除执行记录"""
        try:
            execution = await sync_to_async(ScheduleExecution.objects.get)(id=pk, schedule__created_by=request.user)
            await sync_to_async(execution.delete)()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ScheduleExecution.DoesNotExist:
            return Response({"error": "执行记录不存在"}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=["post"])
    async def control(self, request, pk=None):
        """控制执行记录"""
        try:
            execution = await sync_to_async(ScheduleExecution.objects.get)(id=pk, schedule__created_by=request.user)
            action = request.data.get("action")
            
            if action == "cancel":
                execution.status = "cancelled"
                await sync_to_async(execution.save)()
            elif action == "retry":
                execution.status = "pending"
                await sync_to_async(execution.save)()
                # 重新启动任务
                process_schedule_execution.delay(execution.id)
            else:
                return Response({"error": "不支持的操作"}, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(ScheduleExecutionSerializer(execution).data)
        except ScheduleExecution.DoesNotExist:
            return Response({"error": "执行记录不存在"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"系统错误: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class NotificationViewSet(AsyncViewSet):
    """通知视图集"""
    
    permission_classes = [IsAuthenticated]
    
    async def list(self, request):
        """获取通知列表"""
        notifications = await sync_to_async(list)(AnalysisNotification.objects.filter(user=request.user))
        serializer = AnalysisNotificationSerializer(notifications, many=True)
        return Response(serializer.data)
    
    async def retrieve(self, request, pk=None):
        """获取单个通知"""
        try:
            notification = await sync_to_async(AnalysisNotification.objects.get)(id=pk, user=request.user)
            serializer = AnalysisNotificationSerializer(notification)
            return Response(serializer.data)
        except AnalysisNotification.DoesNotExist:
            return Response({"error": "通知不存在"}, status=status.HTTP_404_NOT_FOUND)
    
    async def update(self, request, pk=None):
        """更新通知"""
        try:
            notification = await sync_to_async(AnalysisNotification.objects.get)(id=pk, user=request.user)
            data = request.data
            
            # 只允许更新某些字段
            allowed_fields = ["is_read"]
            for field in allowed_fields:
                if field in data:
                    setattr(notification, field, data[field])
            
            await sync_to_async(notification.save)()
            
            serializer = AnalysisNotificationSerializer(notification)
            return Response(serializer.data)
        except AnalysisNotification.DoesNotExist:
            return Response({"error": "通知不存在"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"系统错误: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    async def destroy(self, request, pk=None):
        """删除通知"""
        try:
            notification = await sync_to_async(AnalysisNotification.objects.get)(id=pk, user=request.user)
            await sync_to_async(notification.delete)()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except AnalysisNotification.DoesNotExist:
            return Response({"error": "通知不存在"}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=["post"])
    async def mark_all_read(self, request):
        """标记所有通知为已读"""
        try:
            await sync_to_async(AnalysisNotification.objects.filter)(
                user=request.user,
                is_read=False
            ).update(is_read=True)
            return Response({"status": "success"})
        except Exception as e:
            return Response({"error": f"系统错误: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=["post"])
    async def clear_all(self, request):
        """清空所有通知"""
        try:
            await sync_to_async(AnalysisNotification.objects.filter)(
                user=request.user
            ).delete()
            return Response({"status": "success"})
        except Exception as e:
            return Response({"error": f"系统错误: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class NotificationSubscriptionViewSet(AsyncViewSet):
    """通知订阅视图集"""
    
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSubscriptionSerializer
    queryset = NotificationSubscription.objects.all()

    async def list(self, request):
        """获取订阅列表"""
        subscriptions = await sync_to_async(list)(self.queryset.filter(user=request.user))
        serializer = self.serializer_class(subscriptions, many=True)
        return Response(serializer.data)
    
    async def retrieve(self, request, pk=None):
        """获取单个订阅"""
        try:
            subscription = await sync_to_async(self.queryset.get)(id=pk, user=request.user)
            serializer = self.serializer_class(subscription)
            return Response(serializer.data)
        except NotificationSubscription.DoesNotExist:
            return Response({"error": "订阅不存在"}, status=status.HTTP_404_NOT_FOUND)
    
    async def create(self, request):
        """创建订阅"""
        data = request.data.copy()
        data['user'] = request.user.id
        serializer = self.serializer_class(data=data)
        if await sync_to_async(serializer.is_valid)():
            subscription = await sync_to_async(serializer.save)()
            return Response(self.serializer_class(subscription).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    async def update(self, request, pk=None):
        """更新订阅"""
        try:
            subscription = await sync_to_async(self.queryset.get)(id=pk, user=request.user)
            data = request.data
            
            # 更新订阅
            for field in ["notification_type", "config"]:
                if field in data:
                    setattr(subscription, field, data[field])
            
            await sync_to_async(subscription.save)()
            
            serializer = self.serializer_class(subscription)
            return Response(serializer.data)
        except NotificationSubscription.DoesNotExist:
            return Response({"error": "订阅不存在"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"系统错误: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    async def destroy(self, request, *args, **kwargs):
        instance = await sync_to_async(self.get_object)()
        await sync_to_async(instance.delete)()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=["get"])
    async def notifications(self, request):
        """获取通知列表"""
        try:
            notifications = await sync_to_async(list)(AnalysisNotification.objects.filter(user=request.user))
            serializer = AnalysisNotificationSerializer(notifications, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": f"系统错误: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=["post"])
    async def mark_read(self, request):
        """标记通知为已读"""
        try:
            notification_id = request.data.get("notification_id")
            if notification_id:
                # 标记单个通知为已读
                notification = await sync_to_async(AnalysisNotification.objects.get)(
                    id=notification_id,
                    user=request.user
                )
                notification.is_read = True
                await sync_to_async(notification.save)()
                serializer = AnalysisNotificationSerializer(notification)
                return Response(serializer.data)
            else:
                # 标记所有通知为已读
                await sync_to_async(AnalysisNotification.objects.filter)(
                    user=request.user,
                    is_read=False
                ).update(is_read=True)
                return Response({"status": "success"})
        except AnalysisNotification.DoesNotExist:
            return Response({"error": "通知不存在"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"系统错误: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AnalysisVisualizationViewSet(AsyncViewSet):
    """分析可视化视图集"""
    
    permission_classes = [IsAuthenticated]
    
    async def list(self, request):
        """获取可视化列表"""
        visualizations = await sync_to_async(list)(AnalysisVisualization.objects.filter(created_by=request.user))
        serializer = AnalysisVisualizationSerializer(visualizations, many=True)
        return Response(serializer.data)
    
    async def retrieve(self, request, pk=None):
        """获取单个可视化"""
        try:
            visualization = await sync_to_async(AnalysisVisualization.objects.get)(id=pk, created_by=request.user)
            serializer = AnalysisVisualizationSerializer(visualization)
            return Response(serializer.data)
        except AnalysisVisualization.DoesNotExist:
            return Response({"error": "可视化不存在"}, status=status.HTTP_404_NOT_FOUND)
    
    async def create(self, request):
        """创建可视化"""
        try:
            data = request.data
            if not data.get("name") or not data.get("visualization_type"):
                return Response({"error": "可视化名称和类型不能为空"}, status=status.HTTP_400_BAD_REQUEST)
            
            # 创建可视化
            visualization = await sync_to_async(AnalysisVisualization.objects.create)(
                name=data["name"],
                description=data.get("description", ""),
                visualization_type=data["visualization_type"],
                config=data.get("config", {}),
                data_source=data.get("data_source", {}),
                created_by=request.user
            )
            
            # 生成可视化
            visualization_service = VisualizationService()
            result = await visualization_service.generate_visualization(
                visualization_type=data["visualization_type"],
                data=data.get("data", {}),
                config=data.get("config", {})
            )
            
            # 更新可视化结果
            visualization.result = result
            await sync_to_async(visualization.save)()
            
            serializer = AnalysisVisualizationSerializer(visualization)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": f"系统错误: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    async def update(self, request, pk=None):
        """更新可视化"""
        try:
            visualization = await sync_to_async(AnalysisVisualization.objects.get)(id=pk, created_by=request.user)
            data = request.data
            
            # 更新可视化
            for field in ["name", "description", "visualization_type", "config", "data_source"]:
                if field in data:
                    setattr(visualization, field, data[field])
            
            # 如果提供了新数据，重新生成可视化
            if "data" in data:
                visualization_service = VisualizationService()
                result = await visualization_service.generate_visualization(
                    visualization_type=visualization.visualization_type,
                    data=data["data"],
                    config=visualization.config
                )
                visualization.result = result
            
            await sync_to_async(visualization.save)()
            
            serializer = AnalysisVisualizationSerializer(visualization)
            return Response(serializer.data)
        except AnalysisVisualization.DoesNotExist:
            return Response({"error": "可视化不存在"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"系统错误: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    async def destroy(self, request, pk=None):
        """删除可视化"""
        try:
            visualization = await sync_to_async(AnalysisVisualization.objects.get)(id=pk, created_by=request.user)
            await sync_to_async(visualization.delete)()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except AnalysisVisualization.DoesNotExist:
            return Response({"error": "可视化不存在"}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=["post"])
    async def regenerate(self, request, pk=None):
        """重新生成可视化"""
        try:
            visualization = await sync_to_async(AnalysisVisualization.objects.get)(id=pk, created_by=request.user)
            data = request.data.get("data")
            
            if not data:
                return Response({"error": "需要提供数据"}, status=status.HTTP_400_BAD_REQUEST)
            
            # 重新生成可视化
            visualization_service = VisualizationService()
            result = await visualization_service.generate_visualization(
                visualization_type=visualization.visualization_type,
                data=data,
                config=visualization.config
            )
            
            # 更新结果
            visualization.result = result
            await sync_to_async(visualization.save)()
            
            serializer = AnalysisVisualizationSerializer(visualization)
            return Response(serializer.data)
        except AnalysisVisualization.DoesNotExist:
            return Response({"error": "可视化不存在"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"系统错误: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
