from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

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
from .services import AIService, VisualizationService
from .tasks import process_batch_analysis, process_schedule_execution


class AnalysisRuleViewSet(viewsets.ModelViewSet):
    """分析规则视图集"""
    
    queryset = AnalysisRule.objects.all()
    serializer_class = AnalysisRuleSerializer
    permission_classes = [IsAdminUser]  # 只有管理员可以管理规则
    
    def perform_create(self, serializer):
        """创建规则时设置创建者"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """切换规则的启用状态"""
        rule = self.get_object()
        rule.is_active = not rule.is_active
        rule.save()
        
        return Response({
            'message': f"规则已{'启用' if rule.is_active else '禁用'}",
            'is_active': rule.is_active
        })
    
    @action(detail=True, methods=['post'])
    async def test_rule(self, request, pk=None):
        """测试分析规则"""
        rule = self.get_object()
        news_id = request.data.get('news_id')
        
        if not news_id:
            return Response({
                'message': '请提供要测试的新闻ID'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            news_article = NewsArticle.objects.get(id=news_id)
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
    def export_results(self, request, pk=None):
        """
        导出规则分析结果
        
        请求参数：
            - format: 导出格式(csv/excel)，默认csv
            - start_date: 开始日期（可选）
            - end_date: 结束日期（可选）
        """
        try:
            rule = self.get_object()
            
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
            content, content_type, file_ext = ai_service.export_rule_analysis_results(
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

class AIServiceViewSet(viewsets.ViewSet):
    """AI服务视图集"""
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ai_service = AIService()
    
    @action(detail=True, methods=['post'])
    async def analyze_sentiment(self, request, pk=None):
        """
        分析新闻情感
        """
        news_article = get_object_or_404(NewsArticle, pk=pk)
        
        try:
            result = await self.ai_service.analyze_sentiment(news_article)
            return Response({
                'message': '情感分析完成',
                'data': result
            })
        except Exception as e:
            return Response({
                'message': '情感分析失败',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    async def extract_keywords(self, request, pk=None):
        """
        提取新闻关键词
        """
        news_article = get_object_or_404(NewsArticle, pk=pk)
        
        try:
            result = await self.ai_service.extract_keywords(news_article)
            return Response({
                'message': '关键词提取完成',
                'data': result
            })
        except Exception as e:
            return Response({
                'message': '关键词提取失败',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    async def generate_summary(self, request, pk=None):
        """
        生成新闻摘要
        """
        news_article = get_object_or_404(NewsArticle, pk=pk)
        
        try:
            result = await self.ai_service.generate_summary(news_article)
            return Response({
                'message': '摘要生成完成',
                'data': result
            })
        except Exception as e:
            return Response({
                'message': '摘要生成失败',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def get_analysis(self, request, pk=None):
        """
        获取新闻的所有分析结果
        """
        news_article = get_object_or_404(NewsArticle, pk=pk)
        analysis_results = AnalysisResult.objects.filter(
            news=news_article,
            is_valid=True
        )
        
        serializer = AnalysisResultSerializer(analysis_results, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def invalidate_cache(self, request):
        """
        使所有缓存失效
        """
        try:
            self.ai_service.invalidate_cache()
            return Response({
                'message': '缓存已清空'
            })
        except Exception as e:
            return Response({
                'message': '清空缓存失败',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def clean_cache(self, request):
        """
        清理过期缓存
        """
        try:
            self.ai_service.clean_expired_cache()
            return Response({
                'message': '过期缓存已清理'
            })
        except Exception as e:
            return Response({
                'message': '清理缓存失败',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    async def batch_analyze(self, request):
        """
        批量分析新闻
        
        请求体参数：
        {
            "news_ids": [1, 2, 3],  # 新闻ID列表
            "analysis_types": ["sentiment", "keywords", "summary"]  # 可选，分析类型列表
        }
        """
        news_ids = request.data.get('news_ids', [])
        analysis_types = request.data.get('analysis_types')
        
        if not news_ids:
            return Response({
                'message': '请提供要分析的新闻ID列表'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # 创建批量分析任务
        task = BatchAnalysisTask.objects.create(
            created_by=request.user,
            total_count=len(news_ids),
            analysis_types=analysis_types
        )
        
        # 启动异步任务
        process_batch_analysis.delay(task.id, news_ids, analysis_types)
        
        serializer = BatchAnalysisTaskSerializer(task)
        return Response({
            'message': '批量分析任务已创建',
            'data': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    async def analyze_unprocessed(self, request):
        """
        分析未处理的新闻
        
        请求体参数：
        {
            "analysis_types": ["sentiment", "keywords", "summary"],  # 可选，分析类型列表
            "limit": 100  # 可选，处理数量限制
        }
        """
        analysis_types = request.data.get('analysis_types')
        limit = request.data.get('limit', 100)
        
        try:
            # 获取未处理的新闻
            news_articles = NewsArticle.objects.filter(
                analysisresult__isnull=True
            )[:limit]
            
            if not news_articles.exists():
                return Response({
                    'message': '没有未处理的新闻'
                })
            
            # 创建批量分析任务
            task = BatchAnalysisTask.objects.create(
                created_by=request.user,
                total_count=news_articles.count(),
                analysis_types=analysis_types
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
        news_article = get_object_or_404(NewsArticle, pk=pk)
        rule_ids = request.data.get('rule_ids')
        
        try:
            # 获取规则
            if rule_ids:
                rules = AnalysisRule.objects.filter(
                    id__in=rule_ids,
                    is_active=True
                )
                if not rules.exists():
                    return Response({
                        'message': '未找到指定的有效规则'
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                rules = AnalysisRule.objects.filter(is_active=True)
                if not rules.exists():
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
            rules = AnalysisRule.objects.filter(
                id__in=rule_ids,
                is_active=True
            )
            
            if not rules.exists():
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
    def export_results(self, request):
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
            
            # 导出数据
            ai_service = AIService()
            content, content_type, file_ext = ai_service.export_analysis_results(
                query,
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

class BatchAnalysisTaskViewSet(mixins.CreateModelMixin,
                             mixins.RetrieveModelMixin,
                             mixins.ListModelMixin,
                             viewsets.GenericViewSet):
    """批量分析任务视图集"""
    
    queryset = BatchAnalysisTask.objects.all()
    serializer_class = BatchAnalysisTaskSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """根据用户过滤任务"""
        return self.queryset.filter(created_by=self.request.user)
    
    def perform_create(self, serializer):
        """创建任务时设置创建者"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """获取任务的分析结果"""
        task = self.get_object()
        results = BatchAnalysisResult.objects.filter(task=task)
        serializer = BatchAnalysisResultSerializer(results, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """重试失败的任务"""
        task = self.get_object()
        
        if task.status not in ['failed', 'cancelled']:
            return Response({
                'message': '只能重试失败或已取消的任务'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 重置任务状态
        task.status = 'pending'
        task.error_message = None
        task.save()
        
        # 重新启动任务
        process_batch_analysis.delay(task.id)
        
        return Response({
            'message': '任务已重新启动'
        })
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """取消正在进行的任务"""
        task = self.get_object()
        
        if task.status not in ['pending', 'processing']:
            return Response({
                'message': '只能取消等待中或处理中的任务'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        task.status = 'cancelled'
        task.save()
        
        return Response({
            'message': '任务已取消'
        })

class AnalysisScheduleViewSet(viewsets.ModelViewSet):
    """分析任务调度视图集"""
    
    queryset = AnalysisSchedule.objects.all()
    serializer_class = AnalysisScheduleSerializer
    permission_classes = [IsAdminUser]  # 只有管理员可以管理调度
    
    def perform_create(self, serializer):
        """创建调度时设置创建者"""
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        """更新调度时设置更新者"""
        serializer.save(updated_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """切换调度的启用状态"""
        schedule = self.get_object()
        schedule.is_active = not schedule.is_active
        schedule.save()
        
        # 如果启用了调度，立即执行一次
        if schedule.is_active:
            process_schedule_execution.delay(schedule.id)
        
        return Response({
            'message': f"调度已{'启用' if schedule.is_active else '禁用'}",
            'is_active': schedule.is_active
        })
    
    @action(detail=True, methods=['post'])
    def execute_now(self, request, pk=None):
        """立即执行调度任务"""
        schedule = self.get_object()
        
        if not schedule.is_active:
            return Response({
                'message': '调度未启用'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 创建执行记录并启动任务
        execution = ScheduleExecution.objects.create(
            schedule=schedule,
            triggered_by=self.request.user
        )
        process_schedule_execution.delay(schedule.id, execution.id)
        
        return Response({
            'message': '调度任务已启动'
        })
    
    @action(detail=True, methods=['get'])
    def executions(self, request, pk=None):
        """获取调度的执行记录"""
        schedule = self.get_object()
        executions = ScheduleExecution.objects.filter(schedule=schedule)
        
        # 分页
        page = self.paginate_queryset(executions)
        if page is not None:
            serializer = ScheduleExecutionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ScheduleExecutionSerializer(executions, many=True)
        return Response(serializer.data)

class ScheduleExecutionViewSet(mixins.RetrieveModelMixin,
                             mixins.ListModelMixin,
                             viewsets.GenericViewSet):
    """调度执行记录视图集"""
    
    queryset = ScheduleExecution.objects.all()
    serializer_class = ScheduleExecutionSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        """根据条件过滤执行记录"""
        queryset = self.queryset
        
        # 按调度过滤
        schedule_id = self.request.query_params.get('schedule_id')
        if schedule_id:
            queryset = queryset.filter(schedule_id=schedule_id)
        
        # 按状态过滤
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # 按日期范围过滤
        start_date = self.request.query_params.get('start_date')
        if start_date:
            queryset = queryset.filter(created_at__gte=parse_datetime(start_date))
        
        end_date = self.request.query_params.get('end_date')
        if end_date:
            queryset = queryset.filter(created_at__lte=parse_datetime(end_date))
        
        return queryset.order_by('-created_at')

class NotificationViewSet(viewsets.GenericViewSet,
                       mixins.ListModelMixin,
                       mixins.RetrieveModelMixin):
    """通知视图集"""
    
    permission_classes = [IsAuthenticated]
    serializer_class = AnalysisNotificationSerializer
    
    def get_queryset(self):
        """获取查询集"""
        return AnalysisNotification.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """标记通知为已读"""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        
        return Response({
            'message': '通知已标记为已读'
        })
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """标记所有通知为已读"""
        self.get_queryset().filter(is_read=False).update(is_read=True)
        
        return Response({
            'message': '所有通知已标记为已读'
        })
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """获取未读通知数量"""
        count = self.get_queryset().filter(is_read=False).count()
        
        return Response({
            'count': count
        })

class NotificationSubscriptionViewSet(viewsets.GenericViewSet,
                                    mixins.RetrieveModelMixin,
                                    mixins.UpdateModelMixin):
    """通知订阅配置视图集"""
    
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSubscriptionSerializer
    
    def get_object(self):
        """获取或创建用户的订阅配置"""
        subscription, _ = NotificationSubscription.objects.get_or_create(
            user=self.request.user
        )
        return subscription

class AnalysisVisualizationViewSet(viewsets.ModelViewSet):
    """分析可视化视图集"""
    
    queryset = AnalysisVisualization.objects.all()
    serializer_class = AnalysisVisualizationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """根据用户过滤可视化"""
        return self.queryset.filter(created_by=self.request.user)
    
    def perform_create(self, serializer):
        """创建可视化时设置创建者"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def data(self, request, pk=None):
        """获取可视化数据"""
        visualization = self.get_object()
        
        try:
            visualization_service = VisualizationService()
            data = visualization_service.get_visualization_data(visualization)
            
            return Response({
                'data': data
            })
        except Exception as e:
            return Response({
                'message': '获取可视化数据失败',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def refresh(self, request, pk=None):
        """刷新可视化数据"""
        visualization = self.get_object()
        
        try:
            visualization_service = VisualizationService()
            data = visualization_service.refresh_visualization_data(visualization)
            
            return Response({
                'message': '可视化数据已刷新',
                'data': data
            })
        except Exception as e:
            return Response({
                'message': '刷新可视化数据失败',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def available_fields(self, request):
        """获取可用于可视化的字段列表"""
        try:
            visualization_service = VisualizationService()
            fields = visualization_service.get_available_fields()
            
            return Response({
                'fields': fields
            })
        except Exception as e:
            return Response({
                'message': '获取字段列表失败',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
