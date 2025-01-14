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
    CACHE_VERSION_KEY = CACHE_PREFIX + "version"
    CACHE_STATS_KEY = CACHE_PREFIX + "stats"
    CACHE_TIMEOUT = 60 * 5  # 5分钟缓存

    def __init__(self):
        """初始化ES客户端"""
        self.client = Elasticsearch(
            hosts=settings.ELASTICSEARCH_HOSTS,
            basic_auth=(settings.ELASTICSEARCH_USERNAME, settings.ELASTICSEARCH_PASSWORD),
        )
        self.search = Search(using=self.client, index=NewsArticleDocument._index._name)
        self._ensure_cache_version()

    def _ensure_cache_version(self):
        """确保缓存版本存在"""
        if not cache.get(self.CACHE_VERSION_KEY):
            cache.set(self.CACHE_VERSION_KEY, datetime.now().timestamp())

    def _get_cache_key(self, query, filters=None, page=1, size=10):
        """生成缓存键"""
        # 将查询参数序列化为确定性的字符串
        params = {"query": query, "filters": filters, "page": page, "size": size}
        params_str = json.dumps(params, sort_keys=True)

        # 使用MD5生成固定长度的键
        hash_key = hashlib.md5(params_str.encode()).hexdigest()
        version = cache.get(self.CACHE_VERSION_KEY)

        return f"{self.CACHE_PREFIX}result:{version}:{hash_key}"

    def _update_cache_stats(self, cache_hit=True):
        """更新缓存统计信息"""
        stats_key = self.CACHE_STATS_KEY
        stats = cache.get(stats_key) or {"hits": 0, "misses": 0, "total_requests": 0}

        stats["total_requests"] += 1
        if cache_hit:
            stats["hits"] += 1
        else:
            stats["misses"] += 1

        cache.set(stats_key, stats)

    def invalidate_cache(self):
        """使所有搜索缓存失效"""
        cache.incr(self.CACHE_VERSION_KEY)

    def get_cache_stats(self):
        """获取缓存统计信息"""
        stats = cache.get(self.CACHE_STATS_KEY) or {"hits": 0, "misses": 0, "total_requests": 0}

        if stats["total_requests"] > 0:
            stats["hit_rate"] = stats["hits"] / stats["total_requests"]
        else:
            stats["hit_rate"] = 0

        return stats

    def warm_cache(self, queries):
        """
        预热缓存
        :param queries: 要预热的查询列表，每个查询是一个字典，包含query和filters
        """
        for query_params in queries:
            self.search_articles(query=query_params["query"], filters=query_params.get("filters"), use_cache=True)

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
            Q("multi_match", query=query, fields=["title^3", "summary^2", "content", "tags^2"])
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
                "summary": hit.summary,
                "url": hit.url,
                "publish_time": hit.publish_time,
                "score": hit.meta.score,
                "source": hit.source,
                "author": hit.author,
                "tags": hit.tags,
                "sentiment_score": hit.sentiment_score,
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
            # 对于热门查询，延长缓存时间
            if response.hits.total.value > 100:
                cache_timeout = self.CACHE_TIMEOUT * 2
            else:
                cache_timeout = self.CACHE_TIMEOUT

            cache.set(cache_key, search_result, cache_timeout)

        return search_result

    def suggest_titles(self, prefix, size=5):
        """
        标题搜索建议
        :param prefix: 标题前缀
        :param size: 建议数量
        :return: 建议列表
        """
        suggest_query = self.search.suggest(
            "title_suggest", prefix, completion={"field": "title_suggest", "size": size, "skip_duplicates": True}
        )

        response = suggest_query.execute()
        suggestions = []

        if "title_suggest" in response.suggest:
            for item in response.suggest.title_suggest[0].options:
                suggestions.append({"id": item._id, "title": item._source.title, "score": item._score})

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
