import hashlib
import json
from datetime import datetime, timedelta

from django.conf import settings
from django.core.cache import cache
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Q, Search

from .documents import NewsArticleDocument


class NewsSearchService:
    """新闻搜索服务"""

    CACHE_PREFIX = "news_search:"
    CACHE_TIMEOUT = 60 * 5  # 5分钟缓存

    def __init__(self):
        """初始化搜索服务"""
        self.client = Elasticsearch(hosts=settings.ELASTICSEARCH_HOSTS)
        self.search = Search(using=self.client, index=NewsArticleDocument._index._name)
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "total": 0
        }

    def _get_cache_key(self, query, filters=None, page=1, size=10):
        """生成缓存键"""
        key_parts = [query, str(page), str(size)]
        if filters:
            key_parts.append(json.dumps(filters, sort_keys=True))
        return f"{self.CACHE_PREFIX}{'_'.join(key_parts)}"

    def _update_cache_stats(self, cache_hit=True):
        """更新缓存统计"""
        if cache_hit:
            self.cache_stats["hits"] += 1
        else:
            self.cache_stats["misses"] += 1
        self.cache_stats["total"] += 1

    def get_cache_stats(self):
        """获取缓存统计信息"""
        return self.cache_stats

    def search_articles(self, query, filters=None, page=1, size=10, use_cache=True):
        """
        搜索文章
        :param query: 搜索关键词
        :param filters: 过滤条件，如:
            {
                'category': 1,
                'status': 'published',
                'source': '新华网',
                'author': '张三',
                'time_range': {
                    'start': '2024-01-01',
                    'end': '2024-01-31'
                },
                'sentiment': {
                    'min': -1,
                    'max': 1
                },
                'tags': ['科技', '互联网']
            }
        :param page: 页码
        :param size: 每页大小
        :param use_cache: 是否使用缓存
        :return: 搜索结果和总数
        """
        # 尝试从缓存获取
        cache_key = self._get_cache_key(query, filters, page, size)
        if use_cache:
            cached_result = cache.get(cache_key)
            if cached_result:
                self._update_cache_stats(cache_hit=True)
                return cached_result

        self._update_cache_stats(cache_hit=False)

        # 构建搜索查询
        search_query = self.search.query(
            Q("multi_match", query=query, fields=["title^3", "content", "summary"])
        )

        # 添加过滤条件
        if filters:
            # 基础字段过滤
            for field in ["category", "status", "source", "author"]:
                if field in filters:
                    search_query = search_query.filter("term", **{field: filters[field]})

            # 时间范围过滤
            if "time_range" in filters:
                time_range = filters["time_range"]
                range_params = {}
                if "start" in time_range:
                    range_params["gte"] = time_range["start"]
                if "end" in time_range:
                    range_params["lte"] = time_range["end"]
                if range_params:
                    search_query = search_query.filter("range", publish_time=range_params)

            # 情感得分过滤
            if "sentiment" in filters:
                sentiment = filters["sentiment"]
                sentiment_params = {}
                if "min" in sentiment:
                    sentiment_params["gte"] = sentiment["min"]
                if "max" in sentiment:
                    sentiment_params["lte"] = sentiment["max"]
                if sentiment_params:
                    search_query = search_query.filter("range", sentiment_score=sentiment_params)

            # 标签过滤
            if "tags" in filters and filters["tags"]:
                search_query = search_query.filter("terms", tags=filters["tags"])

            # 排序
            if "sort" in filters:
                sort_field = filters["sort"]
                if sort_field.startswith("-"):
                    search_query = search_query.sort({sort_field[1:]: {"order": "desc"}})
                else:
                    search_query = search_query.sort({sort_field: {"order": "asc"}})
            else:
                # 默认按相关性和时间排序
                search_query = search_query.sort("_score", {"publish_time": {"order": "desc"}})

        # 分页
        start = (page - 1) * size
        search_query = search_query[start : start + size]

        # 高亮设置
        search_query = search_query.highlight_options(pre_tags=["<em>"], post_tags=["</em>"], number_of_fragments=3)
        search_query = search_query.highlight("title", "summary", "content")

        # 执行搜索
        response = search_query.execute()

        # 处理结果
        results = []
        for hit in response:
            result = {
                "id": hit.meta.id,
                "title": hit.title,
                "summary": hit.summary if hasattr(hit, 'summary') else '',
                "url": hit.url if hasattr(hit, 'url') else '',
                "publish_time": hit.publish_time if hasattr(hit, 'publish_time') else None,
                "score": hit.meta.score,
                "source": hit.source if hasattr(hit, 'source') else '',
                "author": hit.author if hasattr(hit, 'author') else '',
                "tags": hit.tags if hasattr(hit, 'tags') else [],
                "sentiment_score": hit.sentiment_score if hasattr(hit, 'sentiment_score') else 0.0,
                "status": hit.status if hasattr(hit, 'status') else ''
            }

            # 添加高亮内容
            if hasattr(hit.meta, "highlight"):
                highlight = hit.meta.highlight
                if hasattr(highlight, "title"):
                    result["title_highlight"] = highlight.title[0]
                if hasattr(highlight, "summary"):
                    result["summary_highlight"] = highlight.summary[0]
                if hasattr(highlight, "content"):
                    result["content_highlight"] = highlight.content[0]

            results.append(result)

        search_result = {"total": response.hits.total.value, "results": results}

        # 缓存结果
        if use_cache:
            cache.set(cache_key, search_result, 60 * 5)  # 5分钟缓存

        return search_result

    def suggest_titles(self, prefix, size=5):
        """
        获取标题建议
        :param prefix: 标题前缀
        :param size: 建议数量
        :return: 建议列表
        """
        # 构建建议查询
        suggest_query = {
            "suggest": {
                "title_suggest": {
                    "prefix": prefix,
                    "completion": {
                        "field": "title_suggest",
                        "size": size,
                        "skip_duplicates": True
                    }
                }
            },
            "_source": ["title"]
        }

        # 执行查询
        response = self.client.search(
            index=NewsArticleDocument._index._name,
            body=suggest_query
        )

        # 处理结果
        suggestions = []
        if "suggest" in response and "title_suggest" in response["suggest"]:
            for suggestion in response["suggest"]["title_suggest"][0]["options"]:
                suggestions.append({
                    "id": suggestion["_id"],
                    "title": suggestion["_source"]["title"],
                    "score": suggestion["_score"]
                })

        return suggestions

    def hot_articles(self, days=7, size=10):
        """
        获取热点新闻
        :param days: 最近几天
        :param size: 返回数量
        :return: 热点新闻列表
        """
        from datetime import datetime, timedelta

        # 获取缓存
        cache_key = f"{self.CACHE_PREFIX}hot_articles:{days}:{size}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

        # 构建查询
        start_time = datetime.now() - timedelta(days=days)
        hot_query = self.search.filter("range", publish_time={"gte": start_time}).sort(
            "-sentiment_score", "-publish_time"
        )[:size]

        # 执行查询
        response = hot_query.execute()

        # 处理结果
        results = []
        for hit in response:
            results.append(
                {
                    "id": hit.meta.id,
                    "title": hit.title,
                    "summary": hit.summary,
                    "url": hit.url,
                    "publish_time": hit.publish_time,
                    "sentiment_score": hit.sentiment_score,
                }
            )

        # 缓存结果
        cache.set(cache_key, results, 60 * 60)  # 1小时缓存

        return results
