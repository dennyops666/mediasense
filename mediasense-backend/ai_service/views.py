import logging
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
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
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
    Notification,
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
    NotificationSerializer,
)
from .services import AIService, RateLimitExceeded, VisualizationService
from .tasks import process_batch_analysis, process_schedule_execution

logger = logging.getLogger(__name__)

class AsyncViewSet(viewsets.GenericViewSet):
    renderer_classes = [JSONRenderer]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    logger = logger

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
            self.logger.error(f"系统错误: {str(exc)}")
            return Response(
                {'error': 'internal_error', 'detail': str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AIServiceViewSet(AsyncViewSet):
    """AI服务视图集"""
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    async def analyze_article(self, request, pk=None):
        """分析文章"""
        try:
            article = await sync_to_async(get_object_or_404)(NewsArticle, pk=pk)
            analysis_types = request.data.get('analysis_types', ['sentiment'])
            
            service = AIService()
            results = await service.analyze_text(article.content, analysis_types)
            
            # 保存分析结果
            result_ids = []
            for analysis_type, result in results.items():
                analysis_result = await sync_to_async(AnalysisResult.objects.create)(
                    news=article,
                    analysis_type=analysis_type,
                    result=result,
                    created_by=request.user
                )
                result_ids.append(analysis_result.id)
            
            return Response({
                'message': '分析完成',
                'data': results,
                'result_ids': result_ids
            })
            
        except RateLimitExceeded as e:
            return Response({
                'error': 'rate_limit_exceeded',
                'detail': str(e)
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except Exception as e:
            logger.error(f"分析文章时出错: {str(e)}", exc_info=True)
            return Response({
                'error': 'analysis_failed',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    async def analyze_with_rules(self, request, pk=None):
        """使用规则分析文章"""
        try:
            article = await sync_to_async(get_object_or_404)(NewsArticle, pk=pk)
            rule_id = request.data.get('rule_id')
            rule_ids = request.data.get('rule_ids', [])
            
            if rule_id:
                rule_ids = [rule_id]
        
        if not rule_ids:
            return Response({
                    'error': 'invalid_request',
                    'detail': '未指定分析规则'
            }, status=status.HTTP_400_BAD_REQUEST)
        
            # 获取规则
            rules = await sync_to_async(list)(AnalysisRule.objects.filter(id__in=rule_ids, is_active=True))
            if not rules:
                return Response({
                    'error': 'rules_not_found',
                    'detail': '未找到有效的分析规则'
                }, status=status.HTTP_404_NOT_FOUND)
            
            service = AIService()
            results = await service.analyze_with_rules(article.content, rules)
            
            # 保存分析结果
            result_id = None
            for rule_id, result in results.items():
                analysis_result = await sync_to_async(AnalysisResult.objects.create)(
                    news=article,
                    analysis_type=f'rule_{rule_id}',
                    result=result,
                    created_by=request.user
                )
                if result_id is None:  # 只保存第一个结果的ID
                    result_id = analysis_result.id
            
            return Response({
                'message': '规则分析完成',
                'data': results,
                'result_id': result_id
            })
            
        except RateLimitExceeded as e:
            return Response({
                'error': 'rate_limit_exceeded',
                'detail': str(e)
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except Exception as e:
            logger.error(f"使用规则分析文章时出错: {str(e)}", exc_info=True)
            return Response({
                'error': 'analysis_failed',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AnalysisRuleViewSet(viewsets.ModelViewSet):
    """分析规则视图集"""
    queryset = AnalysisRule.objects.all()
    serializer_class = AnalysisRuleSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """创建时设置创建者"""
        serializer.save(created_by=self.request.user)

    def get_queryset(self):
        """获取查询集"""
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(created_by=self.request.user)
        return queryset
    
    @action(detail=True, methods=['post'])
    async def test_rule(self, request, pk=None):
        """测试规则"""
        try:
            rule = await sync_to_async(get_object_or_404)(AnalysisRule, pk=pk)
            content = request.data.get('content')
            
            if not content:
            return Response({
                    'error': 'invalid_request',
                    'detail': '未提供测试内容'
                }, status=status.HTTP_400_BAD_REQUEST)
        
            service = AIService()
            result = await service.analyze_with_rule(content, rule)
            
            return Response({
                'message': '规则测试完成',
                'data': result
            })
            
        except RateLimitExceeded as e:
            return Response({
                'error': 'rate_limit_exceeded',
                'detail': str(e)
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except Exception as e:
            logger.error(f"测试规则时出错: {str(e)}", exc_info=True)
            return Response({
                'error': 'test_failed',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
class AnalysisScheduleViewSet(AsyncViewSet):
    """
    用于管理分析调度的视图集
    """
    queryset = AnalysisSchedule.objects.all()
    serializer_class = AnalysisScheduleSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def get_queryset(self):
        if self.request.user.is_staff:
            return self.queryset
        return self.queryset.filter(creator=self.request.user)

    async def test_schedule(self, request, pk=None):
        """
        测试分析调度
        """
        try:
            schedule = await sync_to_async(self.get_object)()
            result = await schedule.execute_test()
            return Response({"status": "success", "result": result})
        except RateLimitExceeded as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        except Exception as e:
            logger.error(f"测试调度失败: {str(e)}")
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class AnalysisVisualizationViewSet(AsyncViewSet):
    """
    用于管理分析可视化的视图集
    """
    queryset = AnalysisVisualization.objects.all()
    serializer_class = AnalysisVisualizationSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def get_queryset(self):
        if self.request.user.is_staff:
            return self.queryset
        return self.queryset.filter(creator=self.request.user)

    async def generate_visualization(self, request, pk=None):
        """
        生成分析可视化
        """
        try:
            visualization = await sync_to_async(self.get_object)()
            result = await visualization.generate()
            return Response({"status": "success", "result": result})
        except RateLimitExceeded as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        except Exception as e:
            logger.error(f"生成可视化失败: {str(e)}")
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class BatchAnalysisTaskViewSet(AsyncViewSet):
    """
    用于管理批量分析任务的视图集
    """
    queryset = BatchAnalysisTask.objects.all()
    serializer_class = BatchAnalysisTaskSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def get_queryset(self):
        if self.request.user.is_staff:
            return self.queryset
        return self.queryset.filter(creator=self.request.user)

    async def start_task(self, request, pk=None):
        """
        启动批量分析任务
        """
        try:
            task = await sync_to_async(self.get_object)()
            result = await task.start()
            return Response({"status": "success", "result": result})
        except RateLimitExceeded as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        except Exception as e:
            logger.error(f"启动批量分析任务失败: {str(e)}")
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    async def cancel_task(self, request, pk=None):
        """
        取消批量分析任务
        """
        try:
            task = await sync_to_async(self.get_object)()
            result = await task.cancel()
            return Response({"status": "success", "result": result})
        except Exception as e:
            logger.error(f"取消批量分析任务失败: {str(e)}")
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class NotificationSubscriptionViewSet(AsyncViewSet):
    """
    用于管理通知订阅的视图集
    """
    queryset = NotificationSubscription.objects.all()
    serializer_class = NotificationSubscriptionSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        if self.request.user.is_staff:
            return self.queryset
        return self.queryset.filter(user=self.request.user)

    async def toggle_subscription(self, request, pk=None):
        """
        切换通知订阅状态
        """
        try:
            subscription = await sync_to_async(self.get_object)()
            subscription.is_active = not subscription.is_active
            await sync_to_async(subscription.save)()
            return Response({
                "status": "success",
                "is_active": subscription.is_active
            })
        except Exception as e:
            logger.error(f"切换通知订阅状态失败: {str(e)}")
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class NotificationViewSet(AsyncViewSet):
    """
    用于管理通知的视图集
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return self.queryset
        return self.queryset.filter(user=self.request.user)

    async def mark_as_read(self, request, pk=None):
        """
        将通知标记为已读
        """
        try:
            notification = await sync_to_async(self.get_object)()
            notification.is_read = True
            await sync_to_async(notification.save)()
            return Response({"status": "success"})
        except Exception as e:
            logger.error(f"标记通知为已读失败: {str(e)}")
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    async def mark_all_as_read(self, request):
        """
        将所有通知标记为已读
        """
        try:
            queryset = self.get_queryset()
            await sync_to_async(queryset.update)(is_read=True)
            return Response({"status": "success"})
        except Exception as e:
            logger.error(f"标记所有通知为已读失败: {str(e)}")
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class ScheduleExecutionViewSet(AsyncViewSet):
    """
    用于管理调度执行记录的视图集
    """
    queryset = ScheduleExecution.objects.all()
    serializer_class = ScheduleExecutionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return self.queryset
        return self.queryset.filter(schedule__creator=self.request.user)

    async def retry_execution(self, request, pk=None):
        """
        重试执行调度
        """
        try:
            execution = await sync_to_async(self.get_object)()
            result = await execution.retry()
            return Response({"status": "success", "result": result})
        except RateLimitExceeded as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        except Exception as e:
            logger.error(f"重试执行调度失败: {str(e)}")
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )