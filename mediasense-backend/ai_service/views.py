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

class AsyncViewSet(viewsets.ViewSet):
    """异步视图集基类"""
    renderer_classes = [JSONRenderer]

    def get_handler(self, request):
        """获取处理器"""
        handler = getattr(self, request.method.lower(), None)
        if handler is None:
            return None

        # 如果是action方法，需要获取action的处理器
        if hasattr(handler, 'action'):
            action = handler.action
            handler = getattr(self, action, None)

        return handler

    async def dispatch(self, request, *args, **kwargs):
        """处理请求"""
        try:
            handler = self.get_handler(request)
            if handler is None:
                return JsonResponse(
                    {'error': 'method_not_allowed', 'detail': f'方法 {request.method} 不允许'},
                    status=status.HTTP_405_METHOD_NOT_ALLOWED
                )

            response = await handler(request, *args, **kwargs)
            
            # 如果响应为空,返回204
            if response is None:
                return JsonResponse({}, status=status.HTTP_204_NO_CONTENT)
            
            # 如果是Response对象,转换为JsonResponse
            if isinstance(response, Response):
                return JsonResponse(response.data, status=response.status_code)
            
            # 如果是JsonResponse对象,直接返回
            if isinstance(response, JsonResponse):
                return response
            
            # 如果是字典,直接返回JsonResponse
            if isinstance(response, dict):
                return JsonResponse(response)
            
            # 其他情况,转换为字典后返回
            return JsonResponse({'data': response})

        except NewsArticle.DoesNotExist:
            return JsonResponse(
                {'error': 'not_found', 'detail': '新闻不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
        except RateLimitExceeded as e:
            return JsonResponse(
                {'error': 'rate_limit_exceeded', 'detail': str(e)},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        except openai.RateLimitError:
            return JsonResponse(
                {'error': 'rate_limit_exceeded', 'detail': 'API调用次数超限'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        except openai.APIStatusError as e:
            if e.response.status == 429:
                return JsonResponse(
                    {'error': 'rate_limit_exceeded', 'detail': str(e)},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            return JsonResponse(
                {'error': 'openai_error', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except ValueError as e:
            return JsonResponse(
                {'error': 'invalid_input', 'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return JsonResponse(
                {'error': 'internal_error', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@method_decorator(csrf_exempt, name='dispatch')
class AIServiceViewSet(AsyncViewSet):
    """AI服务视图集"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ai_service = AIService()
    
    @action(detail=True, methods=["post"])
    async def analyze_sentiment(self, request, pk=None):
        """分析新闻情感"""
        try:
            news = await sync_to_async(NewsArticle.objects.get)(id=pk)
            if not news.content:
                return JsonResponse({"error": "新闻内容为空"}, status=400)
            
            # 先检查缓存
            cached_result = await self.ai_service._get_cached_result(pk, "sentiment")
            if cached_result:
                return JsonResponse(json.loads(cached_result))
            
            # 调用分析服务
            result = await self.ai_service.analyze_sentiment(news.content)
            
            # 缓存结果
            await self.ai_service._cache_result(pk, "sentiment", json.dumps(result))
            
            # 保存分析结果
            await sync_to_async(AnalysisResult.objects.create)(
                news=news,
                analysis_type='sentiment',
                result=json.dumps(result)
            )
            
            return JsonResponse(result)
        except NewsArticle.DoesNotExist:
            return JsonResponse({"error": "新闻不存在"}, status=404)
        except RateLimitExceeded as e:
            return JsonResponse({"error": str(e)}, status=429)
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"系统错误: {str(e)}"}, status=500)
    
    @action(detail=True, methods=["post"])
    async def extract_keywords(self, request, pk=None):
        """提取新闻关键词"""
        news = await sync_to_async(NewsArticle.objects.get)(id=pk)
        if not news.content:
            raise ValueError("新闻内容不能为空")
        
        # 先检查缓存
        cached_result = await self.ai_service._get_cached_result(pk, "keywords")
        if cached_result:
            result = json.loads(cached_result)
            return JsonResponse(result.get("keywords", []))
        
        # 调用分析服务
        result = await self.ai_service.extract_keywords(news.content)
        
        # 缓存结果
        await self.ai_service._cache_result(pk, "keywords", json.dumps(result))
        
        return JsonResponse(result.get("keywords", []), safe=False)
    
    @action(detail=True, methods=["post"])
    async def generate_summary(self, request, pk=None):
        """生成新闻摘要"""
        news = await sync_to_async(NewsArticle.objects.get)(id=pk)
        if not news.content:
            raise ValueError("新闻内容不能为空")
        
        # 先检查缓存
        cached_result = await self.ai_service._get_cached_result(pk, "summary")
        if cached_result:
            return JsonResponse(json.loads(cached_result))
        
        # 调用分析服务
        result = await self.ai_service.generate_summary(news.content)
        
        # 缓存结果
        await self.ai_service._cache_result(pk, "summary", json.dumps(result))
        
        return JsonResponse(result)
    
    @action(detail=False, methods=["post"])
    async def batch_analyze(self, request):
        """批量分析新闻"""
        news_ids = request.data.get("news_ids", [])
        analysis_types = request.data.get("analysis_types", [])
        
        if not news_ids:
            raise ValueError("新闻ID列表不能为空")
        if not analysis_types:
            raise ValueError("分析类型列表不能为空")
        
        # 创建批量分析任务
        task = await sync_to_async(BatchAnalysisTask.objects.create)(
            status='pending',
            total_count=len(news_ids),
            processed=0,
            success=0,
            failed=0
        )
        
        # 异步处理每篇新闻
        for news_id in news_ids:
            try:
                news = await sync_to_async(NewsArticle.objects.get)(id=news_id)
                if not news.content:
                    continue
                
                for analysis_type in analysis_types:
                    try:
                        # 先检查缓存
                        cached_result = await self.ai_service._get_cached_result(news_id, analysis_type)
                        if cached_result:
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
                        await self.ai_service._cache_result(news_id, analysis_type, json.dumps(result))
                        
                        # 更新任务状态
                        task.success += 1
                    except Exception as e:
                        task.failed += 1
                
                task.processed += 1
                await sync_to_async(task.save)()
            except NewsArticle.DoesNotExist:
                task.failed += 1
                task.processed += 1
                await sync_to_async(task.save)()
                continue
            except Exception as e:
                task.failed += 1
                task.processed += 1
                await sync_to_async(task.save)()
                continue
        
        # 更新任务状态
        task.status = 'completed'
        await sync_to_async(task.save)()
        
        return JsonResponse({"task_id": task.id}, status=status.HTTP_202_ACCEPTED)
    
    @action(detail=True, methods=["get"])
    async def analysis_result(self, request, pk=None):
        """获取分析结果"""
        try:
            news = await sync_to_async(NewsArticle.objects.get)(id=pk)
            
            # 先获取所有结果
            results = await sync_to_async(list)(AnalysisResult.objects.filter(news_id=pk))
            if not results:
                return JsonResponse({"error": "分析结果不存在"}, status=404)
            
            result = results[0]  # 获取第一个结果
            
            return JsonResponse({
                "sentiment": json.loads(result.result).get("sentiment"),
                "confidence": json.loads(result.result).get("confidence"),
                "keywords": json.loads(result.result).get("keywords", []),
                "summary": json.loads(result.result).get("summary"),
                "created_at": result.created_at.isoformat()
            })
        except NewsArticle.DoesNotExist:
            return JsonResponse({"error": "新闻不存在"}, status=404)
        except Exception as e:
            return JsonResponse({"error": f"系统错误: {str(e)}"}, status=500)
    
    @action(detail=True, methods=["post"])
    async def invalidate_cache(self, request, pk=None):
        """清除缓存"""
        news = await sync_to_async(NewsArticle.objects.get)(id=pk)
        await self.ai_service.invalidate_cache(news.id)
        return JsonResponse({"message": "缓存已清除"})
    
    @action(detail=False, methods=["post"])
    async def clean_cache(self, request):
        """清理过期缓存"""
        await self.ai_service.clean_expired_cache()
        return JsonResponse({"message": "过期缓存已清理"})
    
    @action(detail=False, methods=['post'])
    async def analyze_unprocessed(self, request):
        """
        分析未处理的新闻
        
        请求体参数：
            - analysis_types: 分析类型列表，可选值：sentiment, keywords, summary
            - limit: 处理数量限制（可选）
        """
        try:
            analysis_types = request.data.get('analysis_types', ['sentiment', 'keywords', 'summary'])
            limit = request.data.get('limit')
            
            # 获取未处理的新闻
            unprocessed_news = await sync_to_async(list)(
                NewsArticle.objects.filter(
                    analysisresult__isnull=True
                ).distinct()[:limit] if limit else NewsArticle.objects.filter(
                    analysisresult__isnull=True
                ).distinct()
            )
            
            if not unprocessed_news:
                return JsonResponse({
                    'message': '没有未处理的新闻'
                })
            
            # 创建批量分析任务
            task = await sync_to_async(BatchAnalysisTask.objects.create)(
                status='pending',
                total_count=len(unprocessed_news),
                processed=0,
                success=0,
                failed=0
            )
            
            # 异步处理每篇新闻
            for news in unprocessed_news:
                try:
                    if not news.content:
                        continue
                    
                    for analysis_type in analysis_types:
                        try:
                            # 先检查缓存
                            cached_result = await self.ai_service._get_cached_result(news.id, analysis_type)
                            if cached_result:
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
                            await self.ai_service._cache_result(news.id, analysis_type, json.dumps(result))
                            
                            # 更新任务状态
                            task.success += 1
                        except Exception as e:
                            task.failed += 1
                    
                    task.processed += 1
                    await sync_to_async(task.save)()
                except Exception as e:
                    task.failed += 1
                    task.processed += 1
                    await sync_to_async(task.save)()
                    continue
            
            # 更新任务状态
            task.status = 'completed'
            await sync_to_async(task.save)()
            
            return JsonResponse({
                'task_id': task.id,
                'message': f'已处理 {task.processed} 篇新闻，成功 {task.success} 篇，失败 {task.failed} 篇'
            })
            
        except Exception as e:
            return JsonResponse({
                'error': 'internal_error',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    async def analyze_by_criteria(self, request):
        """
        根据条件分析新闻
        
        请求体参数：
        {
            "criteria": {
                "category": 1,  # 可选，分类ID
                "source": "新华网",  # 可选，新闻来源
                "start_date": "2024-01-01",  # 可选，开始日期
                "end_date": "2024-01-31"  # 可选，结束日期
            },
            "analysis_types": ["sentiment", "keywords", "summary"],  # 可选，分析类型列表
            "limit": 100  # 可选，处理数量限制
        }
        """
        criteria = request.data.get('criteria', {})
        analysis_types = request.data.get('analysis_types')
        limit = request.data.get('limit', 100)
        
        try:
            # 构建查询条件
            query = NewsArticle.objects.all()
            
            if 'category' in criteria:
                query = query.filter(category_id=criteria['category'])
            
            if 'source' in criteria:
                query = query.filter(source=criteria['source'])
            
            if 'start_date' in criteria:
                query = query.filter(publish_time__gte=parse_datetime(criteria['start_date']))
            
            if 'end_date' in criteria:
                query = query.filter(publish_time__lte=parse_datetime(criteria['end_date']))
            
            # 限制数量
            news_articles = query[:limit]
            
            if not news_articles.exists():
                return Response({
                    'message': '没有符合条件的新闻'
                })
            
            # 创建批量分析任务
            task = BatchAnalysisTask.objects.create(
                created_by=request.user,
                total_count=news_articles.count(),
                analysis_types=analysis_types,
                criteria=criteria
            )
            
            # 启动异步任务
            process_batch_analysis.delay(
                task.id,
                [article.id for article in news_articles],
                analysis_types
            )
            
            serializer = BatchAnalysisTaskSerializer(task)
            return Response({
                'message': '批量分析任务已创建',
                'data': serializer.data
            })
            
        except Exception as e:
            return Response({
                'message': '创建分析任务失败',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    async def analyze_with_rules(self, request, pk=None):
        """
        使用指定规则分析新闻
        
        请求体参数：
        {
            "rule_ids": [1, 2, 3]  # 可选，规则ID列表，不提供则使用所有启用的规则
        }
        """
        news_article = await sync_to_async(get_object_or_404)(NewsArticle, pk=pk)
        rule_ids = request.data.get('rule_ids')
        
        try:
            # 获取规则
            if rule_ids:
                rules = await sync_to_async(list)(AnalysisRule.objects.filter(
                    id__in=rule_ids,
                    is_active=True
                ))
                if not rules:
                    return Response({
                        'message': '未找到指定的有效规则'
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                rules = await sync_to_async(list)(AnalysisRule.objects.filter(is_active=True))
                if not rules:
                    return Response({
                        'message': '没有可用的分析规则'
                    }, status=status.HTTP_404_NOT_FOUND)
            
            # 执行分析
            results = await self.ai_service.batch_analyze_with_rules(
                [news_article],
                rules=rules
            )

            return Response({
                'message': '规则分析完成',
                'data': results.get(news_article.id, {})
            })
            
        except Exception as e:
            return Response({
                'message': '规则分析失败',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    async def batch_analyze_with_rules(self, request):
        """
        使用规则批量分析新闻
        
        请求体参数：
        {
            "rule_ids": [1, 2, 3],  # 规则ID列表
            "criteria": {  # 可选，筛选条件
                "category": 1,  # 可选，分类ID
                "source": "新华网",  # 可选，新闻来源
                "start_date": "2024-01-01",  # 可选，开始日期
                "end_date": "2024-01-31"  # 可选，结束日期
            },
            "limit": 100  # 可选，处理数量限制
        }
        """
        rule_ids = request.data.get('rule_ids', [])
        criteria = request.data.get('criteria', {})
        limit = request.data.get('limit', 100)
        
        if not rule_ids:
            return Response({
                'message': '请提供要使用的规则ID列表'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 获取规则
            rules = await sync_to_async(list)(AnalysisRule.objects.filter(
                id__in=rule_ids,
                is_active=True
            ))
            
            if not rules:
                return Response({
                    'message': '未找到有效的规则'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # 构建查询条件
            query = NewsArticle.objects.all()
            
            if 'category' in criteria:
                query = query.filter(category_id=criteria['category'])
            
            if 'source' in criteria:
                query = query.filter(source=criteria['source'])
            
            if 'start_date' in criteria:
                query = query.filter(publish_time__gte=parse_datetime(criteria['start_date']))
            
            if 'end_date' in criteria:
                query = query.filter(publish_time__lte=parse_datetime(criteria['end_date']))
            
            # 限制数量并获取结果
            news_articles = await sync_to_async(list)(query[:limit])
            
            if not news_articles:
                return Response({
                    'message': '没有符合条件的新闻'
                })
            
            # 创建批量分析任务
            task = await sync_to_async(BatchAnalysisTask.objects.create)(
                created_by=request.user,
                total_count=len(news_articles),
                rules=rules,
                criteria=criteria
            )
            
            # 启动异步任务
            process_batch_analysis.delay(
                task.id,
                [article.id for article in news_articles],
                rule_ids=rule_ids
            )
            
            serializer = BatchAnalysisTaskSerializer(task)
            return Response({
                'message': '批量分析任务已创建',
                'data': serializer.data
            })
            
        except Exception as e:
            return Response({
                'message': '创建分析任务失败',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    async def export_results(self, request):
        """
        导出分析结果
        
        请求参数：
            - format: 导出格式(csv/excel)，默认csv
            - start_date: 开始日期（可选）
            - end_date: 结束日期（可选）
            - rule_id: 规则ID（可选）
            - category_id: 分类ID（可选）
            - source: 新闻来源（可选）
        """
        try:
            # 获取请求参数
            export_format = request.query_params.get('format', 'csv')
            if export_format not in ['csv', 'excel']:
                return Response({
                    'message': '不支持的导出格式'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 解析日期参数
            start_date = request.query_params.get('start_date')
            if start_date:
                start_date = parse_datetime(start_date)
            
            end_date = request.query_params.get('end_date')
            if end_date:
                end_date = parse_datetime(end_date)
            
            # 其他过滤参数
            rule_id = request.query_params.get('rule_id')
            category_id = request.query_params.get('category_id')
            source = request.query_params.get('source')
            
            # 构建查询条件
            query = AnalysisResult.objects.filter(is_valid=True)
            
            if start_date:
                query = query.filter(created_at__gte=start_date)
            
            if end_date:
                query = query.filter(created_at__lte=end_date)
            
            if rule_id:
                query = query.filter(rule_id=rule_id)
            
            if category_id:
                query = query.filter(news__category_id=category_id)
            
            if source:
                query = query.filter(news__source=source)
            
            # 获取查询结果
            results = await sync_to_async(list)(query)
            
            # 导出数据
            ai_service = AIService()
            content, content_type, file_ext = await sync_to_async(ai_service.export_analysis_results)(
                results,
                format=export_format
            )
            
            # 生成文件名
            filename = f'analysis_results_{timezone.now().strftime("%Y%m%d_%H%M%S")}{file_ext}'
            
            # 返回文件
            response = HttpResponse(content, content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
            
        except Exception as e:
            return Response({
                'message': '导出失败',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AnalysisRuleViewSet(AsyncViewSet):
    """分析规则视图集"""
    
    queryset = AnalysisRule.objects.all()
    serializer_class = AnalysisRuleSerializer
    permission_classes = [IsAdminUser]  # 只有管理员可以管理规则
    
    async def perform_create(self, serializer):
        """创建规则时设置创建者"""
        await sync_to_async(serializer.save)(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    async def toggle_active(self, request, pk=None):
        """切换规则的启用状态"""
        rule = await sync_to_async(self.get_object)()
        rule.is_active = not rule.is_active
        await sync_to_async(rule.save)()
        
        return Response({
            'message': f"规则已{'启用' if rule.is_active else '禁用'}",
            'is_active': rule.is_active
        })
    
    @action(detail=True, methods=['post'])
    async def test_rule(self, request, pk=None):
        """测试分析规则"""
        rule = await sync_to_async(self.get_object)()
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
        
        try:
            ai_service = AIService()
            result = await ai_service.analyze_with_rule(news_article, rule)
            
            return Response({
                'message': '规则测试成功',
                'data': result
            })
        except Exception as e:
            return Response({
                'message': '规则测试失败',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    async def export_results(self, request, pk=None):
        """
        导出规则分析结果
        
        请求参数：
            - format: 导出格式(csv/excel)，默认csv
            - start_date: 开始日期（可选）
            - end_date: 结束日期（可选）
        """
        try:
            rule = await sync_to_async(self.get_object)()
            
            # 获取请求参数
            export_format = request.query_params.get('format', 'csv')
            if export_format not in ['csv', 'excel']:
                return Response({
                    'message': '不支持的导出格式'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            start_date = request.query_params.get('start_date')
            if start_date:
                start_date = parse_datetime(start_date)
            
            end_date = request.query_params.get('end_date')
            if end_date:
                end_date = parse_datetime(end_date)
            
            # 导出数据
            ai_service = AIService()
            content, content_type, file_ext = await sync_to_async(ai_service.export_rule_analysis_results)(
                rule_id=rule.id,
                format=export_format,
                start_date=start_date,
                end_date=end_date
            )
            
            # 生成文件名
            filename = f'rule_{rule.id}_results_{timezone.now().strftime("%Y%m%d_%H%M%S")}{file_ext}'
            
            # 返回文件
            response = HttpResponse(content, content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
            
        except Exception as e:
            return Response({
                'message': '导出失败',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class BatchAnalysisTaskViewSet(AsyncViewSet):
    """批量分析任务视图集"""
    
    queryset = BatchAnalysisTask.objects.all()
    serializer_class = BatchAnalysisTaskSerializer
    permission_classes = [IsAuthenticated]
    
    async def get_queryset(self):
        """获取查询集"""
        try:
            return await sync_to_async(list)(self.queryset.order_by('-created_at'))
        except Exception:
            return []
    
    async def perform_create(self, serializer):
        """创建任务时设置创建者"""
        await sync_to_async(serializer.save)(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    async def results(self, request, pk=None):
        """获取任务结果"""
        try:
            task = await sync_to_async(self.get_object)()
            results = await sync_to_async(list)(BatchAnalysisResult.objects.filter(task=task))
            serializer = BatchAnalysisResultSerializer(results, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    async def retry(self, request, pk=None):
        """重试失败的任务"""
        try:
            task = await sync_to_async(self.get_object)()
            if task.status != 'failed':
                return Response({
                    'message': '只能重试失败的任务'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            task.status = 'pending'
            task.error_message = ''
            await sync_to_async(task.save)()
            
            process_batch_analysis.delay(task.id)
            
            return Response({
                'message': '任务已重新提交'
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AnalysisScheduleViewSet(AsyncViewSet):
    """分析计划视图集"""
    
    queryset = AnalysisSchedule.objects.all()
    serializer_class = AnalysisScheduleSerializer
    permission_classes = [IsAdminUser]
    
    async def get_queryset(self):
        """获取查询集"""
        try:
            return await sync_to_async(list)(self.queryset.order_by('-created_at'))
        except Exception:
            return []
    
    async def perform_create(self, serializer):
        """创建计划时设置创建者"""
        await sync_to_async(serializer.save)(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    async def toggle_active(self, request, pk=None):
        """切换计划的启用状态"""
        try:
            schedule = await sync_to_async(self.get_object)()
            schedule.is_active = not schedule.is_active
            await sync_to_async(schedule.save)()
            
            return Response({
                'message': f"计划已{'启用' if schedule.is_active else '禁用'}",
                'is_active': schedule.is_active
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    async def execute(self, request, pk=None):
        """立即执行计划"""
        try:
            schedule = await sync_to_async(self.get_object)()
            execution = await sync_to_async(ScheduleExecution.objects.create)(
                schedule=schedule,
                status='pending'
            )
            
            process_schedule_execution.delay(execution.id)
            
            return Response({
                'message': '计划已提交执行',
                'execution_id': execution.id
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ScheduleExecutionViewSet(AsyncViewSet):
    """计划执行记录视图集"""
    
    queryset = ScheduleExecution.objects.all()
    serializer_class = ScheduleExecutionSerializer
    permission_classes = [IsAuthenticated]
    
    async def get_queryset(self):
        """获取查询集"""
        try:
            queryset = self.queryset
            if not self.request.user.is_staff:
                queryset = queryset.filter(schedule__created_by=self.request.user)
            return await sync_to_async(list)(queryset.order_by('-created_at'))
        except Exception:
            return []
    
    @action(detail=True, methods=['post'])
    async def retry(self, request, pk=None):
        """重试失败的执行"""
        try:
            execution = await sync_to_async(self.get_object)()
            if execution.status != 'failed':
                return Response({
                    'message': '只能重试失败的执行'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            execution.status = 'pending'
            execution.error_message = ''
            await sync_to_async(execution.save)()
            
            process_schedule_execution.delay(execution.id)
            
            return Response({
                'message': '执行已重新提交'
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class NotificationViewSet(AsyncViewSet):
    """通知视图集"""
    
    queryset = AnalysisNotification.objects.all()
    serializer_class = AnalysisNotificationSerializer
    permission_classes = [IsAuthenticated]
    
    async def get_queryset(self):
        """获取查询集"""
        try:
            return await sync_to_async(list)(self.queryset.filter(user=self.request.user).order_by('-created_at'))
        except Exception:
            return []
    
    @action(detail=True, methods=['post'])
    async def mark_as_read(self, request, pk=None):
        """标记通知为已读"""
        try:
            notification = await sync_to_async(self.get_object)()
            notification.is_read = True
            await sync_to_async(notification.save)()
            
            return Response({
                'message': '通知已标记为已读'
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    async def mark_all_as_read(self, request):
        """标记所有通知为已读"""
        try:
            await sync_to_async(self.get_queryset().filter(is_read=False).update)(is_read=True)
            return Response({
                'message': '所有通知已标记为已读'
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    async def unread_count(self, request):
        """获取未读通知数量"""
        try:
            count = await sync_to_async(self.get_queryset().filter(is_read=False).count)()
            return Response({
                'count': count
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class NotificationSubscriptionViewSet(AsyncViewSet):
    """通知订阅视图集"""
    
    queryset = NotificationSubscription.objects.all()
    serializer_class = NotificationSubscriptionSerializer
    permission_classes = [IsAuthenticated]
    
    async def get_object(self):
        """获取或创建用户的订阅"""
        try:
            subscription, _ = await sync_to_async(NotificationSubscription.objects.get_or_create)(
                user=self.request.user
            )
            return subscription
        except Exception as e:
            raise e
    
    async def perform_create(self, serializer):
        """创建订阅时设置用户"""
        await sync_to_async(serializer.save)(user=self.request.user)

class AnalysisVisualizationViewSet(AsyncViewSet):
    """分析可视化视图集"""
    
    queryset = AnalysisVisualization.objects.all()
    serializer_class = AnalysisVisualizationSerializer
    permission_classes = [IsAuthenticated]
    
    async def get_queryset(self):
        """获取查询集"""
        try:
            return await sync_to_async(list)(self.queryset.filter(created_by=self.request.user))
        except Exception:
            return []
    
    async def perform_create(self, serializer):
        """创建可视化时设置创建者"""
        await sync_to_async(serializer.save)(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    async def data(self, request, pk=None):
        """获取可视化数据"""
        try:
            visualization = await sync_to_async(self.get_object)()
            visualization_service = VisualizationService()
            data = await sync_to_async(visualization_service.get_visualization_data)(visualization)
            return Response(data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    async def refresh(self, request, pk=None):
        """刷新可视化数据"""
        try:
            visualization = await sync_to_async(self.get_object)()
            visualization_service = VisualizationService()
            await sync_to_async(visualization_service.refresh_visualization_data)(visualization)
            return Response({
                'message': '数据已刷新'
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    async def available_fields(self, request):
        """获取可用字段列表"""
        try:
            visualization_service = VisualizationService()
            fields = await sync_to_async(visualization_service.get_available_fields)()
            return Response(fields)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
