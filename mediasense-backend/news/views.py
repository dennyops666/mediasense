"""新闻管理模块视图."""

from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import (
    F,
    Max,
)
from django.http import HttpResponse
from django.utils import timezone

from rest_framework import filters, permissions, status, viewsets, serializers
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination

from custom_auth.permissions import ActionBasedPermission
from .models import (
    NewsArticle,
    NewsCategory,
    NewsAuditLog,
)
from .serializers import (
    CategoryMoveSerializer,
    CategoryTreeSerializer,
    ImportResultSerializer,
    NewsArticleAuditSerializer,
    NewsArticleCreateSerializer,
    NewsArticleExportSerializer,
    NewsArticleReviewSerializer,
    NewsArticleSerializer,
    NewsArticleUpdateSerializer,
    NewsAuditLogSerializer,
    NewsCategorySerializer,
)
from .filters import NewsFilter


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class NewsViewSet(viewsets.ModelViewSet):
    """新闻管理视图集."""

    queryset = NewsArticle.objects.all()
    serializer_class = NewsArticleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = NewsFilter
    search_fields = ['title', 'content']
    ordering_fields = ['publish_time', 'created_at']
    pagination_class = StandardResultsSetPagination

    @action(detail=False, methods=['get'])
    def categories(self, request):
        categories = NewsCategory.objects.all()
        serializer = NewsCategorySerializer(categories, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['put'])
    def bulk_update(self, request):
        """批量更新新闻文章."""
        data = request.data
        print('Request data:', data)
        print('Request data type:', type(data))
        
        # 如果是QueryDict,获取items列表
        if hasattr(data, 'getlist'):
            items = data.getlist('items', [])
        else:
            items = data.get('items', [])
            
        print('Items:', items)
        print('Items type:', type(items))
        
        if not items:
            return Response(
                {'error': '缺少必要的参数'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 解析每个item字符串为字典
        parsed_items = []
        for item in items:
            if isinstance(item, str):
                try:
                    # 移除单引号,替换为双引号
                    item = item.replace("'", '"')
                    import json
                    parsed_item = json.loads(item)
                    parsed_items.append(parsed_item)
                except json.JSONDecodeError:
                    return Response(
                        {'error': f'无效的JSON格式: {item}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                parsed_items.append(item)
                
        print('Parsed items:', parsed_items)
        
        # 验证每个item的格式
        for item in parsed_items:
            if not isinstance(item, dict):
                return Response(
                    {'error': '每个item必须是一个字典'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if 'id' not in item:
                return Response(
                    {'error': '每个item必须包含id字段'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if 'status' not in item:
                return Response(
                    {'error': '每个item必须包含status字段'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if item['status'] not in ['draft', 'pending', 'published', 'rejected']:
                return Response(
                    {'error': f'无效的状态值: {item["status"]}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        try:
            updated = 0
            for item in parsed_items:
                news_id = item['id']
                status_value = item['status']
                updated += NewsArticle.objects.filter(id=news_id).update(
                    status=status_value,
                    updated_at=timezone.now()
                )
            return Response({'updated': updated}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        """批量删除新闻文章."""
        data = request.data
        ids = data.get('ids', [])
        
        if not ids:
            return Response(
                {'error': '缺少必要的参数'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            deleted = NewsArticle.objects.filter(id__in=ids).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class NewsCategoryViewSet(viewsets.ModelViewSet):
    """新闻分类管理视图集."""

    queryset = NewsCategory.objects.all()
    serializer_class = NewsCategorySerializer
    permission_classes = [ActionBasedPermission]
    action_permissions = {
        'list': [permissions.AllowAny],
        'retrieve': [permissions.AllowAny],
        'create': [permissions.IsAdminUser],
        'update': [permissions.IsAdminUser],
        'partial_update': [permissions.IsAdminUser],
        'destroy': [permissions.IsAdminUser],
    }

    def get_queryset(self):
        """获取分类查询集."""
        return self.queryset.filter(is_active=True)

    def perform_create(self, serializer):
        """创建分类."""
        serializer.save()

    def perform_update(self, serializer):
        """更新分类."""
        serializer.save()

    def perform_destroy(self, instance):
        """删除分类前检查是否有关联文章."""
        if instance.articles.exists():
            raise serializers.ValidationError('该分类下存在文章，无法删除')
        instance.delete()

    def get_serializer_class(self):
        """根据不同的动作返回不同的序列化器"""
        if self.action == "tree":
            return CategoryTreeSerializer
        elif self.action == "move":
            return CategoryMoveSerializer
        return self.serializer_class

    @action(detail=False, methods=["get"])
    def tree(self, request):
        """获取分类树形结构"""
        root_categories = self.get_queryset().filter(parent__isnull=True)
        serializer = self.get_serializer(root_categories, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def move(self, request, pk=None):
        """
        移动分类位置
        ---
        请求参数:
            - target_id: 目标分类ID
            - position: 移动位置(before/after/inside)
        """
        category = self.get_object()
        serializer = self.get_serializer(category, data=request.data)
        serializer.is_valid(raise_exception=True)

        target = serializer.validated_data["target"]
        position = serializer.validated_data["position"]

        try:
            with transaction.atomic():
                if position == "inside":
                    # 移动到目标分类内部
                    max_order = (
                        NewsCategory.objects.filter(parent=target).aggregate(Max("sort_order"))["sort_order__max"] or 0
                    )

                    category.parent = target
                    category.sort_order = max_order + 1
                    category.save()

                else:
                    # 移动到目标分类前面或后面
                    if position == "before":
                        new_order = target.sort_order
                        # 更新后面的排序
                        NewsCategory.objects.filter(parent=target.parent, sort_order__gte=new_order).update(
                            sort_order=F("sort_order") + 1
                        )
                    else:  # after
                        new_order = target.sort_order + 1
                        # 更新后面的排序
                        NewsCategory.objects.filter(parent=target.parent, sort_order__gt=target.sort_order).update(
                            sort_order=F("sort_order") + 1
                        )

                    category.parent = target.parent
                    category.sort_order = new_order
                    category.save()

            return Response({"message": "移动成功"})

        except Exception as e:
            return Response({"message": "移动失败", "errors": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def sort(self, request, pk=None):
        """
        更新分类排序
        ---
        请求参数:
            - sort_order: 新的排序值
        """
        category = self.get_object()
        new_order = request.data.get("sort_order")

        if not isinstance(new_order, int):
            return Response({"message": "排序值必须是整数"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                if new_order > category.sort_order:
                    # 向后移动
                    NewsCategory.objects.filter(
                        parent=category.parent, sort_order__gt=category.sort_order, sort_order__lte=new_order
                    ).update(sort_order=F("sort_order") - 1)
                else:
                    # 向前移动
                    NewsCategory.objects.filter(
                        parent=category.parent, sort_order__gte=new_order, sort_order__lt=category.sort_order
                    ).update(sort_order=F("sort_order") + 1)

                category.sort_order = new_order
                category.save()

            return Response({"message": "排序更新成功"})

        except Exception as e:
            return Response({"message": "排序更新失败", "errors": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """获取分类统计信息"""
        category = self.get_object()
        articles = category.articles.all()
        
        total_articles = articles.count()
        published_articles = articles.filter(status='published').count()
        
        return Response({
            'total_articles': total_articles,
            'published_articles': published_articles
        })


class NewsArticleViewSet(viewsets.ModelViewSet):
    """新闻文章视图集."""

    queryset = NewsArticle.objects.all()
    serializer_class = NewsArticleSerializer
    permission_classes = [ActionBasedPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'content', 'summary', 'source', 'author']
    ordering_fields = ['publish_time', 'created_at', 'sentiment_score']
    ordering = ['-publish_time']
    parser_classes = [JSONParser, MultiPartParser]

    def get_queryset(self):
        """获取文章列表，支持多种过滤."""
        queryset = super().get_queryset()

        # 过滤分类
        category_id = self.request.query_params.get('category_id')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # 过滤状态
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # 过滤时间范围
        start_time = self.request.query_params.get('start_time')
        end_time = self.request.query_params.get('end_time')
        if start_time:
            queryset = queryset.filter(publish_time__gte=start_time)
        if end_time:
            queryset = queryset.filter(publish_time__lte=end_time)

        # 过滤标签
        tag = self.request.query_params.get('tag')
        if tag:
            queryset = queryset.filter(tags__contains=[tag])

        # 普通用户只能看到已发布的文章,且仅在list操作时过滤
        user = self.request.user
        if not (user and user.is_authenticated and user.user_type in ['admin', 'staff']) and self.action == 'list':
            queryset = queryset.filter(status=NewsArticle.Status.PUBLISHED)

        return queryset

    def get_serializer_class(self):
        """根据不同的动作返回不同的序列化器."""
        if self.action == 'create':
            return NewsArticleCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return NewsArticleUpdateSerializer
        elif self.action == 'review':
            return NewsArticleReviewSerializer
        return self.serializer_class

    def get_permissions(self):
        """根据不同的动作返回不同的权限类.
        
        - list/retrieve: 所有人可访问（已发布的文章）
        - create/update/delete: 需要管理员或工作人员权限
        - review: 只有管理员可以审核
        - import/export: 需要管理员或工作人员权限
        """
        self.permission_classes = [ActionBasedPermission]
        self.action_permissions = {
            permissions.IsAdminUser: [
                'create',
                'update',
                'partial_update',
                'destroy',
                'submit_review',
                'import_articles',
                'export_articles',
                'bulk_update',
                'bulk_delete'
            ],
            permissions.AllowAny: ['list', 'retrieve']
        }
        return super().get_permissions()

    @action(detail=True, methods=['post'])
    def submit_review(self, request, pk=None):
        """提交审核."""
        instance = self.get_object()
        serializer = NewsArticleAuditSerializer(
            instance, data=request.data, context={'request': request, 'action': 'submit'}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def assign_reviewer(self, request, pk=None):
        """分配审核人."""
        instance = self.get_object()
        serializer = NewsArticleAuditSerializer(
            instance, data=request.data, context={'request': request, 'action': 'assign'}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """审核通过."""
        instance = self.get_object()
        serializer = NewsArticleAuditSerializer(
            instance, data=request.data, context={'request': request, 'action': 'approve'}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """审核拒绝."""
        instance = self.get_object()
        serializer = NewsArticleAuditSerializer(
            instance, data=request.data, context={'request': request, 'action': 'reject'}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def withdraw(self, request, pk=None):
        """撤回审核."""
        instance = self.get_object()
        serializer = NewsArticleAuditSerializer(
            instance, data=request.data, context={'request': request, 'action': 'withdraw'}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def audit_logs(self, request, pk=None):
        """获取审核日志."""
        instance = self.get_object()
        logs = instance.audit_logs.all()
        serializer = NewsAuditLogSerializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        """审核文章."""
        article = self.get_object()
        serializer = self.get_serializer(article, data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
            with transaction.atomic():
                article = serializer.save()

            return Response({'message': '审核完成', 'data': NewsArticleSerializer(article).data})
        except Exception as e:
            return Response({'message': '审核失败', 'errors': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """归档文章."""
        article = self.get_object()

        if article.status != NewsArticle.Status.PUBLISHED:
            return Response({'message': '只有已发布的文章可以归档'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                article.status = NewsArticle.Status.ARCHIVED
                article.save()

            return Response({'message': '文章已归档', 'data': NewsArticleSerializer(article).data})
        except Exception as e:
            return Response({'message': '归档失败', 'errors': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        """创建文章时记录当前时间."""
        if not serializer.validated_data.get('publish_time'):
            serializer.validated_data['publish_time'] = timezone.now()
        serializer.save()

    def perform_update(self, serializer):
        """更新文章时进行额外处理."""
        # 如果只更新分类，直接保存
        if len(serializer.validated_data) == 1 and 'category' in serializer.validated_data:
            serializer.save()
            return

        # 如果状态从草稿改为待审核，清空审核相关信息
        if (
            serializer.instance.status == NewsArticle.Status.DRAFT
            and serializer.validated_data.get('status') == NewsArticle.Status.PENDING
        ):
            serializer.validated_data.update({
                'reviewer': None,
                'review_time': None,
                'review_comment': ''
            })

        serializer.save()

    @action(detail=False, methods=['post'])
    def import_articles(self, request):
        """导入文章.
        
        请求参数:
            - file: 文件对象（Excel或CSV）
        """
        file = request.FILES.get('file')
        if not file:
            return Response({'message': '请选择要导入的文件'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = NewsImportExportHelper.import_data(file)
            serializer = ImportResultSerializer(result)

            return Response({'message': '导入完成', 'data': serializer.data})

        except Exception as e:
            return Response({'message': '导入失败', 'errors': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def export_articles(self, request):
        """导出文章.
        
        请求参数:
            - format: 导出格式(excel/csv)，默认excel
            - category_id: 分类ID（可选）
            - status: 状态（可选）
            - start_time: 开始时间（可选）
            - end_time: 结束时间（可选）
        """
        try:
            # 获取过滤后的查询集
            queryset = self.filter_queryset(self.get_queryset())

            # 获取导出格式
            export_format = request.query_params.get('format', 'excel')
            if export_format not in ['excel', 'csv']:
                return Response({'message': '不支持的导出格式'}, status=status.HTTP_400_BAD_REQUEST)

            # 导出数据
            file_content, content_type, file_ext = NewsImportExportHelper.export_data(queryset, export_format)

            # 生成文件名
            filename = f'news_articles_{timezone.now().strftime("%Y%m%d_%H%M%S")}{file_ext}'

            # 返回文件
            response = HttpResponse(file_content, content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

        except Exception as e:
            return Response({'message': '导出失败', 'errors': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['put'], url_path='bulk-update')
    def bulk_update(self, request):
        """批量更新文章."""
        items = request.data.get('items', [])
        if not items:
            return Response({"message": "没有提供要更新的数据"}, status=status.HTTP_400_BAD_REQUEST)

        updated_count = 0
        errors = []

        for item in items:
            try:
                article_id = item.pop('id')
                article = NewsArticle.objects.get(id=article_id)
                serializer = self.get_serializer(article, data=item, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                updated_count += 1
            except Exception as e:
                errors.append(f"更新文章 {article_id} 失败: {str(e)}")

        return Response({
            "message": f"成功更新 {updated_count} 篇文章",
            "errors": errors
        })

    @action(detail=False, methods=['post'], url_path='bulk-delete')
    def bulk_delete(self, request):
        """批量删除文章."""
        ids = request.data.get('ids', [])
        if not ids:
            return Response({"message": "没有提供要删除的文章ID"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            articles = NewsArticle.objects.filter(id__in=ids)
            count = articles.count()
            articles.delete()
            return Response({"message": f"成功删除 {count} 篇文章"}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"message": f"删除失败: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
