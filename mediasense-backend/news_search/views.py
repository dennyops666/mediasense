from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import MultiMatch, Bool
from django.conf import settings
from elasticsearch import Elasticsearch
import json
import logging

from .serializers import (
    HotArticleQuerySerializer,
    HotArticleSerializer,
    SearchQuerySerializer,
    SearchResponseSerializer,
    SuggestQuerySerializer,
    SuggestResultSerializer,
    SearchSuggestionSerializer,
)
from .services import NewsSearchService
from news.models import NewsArticle
from .documents import NewsArticleDocument
from .models import SearchSuggestion, SearchHistory

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
        try:
            query = request.query_params.get("q", "")
            highlight = request.query_params.get("highlight", "false").lower() == "true"
            exact_match = request.query_params.get("exact_match", "false").lower() == "true"
            page = int(request.query_params.get("page", 1))
            page_size = int(request.query_params.get("page_size", 10))
            
            # 处理字段过滤
            raw_fields = request.query_params.getlist("fields")
            logger.info(f"Raw fields: {raw_fields}, type: {type(raw_fields)}")
            if raw_fields:
                fields = []
                for field in raw_fields:
                    if isinstance(field, str):
                        fields.extend(f.strip() for f in field.split(',') if f.strip())
                    else:
                        fields.append(str(field))
                logger.info(f"Processed fields: {fields}, type: {type(fields)}")
                
                # 验证字段是否有效
                valid_fields = []
                for field in fields:
                    if field == '*':
                        valid_fields = ['*']
                        break
                    if field in ["title", "content", "summary", "source", "author", "source_url", "status", "publish_time", "category"]:
                        valid_fields.append(field)
                fields = valid_fields
                logger.info(f"Valid fields: {fields}, type: {type(fields)}")
            else:
                fields = None
                logger.info(f"No fields specified")
            
            # 记录搜索历史
            if query and request.user.is_authenticated:
                SearchHistory.objects.create(
                    user=request.user,
                    keyword=query
                )
            
            # 创建ES客户端
            es_client = Elasticsearch(settings.ELASTICSEARCH_HOSTS)
            index_name = f"{settings.ELASTICSEARCH_INDEX_PREFIX}news_articles"
            
            # 构建搜索查询
            search_body = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "match_all": {}
                            }
                        ]
                    }
                } if not query else {
                    "bool": {
                        "must": [
                            {
                                "multi_match": {
                                    "query": query,
                                    "fields": ["title^2", "content", "summary"],
                                    "type": "phrase" if exact_match else "best_fields"
                                }
                            }
                        ]
                    }
                },
                "from": (page - 1) * page_size,
                "size": page_size,
                "sort": [{"_score": "desc"}]
            }

            # 添加字段过滤
            if fields:
                if '*' in fields:
                    search_body["_source"] = True
                elif fields:
                    search_body["_source"] = fields
                else:
                    search_body["_source"] = False
            
            # 添加高亮配置
            if highlight:
                pre_tags = request.query_params.get("highlight_pre_tags", "<em>")
                post_tags = request.query_params.get("highlight_post_tags", "</em>")
                search_body["highlight"] = {
                    "fields": {
                        "title": {
                            "number_of_fragments": 0,
                            "pre_tags": [pre_tags],
                            "post_tags": [post_tags]
                        },
                        "content": {
                            "number_of_fragments": 3,
                            "fragment_size": 150,
                            "pre_tags": [pre_tags],
                            "post_tags": [post_tags]
                        },
                        "summary": {
                            "number_of_fragments": 1,
                            "fragment_size": 150,
                            "pre_tags": [pre_tags],
                            "post_tags": [post_tags]
                        }
                    }
                }
            
            # 执行搜索
            response = es_client.search(index=index_name, body=search_body)
            
            # 处理搜索结果
            hits = response["hits"]["hits"]
            total = response["hits"]["total"]["value"]
            
            results = []
            for hit in hits:
                result = {}
                
                # 处理字段过滤
                if fields:
                    if '*' in fields:
                        result = hit.get("_source", {}).copy()
                        result["id"] = hit["_id"]
                        result["score"] = hit["_score"]
                    elif fields:
                        result = {}
                        source = hit.get("_source", {})
                        for field in fields:
                            result[field] = source.get(field)
                        result["id"] = hit["_id"]
                        result["score"] = hit["_score"]
                    else:
                        result = {}
                else:
                    result = hit.get("_source", {}).copy()
                    result["id"] = hit["_id"]
                    result["score"] = hit["_score"]
                
                # 如果没有有效字段，返回空字典
                if fields is not None and not fields:
                    result = {}
                
                # 添加高亮结果
                if highlight and "highlight" in hit:
                    for field, highlights in hit["highlight"].items():
                        if not fields or field in fields or '*' in fields:
                            result[field] = highlights[0]
                
                results.append(result)
            
            return Response({
                "total": total,
                "count": total,
                "results": results,
                "page": page,
                "page_size": page_size
            })
            
        except Exception as e:
            logger.error(f"搜索失败: {str(e)}", exc_info=True)
            return Response(
                {"message": "搜索失败", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["get"])
    def suggest(self, request):
        """获取搜索建议"""
        prefix = request.query_params.get("prefix") or request.query_params.get("q", "")
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 10))
        
        suggestions = SearchSuggestion.objects.filter(
            keyword__istartswith=prefix
        ).order_by("-search_count")
        
        start = (page - 1) * page_size
        end = start + page_size
        paginated_suggestions = suggestions[start:end]
        
        serializer = SearchSuggestionSerializer(paginated_suggestions, many=True)
        data = serializer.data
        suggestions_list = [item["keyword"] for item in data]
        
        return Response({
            "suggestions": suggestions_list,
            "count": suggestions.count()
        })

    @action(detail=False, methods=["get"])
    def hot(self, request):
        """获取热门搜索"""
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 10))
        min_count = request.query_params.get("min_count")
        
        filters = {
            'is_hot': True
        }
        
        if min_count:
            filters['search_count__gte'] = int(min_count)
        
        hot_searches = SearchSuggestion.objects.filter(
            **filters
        ).order_by("-search_count")
        
        start = (page - 1) * page_size
        end = start + page_size
        paginated_searches = hot_searches[start:end]
        
        serializer = SearchSuggestionSerializer(paginated_searches, many=True)
        return Response({
            "hot_searches": serializer.data,
            "count": hot_searches.count()
        })

    @action(detail=False, methods=["get"])
    def history(self, request):
        """获取用户搜索历史"""
        if not request.user.is_authenticated:
            return Response({"message": "请先登录"}, status=status.HTTP_401_UNAUTHORIZED)
            
        history = SearchHistory.objects.filter(
            user=request.user
        ).order_by("-created_at")[:50]
        
        return Response({
            "history": [
                {
                    "keyword": h.keyword,
                    "created_at": h.created_at
                } for h in history
            ],
            "count": len(history)
        })

    @action(detail=False, methods=["post"])
    def clear_history(self, request):
        """清空用户搜索历史"""
        if not request.user.is_authenticated:
            return Response({"message": "请先登录"}, status=status.HTTP_401_UNAUTHORIZED)
            
        SearchHistory.objects.filter(user=request.user).delete()
        return Response({"message": "搜索历史已清空"})
