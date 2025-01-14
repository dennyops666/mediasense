import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from news.models import News
from news_search.models import SearchSuggestion
from .factories import NewsFactory, UserFactory
from elasticsearch_dsl import Search
from elasticsearch import Elasticsearch
from django.conf import settings

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

class TestNewsSearch:
    """TC-SEARCH-001: 新闻搜索功能测试"""

    @pytest.fixture
    def test_news_data(self):
        """创建测试新闻数据"""
        news_list = [
            NewsFactory(
                title=f'Test News {i}',
                content=f'Test content {i}',
                status='published'
            ) for i in range(5)
        ]
        # 确保Elasticsearch索引已更新
        es_client = Elasticsearch(hosts=settings.ELASTICSEARCH_HOSTS)
        es_client.indices.refresh(index='news')
        return news_list

    def test_basic_keyword_search(self, authenticated_client, test_news_data):
        """测试基础关键词搜索"""
        url = reverse('news-search')
        response = authenticated_client.get(url, {'q': 'Test News'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0
        assert 'Test News' in response.data['results'][0]['title']

    def test_advanced_filter_search(self, authenticated_client, test_news_data):
        """测试高级过滤搜索"""
        url = reverse('news-search')
        filters = {
            'q': 'Test',
            'status': 'published',
            'date_from': '2024-01-01',
            'date_to': '2024-12-31'
        }
        response = authenticated_client.get(url, filters)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0
        for result in response.data['results']:
            assert result['status'] == 'published'

    def test_pagination(self, authenticated_client, test_news_data):
        """测试分页获取结果"""
        url = reverse('news-search')
        # 第一页
        response1 = authenticated_client.get(url, {
            'q': 'Test',
            'page': 1,
            'page_size': 2
        })
        assert response1.status_code == status.HTTP_200_OK
        assert len(response1.data['results']) == 2
        
        # 第二页
        response2 = authenticated_client.get(url, {
            'q': 'Test',
            'page': 2,
            'page_size': 2
        })
        assert response2.status_code == status.HTTP_200_OK
        assert len(response2.data['results']) == 2
        
        # 验证两页数据不重复
        page1_ids = [item['id'] for item in response1.data['results']]
        page2_ids = [item['id'] for item in response2.data['results']]
        assert not set(page1_ids).intersection(set(page2_ids))

    def test_result_sorting(self, authenticated_client, test_news_data):
        """测试结果排序功能"""
        url = reverse('news-search')
        
        # 按时间降序
        response = authenticated_client.get(url, {
            'q': 'Test',
            'sort': '-publish_time'
        })
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        assert len(results) > 1
        for i in range(len(results)-1):
            assert results[i]['publish_time'] >= results[i+1]['publish_time']
        
        # 按相关度排序
        response = authenticated_client.get(url, {
            'q': 'Test',
            'sort': 'relevance'
        })
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0

    def test_search_suggestions(self, authenticated_client):
        """测试搜索建议功能"""
        # 创建一些搜索建议数据
        suggestions = [
            SearchSuggestion.objects.create(
                keyword=f'test suggestion {i}',
                frequency=10-i
            ) for i in range(5)
        ]
        
        # 测试获取搜索建议
        url = reverse('search-suggestions')
        response = authenticated_client.get(url, {'q': 'test'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0
        assert all('test' in suggestion.lower() 
                  for suggestion in response.data)
        
        # 测试建议按频率排序
        frequencies = [suggestion['frequency'] 
                      for suggestion in response.data]
        assert frequencies == sorted(frequencies, reverse=True)

    def test_elasticsearch_integration(self, es_client, test_news_data):
        """测试Elasticsearch集成"""
        # 确保索引存在
        assert es_client.indices.exists(index='news')
        
        # 测试文档索引
        s = Search(using=es_client, index='news')
        response = s.execute()
        assert response.hits.total.value > 0
        
        # 测试全文搜索
        s = Search(using=es_client, index='news').query(
            'multi_match',
            query='Test News',
            fields=['title^2', 'content']
        )
        response = s.execute()
        assert response.hits.total.value > 0
        assert 'Test News' in response.hits[0].title

    def test_search_result_highlighting(self, authenticated_client, test_news_data):
        """测试搜索结果高亮"""
        url = reverse('news-search')
        response = authenticated_client.get(url, {
            'q': 'Test News',
            'highlight': 'true'
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0
        assert 'highlights' in response.data['results'][0]
        assert '<em>' in response.data['results'][0]['highlights']['title'] 