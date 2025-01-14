from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from .models import CrawlerConfig, CrawlerTask
from .serializers import CrawlerConfigSerializer, CrawlerTaskDetailSerializer, CrawlerTaskSerializer
from .services import CrawlerService
from .tasks import execute_crawler_task


class CrawlerConfigViewSet(viewsets.ModelViewSet):
    """爬虫配置管理视图集"""

    queryset = CrawlerConfig.objects.all()
    serializer_class = CrawlerConfigSerializer
    permission_classes = [IsAdminUser]

    @action(detail=True, methods=["post"])
    def enable(self, request, pk=None):
        """启用爬虫配置"""
        config = self.get_object()
        config.enabled = True
        config.save()
        return Response({"status": "success"})

    @action(detail=True, methods=["post"])
    def disable(self, request, pk=None):
        """禁用爬虫配置"""
        config = self.get_object()
        config.enabled = False
        config.save()
        return Response({"status": "success"})

    @action(detail=True, methods=["post"])
    def test(self, request, pk=None):
        """测试爬虫配置"""
        config = self.get_object()
        try:
            # 创建测试任务
            task = CrawlerTask.objects.create(config=config, status=CrawlerTask.Status.PENDING, is_test=True)
            # 异步执行任务
            execute_crawler_task.delay(task.id)
            return Response({"status": "success", "task_id": task.id})
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CrawlerTaskViewSet(viewsets.ReadOnlyModelViewSet):
    """爬虫任务管理视图集"""

    queryset = CrawlerTask.objects.all()
    permission_classes = [IsAdminUser]

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

    @action(detail=True, methods=["post"])
    def retry(self, request, pk=None):
        """重试失败的任务"""
        task = self.get_object()
        if task.status != CrawlerTask.Status.FAILED:
            return Response({"status": "error", "message": "只能重试失败的任务"}, status=status.HTTP_400_BAD_REQUEST)

        # 重置任务状态
        task.status = CrawlerTask.Status.PENDING
        task.error_message = ""
        task.start_time = None
        task.end_time = None
        task.save()

        # 异步执行任务
        execute_crawler_task.delay(task.id)
        return Response({"status": "success"})

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
