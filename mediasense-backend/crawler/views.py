from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Q
import sys
import uuid

from .models import CrawlerConfig, CrawlerTask
from .serializers import (
    CrawlerConfigSerializer, 
    CrawlerTaskDetailSerializer, 
    CrawlerTaskSerializer,
    CrawlerConfigBulkSerializer,
    CrawlerTaskBulkSerializer
)
from .services import CrawlerService
from .tasks import crawl_single_website


class CrawlerConfigViewSet(viewsets.ModelViewSet):
    """爬虫配置视图集"""

    queryset = CrawlerConfig.objects.all()
    serializer_class = CrawlerConfigSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def enable(self, request, pk=None):
        """启用爬虫配置"""
        config = self.get_object()
        config.status = 1
        config.is_active = True
        config.save()
        return Response({'status': 'success', 'is_active': True})

    @action(detail=True, methods=['post'])
    def disable(self, request, pk=None):
        """禁用爬虫配置"""
        config = self.get_object()
        
        # 更新配置状态为禁用
        config.status = 0
        config.is_active = False
        config.save()
        
        # 停止所有运行中的任务
        running_tasks = CrawlerTask.objects.filter(
            config=config,
            status__in=[CrawlerTask.Status.PENDING, CrawlerTask.Status.RUNNING]
        )
        for task in running_tasks:
            task.status = CrawlerTask.Status.CANCELLED
            task.end_time = timezone.now()
            task.save()
        
        return Response({"status": "success", "is_active": False})

    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """测试爬虫配置"""
        try:
            config = self.get_object()
            
            # 检查配置是否有效
            if not config.source_url:
                return Response(
                    {'error': 'source_url is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not config.config_data:
                return Response(
                    {'error': 'config_data is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 检查配置数据格式
            if not isinstance(config.config_data, dict):
                return Response(
                    {'error': 'config_data must be a dictionary'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 检查爬虫类型相关的必要配置
            if config.crawler_type == 1:  # RSS
                required_fields = ['title_path', 'content_path', 'link_path', 'pub_date_path']
                missing_fields = [field for field in required_fields if field not in config.config_data]
                if missing_fields:
                    return Response(
                        {'error': f'Missing required fields for RSS crawler: {", ".join(missing_fields)}'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            elif config.crawler_type == 2:  # API
                required_fields = ['title_path', 'content_path', 'link_path', 'pub_date_path']
                missing_fields = [field for field in required_fields if field not in config.config_data]
                if missing_fields:
                    return Response(
                        {'error': f'Missing required fields for API crawler: {", ".join(missing_fields)}'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            elif config.crawler_type == 3:  # HTML
                required_fields = ['title_selector', 'content_selector', 'link_selector', 'pub_date_selector']
                missing_fields = [field for field in required_fields if field not in config.config_data]
                if missing_fields:
                    return Response(
                        {'error': f'Missing required fields for HTML crawler: {", ".join(missing_fields)}'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # 先创建任务记录
            task = CrawlerTask.objects.create(
                config=config,
                task_id=str(uuid.uuid4()),
                status=CrawlerTask.Status.PENDING,
                is_test=True
            )
            
            # 调用异步任务
            crawl_single_website.delay(config.id)
            
            return Response({
                'status': 'success',
                'task_id': task.task_id,
                'test_results': {
                    'config_id': config.id,
                    'source_url': config.source_url,
                    'crawler_type': config.crawler_type,
                    'config_data': config.config_data
                }
            })
        except Exception as e:
            import traceback
            return Response(
                {
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def retrieve(self, request, *args, **kwargs):
        """获取配置详情,包含统计数据"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        
        # 添加统计数据
        tasks = instance.crawlertask_set.all()
        data.update({
            'total_tasks': tasks.count(),
            'total_items': sum(
                task.result.get('items_count', 0)
                for task in tasks.filter(status=CrawlerTask.Status.COMPLETED)
                if task.result
            ),
            'success_rate': round(
                tasks.filter(status=CrawlerTask.Status.COMPLETED).count() / tasks.count() * 100
                if tasks.exists() else 0,
                2
            )
        })
        
        return Response(data)

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """批量创建爬虫配置"""
        serializer = CrawlerConfigBulkSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        configs = [CrawlerConfig(**item) for item in serializer.validated_data]
        created_configs = CrawlerConfig.objects.bulk_create(configs)
        return Response(
            CrawlerConfigBulkSerializer(created_configs, many=True).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['put'])
    def bulk_update(self, request):
        """批量更新爬虫配置"""
        serializer = CrawlerConfigBulkSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_bulk_update(serializer)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        """批量删除爬虫配置"""
        ids = request.data.get('ids', [])
        if not ids:
            return Response({"error": "No IDs provided"}, status=status.HTTP_400_BAD_REQUEST)
        CrawlerConfig.objects.filter(id__in=ids).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """获取爬虫配置统计信息"""
        total_configs = CrawlerConfig.objects.count()
        active_configs = CrawlerConfig.objects.filter(is_active=True).count()
        total_tasks = CrawlerTask.objects.count()
        task_status_counts = dict(CrawlerTask.objects.values('status').annotate(count=Count('id')))
        
        return Response({
            'total_configs': total_configs,
            'active_configs': active_configs,
            'total_tasks': total_tasks,
            'task_status_counts': task_status_counts
        })


class CrawlerTaskViewSet(viewsets.ModelViewSet):
    """爬虫任务视图集"""

    queryset = CrawlerTask.objects.all()
    serializer_class = CrawlerTaskSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CrawlerTaskDetailSerializer
        return CrawlerTaskSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        # 支持按配置ID过滤
        config_id = self.request.query_params.get("config_id")
        if config_id:
            queryset = queryset.filter(config_id=config_id)
        # 支持按状态过滤
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """重试失败的任务"""
        task = self.get_object()
        if task.status != CrawlerTask.Status.ERROR:  # 只能重试失败的任务
            return Response(
                {'error': 'Only failed tasks can be retried'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        new_task = crawl_single_website.delay(task.config.id)
        return Response({
            'status': CrawlerTask.Status.PENDING,
            'task_id': new_task.id
        })

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """取消待执行的任务"""
        task = self.get_object()
        if task.status != CrawlerTask.Status.PENDING:
            return Response({"status": "error", "message": "只能取消待执行的任务"}, status=status.HTTP_400_BAD_REQUEST)

        # 更新任务状态
        task.status = CrawlerTask.Status.CANCELLED
        task.end_time = timezone.now()
        task.save()
        return Response({"status": "success"})

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """批量创建爬虫任务"""
        serializer = CrawlerTaskBulkSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_bulk_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['put'])
    def bulk_update(self, request):
        """批量更新爬虫任务"""
        serializer = CrawlerTaskBulkSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_bulk_update(serializer)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        """批量删除爬虫任务"""
        ids = request.data.get('ids', [])
        if not ids:
            return Response({"error": "No IDs provided"}, status=status.HTTP_400_BAD_REQUEST)
        CrawlerTask.objects.filter(id__in=ids).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """获取爬虫任务统计信息"""
        total_tasks = CrawlerTask.objects.count()
        status_counts = dict(CrawlerTask.objects.values('status').annotate(count=Count('id')))
        success_rate = round(
            CrawlerTask.objects.filter(status=CrawlerTask.Status.COMPLETED).count() / total_tasks * 100
            if total_tasks else 0,
            2
        )
        
        return Response({
            'total_tasks': total_tasks,
            'status_counts': status_counts,
            'success_rate': success_rate
        })
