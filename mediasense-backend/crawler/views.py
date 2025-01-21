from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import sys

from .models import CrawlerConfig, CrawlerTask
from .serializers import CrawlerConfigSerializer, CrawlerTaskDetailSerializer, CrawlerTaskSerializer
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
        config.save()
        return Response({'status': 'success'})

    @action(detail=True, methods=['post'])
    def disable(self, request, pk=None):
        """禁用爬虫配置"""
        config = self.get_object()
        
        # 更新配置状态为禁用
        config.status = 0
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
        
        return Response({"status": "success"})

    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """测试爬虫配置"""
        config = self.get_object()
        task = crawl_single_website.delay(config.id)
        return Response({
            'status': 'success',
            'task_id': task.id
        })

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
                for task in tasks.filter(status=2)  # 已完成状态
                if task.result
            ),
            'success_rate': round(
                tasks.filter(status=2).count() / tasks.count() * 100
                if tasks.exists() else 0,
                2
            )
        })
        
        return Response(data)


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
        if task.status != 4:  # 只能重试失败的任务
            return Response(
                {'error': 'Only failed tasks can be retried'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        new_task = crawl_single_website.delay(task.config.id)
        return Response({
            'status': 'success',
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
