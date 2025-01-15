import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from news.models import NewsArticle
from .factories import NewsArticleFactory, UserFactory
from elasticsearch_dsl import Search
from elasticsearch import Elasticsearch
from django.conf import settings
from news_search.documents import NewsArticleDocument
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl.connections import connections
from django.utils import timezone

pytestmark = pytest.mark.django_db

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def authenticated_client(api_client):
    user = UserFactory()
    api_client.force_authenticate(user=user)
    return api_client

@pytest.fixture
def es_client():
    return Elasticsearch(hosts=settings.ELASTICSEARCH_HOSTS)

@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """确保测试数据库和Elasticsearch索引都已准备好"""
    from django.core.management import call_command
    
    # 初始化Elasticsearch连接
    connections.create_connection(
        hosts=settings.ELASTICSEARCH_HOSTS,
        timeout=20
    )
    
    # 获取Elasticsearch客户端
    es_client = Elasticsearch(hosts=settings.ELASTICSEARCH_HOSTS)
    
    with django_db_blocker.unblock():
        # 如果索引不存在则创建
        if not es_client.indices.exists(index='news_articles'):
            NewsArticleDocument._index.create()

class TestNewsSearch:
    """TC-SEARCH-001: 新闻搜索功能测试"""

    @pytest.fixture
    def test_news_data(self):
        """创建测试新闻数据"""
        # 创建测试数据
        news_list = [
            NewsArticleFactory(
                title=f'Test News {i}',
                content=f'Test content {i}',
                summary=f'Test summary {i}',
                source='Test Source',
                author='Test Author',
                url=f'https://example.com/test-{i}',
                status='published',
                sentiment_score=0.5,
                publish_time=timezone.now()
            ) for i in range(5)
        ]
        
        # 同步数据到Elasticsearch
        for news in news_list:
            doc = NewsArticleDocument()
            doc.title = news.title
            doc.content = news.content
            doc.summary = news.summary
            doc.source = news.source
            doc.author = news.author
            doc.url = news.url
            doc.status = news.status
            doc.sentiment_score = news.sentiment_score
            doc.publish_time = news.publish_time
            doc.created_at = news.created_at
            doc.updated_at = news.updated_at
            doc.title_suggest = {
                'input': [news.title],
                'weight': 100 if news.status == 'published' else 50
            }
            doc.save()
        
        # 确保Elasticsearch索引已更新
        es_client = Elasticsearch(hosts=settings.ELASTICSEARCH_HOSTS)
        es_client.indices.refresh(index='news_articles')
        return news_list

    def test_basic_keyword_search(self, authenticated_client, test_news_data):
        """测试基础关键词搜索"""
        url = reverse('news-search-search')
        response = authenticated_client.get(url, {'query': 'Test News'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0
        assert 'Test News' in response.data['results'][0]['title']

    def test_advanced_filter_search(self, authenticated_client, test_news_data):
        """测试高级过滤搜索"""
        url = reverse('news-search-search')
        filters = {
            'query': 'Test',
            'status': 'published',
            'time_range': {
                'start': '2024-01-01',
                'end': '2025-12-31'
            }
        }
        response = authenticated_client.get(url, filters)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0
        for result in response.data['results']:
            assert result['status'] == 'published'

    def test_pagination(self, authenticated_client, test_news_data):
        """测试分页获取结果"""
        url = reverse('news-search-search')
        # 第一页
        response1 = authenticated_client.get(url, {
            'query': 'Test',
            'page': 1,
            'size': 2
        })
        assert response1.status_code == status.HTTP_200_OK
        assert len(response1.data['results']) == 2
        
        # 第二页
        response2 = authenticated_client.get(url, {
            'query': 'Test',
            'page': 2,
            'size': 2
        })
        assert response2.status_code == status.HTTP_200_OK
        assert len(response2.data['results']) == 2
        
        # 验证两页数据不重复
        page1_ids = [item['id'] for item in response1.data['results']]
        page2_ids = [item['id'] for item in response2.data['results']]
        assert not set(page1_ids).intersection(set(page2_ids))

    def test_result_sorting(self, authenticated_client, test_news_data):
        """测试结果排序功能"""
        url = reverse('news-search-search')
        
        # 按时间降序
        response = authenticated_client.get(url, {
            'query': 'Test',
            'sort': '-publish_time'
        })
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        assert len(results) > 1
        for i in range(len(results)-1):
            assert results[i]['publish_time'] >= results[i+1]['publish_time']
        
        # 按相关度排序
        response = authenticated_client.get(url, {
            'query': 'Test',
            'sort': 'relevance'
        })
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0

    def test_search_suggestions(self, authenticated_client, test_news_data):
        """测试搜索建议功能"""
        # 创建带有特定标题的测试新闻
        news_with_suggestions = [
            NewsArticleFactory(
                title=f'Python Tutorial {i}',
                content=f'Python programming tutorial content {i}',
                tags=['python', 'programming', 'tutorial'],
                status='published'
            ) for i in range(3)
        ]
        
        # 同步数据到Elasticsearch
        for news in news_with_suggestions:
            doc = NewsArticleDocument()
            doc.title = news.title
            doc.content = news.content
            doc.tags = news.tags
            doc.status = news.status
            doc.title_suggest = {
                'input': [news.title] + news.tags,
                'weight': 100 if news.status == 'published' else 50
            }
            doc.save()
        
        # 确保Elasticsearch索引已更新
        es_client = Elasticsearch(hosts=settings.ELASTICSEARCH_HOSTS)
        es_client.indices.refresh(index='news_articles')
        
        # 测试获取搜索建议
        url = reverse('news-search-suggest')
        response = authenticated_client.get(url, {'prefix': 'P'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0
        assert all('Python' in suggestion['title'] 
                  for suggestion in response.data)
        
        # 测试建议按分数排序
        scores = [suggestion['score'] 
                      for suggestion in response.data]
        assert scores == sorted(scores, reverse=True)

    def test_elasticsearch_integration(self, es_client, test_news_data):
        """测试Elasticsearch集成"""
        # 确保索引存在
        assert es_client.indices.exists(index='news_articles')
        
        # 测试文档索引
        s = Search(using=es_client, index='news_articles')
        response = s.execute()
        assert response.hits.total.value > 0
        
        # 测试全文搜索
        s = Search(using=es_client, index='news_articles').query(
            'multi_match',
            query='Test News',
            fields=['title^2', 'content']
        )
        response = s.execute()
        assert response.hits.total.value > 0
        assert 'Test News' in response.hits[0].title

    def test_search_result_highlighting(self, authenticated_client, test_news_data):
        """测试搜索结果高亮"""
        url = reverse('news-search-search')
        response = authenticated_client.get(url, {
            'query': 'Test News',
            'highlight': 'true'
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0
        assert 'title_highlight' in response.data['results'][0]
        assert '<em>' in response.data['results'][0]['title_highlight'] 