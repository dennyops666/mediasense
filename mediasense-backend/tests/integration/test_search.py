import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch, Mock, MagicMock
from tests.factories import UserFactory, NewsArticleFactory as NewsFactory, NewsCategoryFactory
from news.models import NewsArticle
from django.utils import timezone
import json
from django.test import TransactionTestCase, override_settings
from asgiref.sync import sync_to_async
import logging
from elasticsearch_dsl.connections import connections
from django.conf import settings
import elasticsearch
import time
from news_search.models import SearchSuggestion
from news_search.documents import NewsArticleDocument
from django.core.cache import cache

pytestmark = [
    pytest.mark.django_db(transaction=True),
    pytest.mark.asyncio
]

logger = logging.getLogger(__name__)

@override_settings(
    ELASTICSEARCH_INDEX_PREFIX='test_',
    ELASTICSEARCH_HOSTS=['http://localhost:9200']
)
class TestSearchIntegration(TransactionTestCase):
    """TC-INT-SEARCH-001: 搜索服务集成测试"""

    def setUp(self):
        """设置测试环境"""
        super().setUp()
        self.user = UserFactory(is_staff=True, is_superuser=True)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # 确保Elasticsearch连接已建立
        self.es_client = elasticsearch.Elasticsearch(hosts=settings.ELASTICSEARCH_HOSTS)
        connections.create_connection(hosts=settings.ELASTICSEARCH_HOSTS)
        
        # 创建测试索引
        self.index_name = "test_news_articles"
        if not self.es_client.indices.exists(index=self.index_name):
            self.es_client.indices.create(
                index=self.index_name,
                body={
                    "mappings": {
                        "properties": {
                            "title": {
                                "type": "text",
                                "fields": {
                                    "raw": {"type": "keyword"},
                                    "suggest": {"type": "completion"}
                                }
                            },
                            "content": {"type": "text"},
                            "summary": {"type": "text"},
                            "source": {"type": "keyword"},
                            "author": {"type": "keyword"},
                            "status": {"type": "keyword"},
                            "publish_time": {"type": "date"},
                            "created_at": {"type": "date"},
                            "updated_at": {"type": "date"},
                            "category": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer"},
                                    "name": {"type": "keyword"}
                                }
                            }
                        }
                    },
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0,
                        "analysis": {
                            "analyzer": {
                                "html_strip": {
                                    "tokenizer": "standard",
                                    "filter": ["lowercase", "stop", "snowball"],
                                    "char_filter": ["html_strip"]
                                }
                            }
                        }
                    }
                }
            )

    def tearDown(self):
        """清理测试环境"""
        super().tearDown()
        # 删除测试索引
        if self.es_client.indices.exists(index=self.index_name):
            self.es_client.indices.delete(index=self.index_name)

    async def index_article(self, article):
        """索引文章到Elasticsearch"""
        doc = NewsArticleDocument()
        doc.meta.id = article.id
        doc.title = article.title
        doc.content = article.content
        doc.status = article.status
        doc.publish_time = article.publish_time
        doc.created_at = article.created_at
        doc.updated_at = article.updated_at
        if article.category:
            doc.category = {
                'id': article.category.id,
                'name': article.category.name
            }
        await sync_to_async(doc.save)()

    async def test_news_search(self):
        """测试新闻搜索功能"""
        # 创建测试分类
        category = await NewsCategoryFactory.acreate()
        
        # 创建测试文章
        articles = []
        for i in range(5):
            article = await NewsFactory.acreate(
                title=f"测试文章{i}",
                content=f"这是测试文章{i}的内容",
                category=category,
                status="published",
                publish_time=timezone.now()
            )
            articles.append(article)
            # 索引文章
            await self.index_article(article)

        # 等待索引刷新
        await sync_to_async(time.sleep)(1)
        await sync_to_async(self.es_client.indices.refresh)(index=self.index_name)

        # 关键词搜索
        response = await sync_to_async(self.client.get)(
            reverse("api:news_search:news-search-search"),
            {"q": "测试文章", "highlight": "true"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 5
        # 验证所有结果都包含高亮标记
        for result in data["results"]:
            assert "<em>" in result["title"]
            assert "</em>" in result["title"]

        # 高级搜索
        response = await sync_to_async(self.client.get)(
            reverse("api:news_search:news-search-search"),
            {"q": "测试文章0", "highlight": "true", "exact_match": "true"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 1
        # 验证高亮结果包含查询词
        highlighted_title = data["results"][0]["title"]
        assert "<em>" in highlighted_title
        assert "</em>" in highlighted_title
        assert "测试文章0" in highlighted_title.replace("<em>", "").replace("</em>", "")

    async def test_search_suggestions(self):
        """测试搜索建议功能"""
        # 重置速率限制
        rate_limit_key = f"ratelimit_search_suggest_{self.user.id}"
        await sync_to_async(cache.delete)(rate_limit_key)
        
        # 创建测试分类
        category = await NewsCategoryFactory.acreate()
        
        # 创建测试文章
        articles = []
        for i in range(3):
            article = await NewsFactory.acreate(
                title=f"人工智能{i}",
                content=f"这是关于人工智能的文章{i}",
                category=category,
                status="published",
                publish_time=timezone.now()
            )
            articles.append(article)
            # 索引文章
            await self.index_article(article)

        # 等待索引刷新
        await sync_to_async(time.sleep)(1)
        await sync_to_async(self.es_client.indices.refresh)(index=self.index_name)

        try:
            # 获取搜索建议
            response = await sync_to_async(self.client.get)(
                reverse("api:news_search:news-search-suggest"),
                {"q": "人工智能"}
            )
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "suggestions" in data
            assert any("人工智能" in suggestion for suggestion in data["suggestions"])

            # 创建搜索历史
            response = await sync_to_async(self.client.get)(
                reverse("api:news_search:news-search-search"),
                {"q": "人工智能"}
            )
            assert response.status_code == status.HTTP_200_OK

            # 获取搜索历史
            response = await sync_to_async(self.client.get)(
                reverse("api:news_search:news-search-history")
            )
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "history" in data
            assert len(data["history"]) > 0

            # 清除搜索历史
            response = await sync_to_async(self.client.post)(
                reverse("api:news_search:news-search-clear-history")
            )
            assert response.status_code == status.HTTP_200_OK

            # 验证历史已清除
            response = await sync_to_async(self.client.get)(
                reverse("api:news_search:news-search-history")
            )
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "history" in data
            assert len(data["history"]) == 0

        except Exception as e:
            logger.error(f"测试搜索建议功能失败: {str(e)}")
            raise

    async def test_hot_searches(self):
        """测试热门搜索功能"""
        # 创建测试分类
        category = await NewsCategoryFactory.acreate()
        
        # 创建测试文章
        articles = []
        for i in range(3):
            article = await NewsFactory.acreate(
                title=f"热门话题{i}",
                content=f"这是热门话题{i}的内容",
                category=category,
                status="published",
                publish_time=timezone.now()
            )
            articles.append(article)
            # 索引文章
            await self.index_article(article)

        # 等待索引刷新
        await sync_to_async(time.sleep)(1)
        await sync_to_async(self.es_client.indices.refresh)(index=self.index_name)

        try:
            # 创建热门搜索记录
            for i in range(3):
                await sync_to_async(SearchSuggestion.objects.create)(
                    keyword=f"热门话题{i}",
                    search_count=10 * (i + 1),
                    is_hot=True
                )

            # 生成热门搜索记录
            for i in range(3):
                response = await sync_to_async(self.client.get)(
                    reverse("api:news_search:news-search-search"),
                    {"q": f"热门话题{i}"}
                )
                assert response.status_code == status.HTTP_200_OK

            # 获取热门搜索
            response = await sync_to_async(self.client.get)(
                reverse("api:news_search:news-search-hot")
            )
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "hot_searches" in data
            assert len(data["hot_searches"]) == 3
            assert data["count"] == 3
            assert any("热门话题" in item["keyword"] for item in data["hot_searches"])

        except Exception as e:
            logger.error(f"测试热门搜索功能失败: {str(e)}")
            raise 