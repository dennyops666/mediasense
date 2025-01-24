import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from news.models import NewsArticle, NewsCategory
from tests.factories import UserFactory, NewsFactory, CategoryFactory
from unittest.mock import patch, MagicMock
from elasticsearch_dsl.response import Response as ESResponse
from elasticsearch_dsl.response import Hit
from elasticsearch.client import Elasticsearch

User = get_user_model()

@pytest.mark.django_db
class TestNewsIntegration:
    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def test_user(self):
        return UserFactory(
            username='testuser',
            email='test@example.com',
            is_active=True
        )

    @pytest.fixture
    def test_category(self):
        return CategoryFactory(name='测试分类')

    @pytest.fixture
    def test_news(self, test_category):
        return NewsFactory(
            title='测试新闻',
            content='测试内容',
            category=test_category,
            status=NewsArticle.Status.PUBLISHED
        )

    @pytest.fixture
    def mock_es_response(self):
        """模拟Elasticsearch响应"""
        def create_response(title, total=1):
            # 创建hit对象
            hit = MagicMock()
            hit.meta = MagicMock()
            hit.meta.id = 1
            hit.meta.score = 1.0
            hit.title = title
            hit.content = f'Content for {title}'

            # 创建response对象
            response = MagicMock(spec=ESResponse)
            response.hits = MagicMock()
            response.hits.total = MagicMock()
            response.hits.total.value = total
            response.__iter__.return_value = [hit]
            
            return response
        return create_response

    def test_news_creation_and_search(self, api_client, test_user, test_category, mock_es_response):
        """测试新闻创建和搜索集成"""
        # 1. 用户认证
        api_client.force_authenticate(user=test_user)

        # 2. 创建新闻
        news_data = {
            'title': '测试新闻标题',
            'content': '这是一条测试新闻的内容',
            'category': test_category.id,
            'source': '测试来源',
            'author': '测试作者',
            'status': NewsArticle.Status.PUBLISHED,
            'url': 'http://example.com/test-news'
        }
        create_url = reverse('news:news-article-list')
        response = api_client.post(create_url, news_data)
        assert response.status_code == status.HTTP_201_CREATED
        news_id = response.data['id']

        # 3. 验证新闻已被索引
        with patch('elasticsearch_dsl.Search.execute') as mock_execute:
            mock_execute.return_value = mock_es_response('测试新闻标题')
            search_url = reverse('search:news-search-search')
            response = api_client.get(search_url, {'q': '测试新闻标题'})
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data['results']) > 0
            assert response.data['results'][0]['title'] == '测试新闻标题'

    def test_news_update_and_cache(self, api_client, test_user, test_news, mock_es_response):
        """测试新闻更新和缓存集成"""
        # 1. 用户认证
        api_client.force_authenticate(user=test_user)

        # 2. 更新新闻
        update_data = {
            'title': '更新后的标题',
            'content': '更新后的内容'
        }
        update_url = reverse('news:news-article-detail', args=[test_news.id])
        response = api_client.patch(update_url, update_data)
        assert response.status_code == status.HTTP_200_OK

        # 3. 验证缓存更新
        detail_url = reverse('news:news-article-detail', args=[test_news.id])
        response = api_client.get(detail_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == '更新后的标题'

        # 4. 验证搜索结果更新
        with patch('elasticsearch_dsl.Search.execute') as mock_execute:
            mock_execute.return_value = mock_es_response('更新后的标题')
            search_url = reverse('search:news-search-search')
            response = api_client.get(search_url, {'q': '更新后的标题'})
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data['results']) > 0
            assert response.data['results'][0]['title'] == '更新后的标题'

    def test_category_filter_and_search(self, api_client, test_user, test_category, mock_es_response):
        """测试分类筛选和搜索集成"""
        # 1. 用户认证
        api_client.force_authenticate(user=test_user)

        # 2. 创建测试新闻
        news_list = [
            NewsFactory(
                title=f'测试新闻{i}',
                content=f'测试内容{i}',
                category=test_category,
                status=NewsArticle.Status.PUBLISHED,
                url=f'http://example.com/test-news-{i}'
            ) for i in range(3)
        ]

        # 3. 测试分类筛选
        filter_url = reverse('news:news-article-list')
        response = api_client.get(filter_url, {'category': test_category.id})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3

        # 4. 测试分类搜索
        with patch('elasticsearch_dsl.Search.execute') as mock_execute:
            mock_execute.return_value = mock_es_response('测试新闻0', total=3)
            search_url = reverse('search:news-search-search')
            response = api_client.get(search_url, {
                'q': '测试新闻',
                'category': test_category.id
            })
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data['results']) == 1  # mock只返回一个结果

    def test_search_result_sorting(self, api_client, test_user, test_category, mock_es_response):
        """测试搜索结果排序"""
        # 1. 用户认证
        api_client.force_authenticate(user=test_user)

        # 2. 创建测试新闻
        news_list = [
            NewsFactory(
                title=f'测试新闻{i}',
                content=f'测试内容{i}',
                category=test_category,
                read_count=i,
                status=NewsArticle.Status.PUBLISHED,
                url=f'http://example.com/test-news-{i}'
            ) for i in range(3)
        ]

        # 3. 测试按热度排序
        with patch('elasticsearch_dsl.Search.execute') as mock_execute:
            mock_execute.return_value = mock_es_response('测试新闻2', total=3)
            search_url = reverse('search:news-search-search')
            response = api_client.get(search_url, {
                'q': '测试新闻',
                'sort': '-read_count'
            })
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data['results']) == 1  # mock只返回一个结果 