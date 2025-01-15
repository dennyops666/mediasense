from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .serializers import (
    HotArticleQuerySerializer,
    HotArticleSerializer,
    SearchQuerySerializer,
    SearchResponseSerializer,
    SuggestQuerySerializer,
    SuggestResultSerializer,
)
from .services import NewsSearchService
import logging

logger = logging.getLogger(__name__)


class NewsSearchViewSet(viewsets.ViewSet):
    """新闻搜索视图集"""

    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.search_service = NewsSearchService()

    def get_permissions(self):
        """根据不同的操作设置权限"""
        if self.action in ["cache_stats", "invalidate_cache", "warm_cache"]:
            return [IsAdminUser()]
        return super().get_permissions()

    @action(detail=False, methods=["get"])
    def cache_stats(self, request):
        """
        获取缓存统计信息
        仅管理员可访问
        """
        stats = self.search_service.get_cache_stats()
        return Response(stats)

    @action(detail=False, methods=["post"])
    def invalidate_cache(self, request):
        """
        使所有搜索缓存失效
        仅管理员可访问
        """
        self.search_service.invalidate_cache()
        return Response({"message": "缓存已清空"})

    @action(detail=False, methods=["post"])
    def warm_cache(self, request):
        """
        预热缓存
        仅管理员可访问
        ---
        请求体:
        {
            "queries": [
                {
                    "query": "搜索关键词",
                    "filters": {
                        "category": 1,
                        "status": "published"
                    }
                },
                ...
            ]
        }
        """
        queries = request.data.get("queries", [])
        if not queries:
            return Response({"message": "请提供要预热的查询列表"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            self.search_service.warm_cache(queries)
            return Response({"message": "缓存预热完成"})
        except Exception as e:
            return Response({"message": "缓存预热失败", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["get"])
    def search(self, request):
        """
        搜索文章
        ---
        请求参数:
            - query: 搜索关键词
            - category: 分类ID（可选）
            - status: 文章状态（可选）
            - page: 页码，默认1
            - size: 每页大小，默认10
        """
        # 验证请求参数
        query_serializer = SearchQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        # 构建过滤条件
        filters = {}
        if "category" in query_serializer.validated_data:
            filters["category"] = query_serializer.validated_data["category"]
        if "status" in query_serializer.validated_data:
            filters["status"] = query_serializer.validated_data["status"]
        if "time_range" in query_serializer.validated_data:
            filters["time_range"] = query_serializer.validated_data["time_range"]
        if "sentiment" in query_serializer.validated_data:
            filters["sentiment"] = query_serializer.validated_data["sentiment"]
        if "tags" in query_serializer.validated_data:
            filters["tags"] = query_serializer.validated_data["tags"]
        if "sort" in query_serializer.validated_data:
            filters["sort"] = query_serializer.validated_data["sort"]

        try:
            # 执行搜索
            result = self.search_service.search_articles(
                query=query_serializer.validated_data["query"],
                filters=filters,
                page=query_serializer.validated_data.get("page", 1),
                size=query_serializer.validated_data.get("size", 10),
            )

            # 序列化结果
            response_serializer = SearchResponseSerializer(result)
            return Response(response_serializer.data)

        except Exception as e:
            logger.error(f"搜索失败: {str(e)}", exc_info=True)
            return Response(
                {"message": "搜索失败", "errors": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["get"])
    def suggest(self, request):
        """
        获取搜索建议
        ---
        请求参数:
            - prefix: 标题前缀
            - size: 建议数量，默认5
        """
        # 验证请求参数
        query_serializer = SuggestQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        try:
            # 获取建议
            suggestions = self.search_service.suggest_titles(
                prefix=query_serializer.validated_data["prefix"],
                size=query_serializer.validated_data.get("size", 5)
            )

            # 序列化结果
            response_serializer = SuggestResultSerializer(suggestions, many=True)
            return Response(response_serializer.data)

        except Exception as e:
            logger.error(f"获取搜索建议失败: {str(e)}", exc_info=True)
            return Response(
                {"message": "获取搜索建议失败", "errors": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["get"])
    def hot(self, request):
        """
        获取热点新闻
        ---
        请求参数:
            - days: 最近几天，默认7天
            - size: 返回数量，默认10
        """
        # 验证请求参数
        query_serializer = HotArticleQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        try:
            # 获取热点新闻
            hot_articles = self.search_service.hot_articles(
                days=query_serializer.validated_data["days"], size=query_serializer.validated_data["size"]
            )

            # 序列化结果
            response_serializer = HotArticleSerializer(hot_articles, many=True)
            return Response(response_serializer.data)

        except Exception as e:
            return Response(
                {"message": "获取热点新闻失败", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
