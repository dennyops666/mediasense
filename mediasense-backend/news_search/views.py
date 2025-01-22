from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import MultiMatch, Bool
from django.conf import settings
from elasticsearch import Elasticsearch
import json

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
from news.models import NewsArticle
from .documents import NewsArticleDocument

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

    def get_client(self):
        """获取Elasticsearch客户端"""
        return Elasticsearch(hosts=settings.ELASTICSEARCH_HOSTS)

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
        """搜索新闻"""
        query = request.query_params.get('query', '')
        page = int(request.query_params.get('page', 1))
        size = int(request.query_params.get('size', 10))
        sort = request.query_params.get('sort', '-publish_time')
        highlight = request.query_params.get('highlight', 'false').lower() == 'true'

        # 创建搜索对象
        s = Search(using=self.get_client(), index='news_articles')

        # 构建查询
        if query:
            s = s.query(MultiMatch(
                query=query,
                fields=['title^2', 'content', 'summary']
            ))

        # 添加过滤
        if 'status' in request.query_params:
            s = s.filter('term', status=request.query_params['status'])

        if 'time_range' in request.query_params:
            try:
                time_range = json.loads(request.query_params['time_range'])
                if isinstance(time_range, dict):
                    range_filter = {}
                    if 'start' in time_range:
                        range_filter['gte'] = time_range['start']
                    if 'end' in time_range:
                        range_filter['lte'] = time_range['end']
                    if range_filter:
                        s = s.filter('range', publish_time=range_filter)
            except json.JSONDecodeError:
                logger.warning("Invalid time_range format")

        # 添加排序
        if sort == 'relevance':
            s = s.sort('_score')
        else:
            s = s.sort(sort)

        # 添加分页
        start = (page - 1) * size
        s = s[start:start + size]

        # 添加高亮
        if highlight:
            s = s.highlight_options(
                pre_tags=['<em>'],
                post_tags=['</em>'],
                number_of_fragments=0
            )
            s = s.highlight('title', 'content')

        # 执行搜索
        response = s.execute()

        # 处理结果
        results = []
        for hit in response:
            result = {
                'id': hit.meta.id,
                'title': hit.title,
                'content': hit.content,
                'summary': hit.summary,
                'source': hit.source,
                'author': hit.author,
                'url': hit.url,
                'status': hit.status,
                'publish_time': hit.publish_time,
                'score': hit.meta.score
            }

            # 添加高亮结果
            if highlight and hasattr(hit.meta, 'highlight'):
                if hasattr(hit.meta.highlight, 'title'):
                    result['title_highlight'] = hit.meta.highlight.title[0]
                if hasattr(hit.meta.highlight, 'content'):
                    result['content_highlight'] = hit.meta.highlight.content[0]

            results.append(result)

        return Response({
            'total': response.hits.total.value,
            'page': page,
            'size': size,
            'results': results
        })

    @action(detail=False, methods=["get"])
    def suggest(self, request):
        """搜索建议"""
        prefix = request.query_params.get('prefix', '')
        size = int(request.query_params.get('size', 5))

        if not prefix:
            return Response([])

        # 创建搜索对象
        s = Search(using=self.get_client(), index='news_articles')
        
        # 使用标题字段的前缀匹配查询
        s = s.query('match_phrase_prefix',
            title={
                'query': prefix,
                'max_expansions': 10,
                'slop': 2
            }
        )
        s = s[:size]

        # 执行查询
        response = s.execute()

        # 处理结果
        suggestions = []
        for hit in response:
            suggestions.append({
                'title': hit.title,
                'score': hit.meta.score
            })

        return Response(suggestions)

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
