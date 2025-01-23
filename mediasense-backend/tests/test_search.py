import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from news.models import NewsArticle, NewsCategory
from news_search.models import SearchSuggestion
from elasticsearch_dsl.connections import connections
from django.conf import settings
import elasticsearch

User = get_user_model()

@pytest.fixture(scope='session')
def es_client():
    """创建Elasticsearch测试客户端"""
    client = elasticsearch.Elasticsearch(hosts=settings.ELASTICSEARCH_HOSTS)
    # 创建测试索引
    index_name = f"{settings.ELASTICSEARCH_INDEX_PREFIX}news_articles"
    if not client.indices.exists(index=index_name):
        client.indices.create(
            index=index_name,
            body={
                "mappings": {
                    "properties": {
                        "title": {"type": "text"},
                        "content": {"type": "text"},
                        "category": {"type": "keyword"},
                        "source": {"type": "keyword"},
                        "publish_time": {"type": "date"}
                    }
                }
            }
        )
    return client

@pytest.fixture(autouse=True)
def setup_es(es_client):
    """设置Elasticsearch连接"""
    connections.create_connection(hosts=settings.ELASTICSEARCH_HOSTS)
    yield
    # 清理测试数据
    index_name = f"{settings.ELASTICSEARCH_INDEX_PREFIX}news_articles"
    if es_client.indices.exists(index=index_name):
        es_client.indices.delete(index=index_name)

@pytest.fixture
def authenticated_client(api_client, test_user):
    login_url = reverse('api:auth:token_obtain')
    login_response = api_client.post(login_url, {
        'username': test_user.username,
        'password': 'testpass123'
    })
    access_token = login_response.data['access']
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    return api_client

@pytest.fixture
def test_user(db):
    user = User.objects.create_user(
        username='testuser',
        password='testpass123',
        email='test@example.com'
    )
    return user

@pytest.fixture
def test_category():
    return NewsCategory.objects.create(
        name='Test Category',
        description='Test category description'
    )

@pytest.fixture
def test_articles(test_category):
    articles = []
    for i in range(5):
        article = NewsArticle.objects.create(
            title=f'Test Article {i}',
            content=f'Test content {i}',
            summary=f'Test summary {i}',
            source='Test Source',
            author='Test Author',
            url=f'http://example.com/article-{i}',
            category=test_category,
            tags=['test', f'article-{i}'],
            status='published'
        )
        articles.append(article)
    return articles

@pytest.fixture
def test_suggestions(db):
    suggestions = []
    for i in range(3):
        suggestion = SearchSuggestion.objects.create(
            keyword=f'测试关键词{i}',
            search_count=10-i,
            is_hot=(i == 0)
        )
        suggestions.append(suggestion)
    return suggestions

@pytest.mark.django_db
class TestSearchAPI:
    """搜索模块API测试"""

    def test_basic_search(self, authenticated_client, test_articles, es_client):
        """测试基础搜索功能"""
        # 索引测试文章
        index_name = f"{settings.ELASTICSEARCH_INDEX_PREFIX}news_articles"
        for article in test_articles:
            es_client.index(
                index=index_name,
                id=article.id,
                body={
                    'title': article.title,
                    'content': article.content,
                    'category': article.category.id,
                    'source': article.source
                }
            )
        es_client.indices.refresh(index=index_name)

        url = reverse('api:news_search:news-search-search')
        response = authenticated_client.get(url, {'q': 'Test'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0

    def test_advanced_search(self, authenticated_client, test_articles, es_client):
        """测试高级搜索功能"""
        # 索引测试文章
        index_name = f"{settings.ELASTICSEARCH_INDEX_PREFIX}news_articles"
        for article in test_articles:
            es_client.index(
                index=index_name,
                id=article.id,
                body={
                    'title': article.title,
                    'content': article.content,
                    'category': article.category.id,
                    'source': article.source
                }
            )
        es_client.indices.refresh(index=index_name)

        url = reverse('api:news_search:news-search-search')
        response = authenticated_client.get(url, {
            'q': 'Test',
            'source': 'Test Source',
            'category': test_articles[0].category.id
        })
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0

    def test_search_with_pagination(self, authenticated_client, test_articles, es_client):
        """测试搜索分页功能"""
        # 索引测试文章
        index_name = f"{settings.ELASTICSEARCH_INDEX_PREFIX}news_articles"
        for article in test_articles:
            es_client.index(
                index=index_name,
                id=article.id,
                body={
                    'title': article.title,
                    'content': article.content,
                    'category': article.category.id,
                    'source': article.source
                }
            )
        es_client.indices.refresh(index=index_name)

        url = reverse('api:news_search:news-search-search')
        response = authenticated_client.get(url, {
            'q': 'Test',
            'page': 1,
            'page_size': 2
        })
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2
        assert response.data['count'] > 2

    def test_search_suggestions(self, authenticated_client):
        """测试搜索建议功能"""
        url = reverse('api:news_search:news-search-suggest')
        SearchSuggestion.objects.create(
            keyword='test suggestion',
            search_count=10
        )
        response = authenticated_client.get(url, {'prefix': 'test'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0

    def test_hot_searches(self, authenticated_client):
        """测试热门搜索功能"""
        url = reverse('api:news_search:news-search-hot')
        SearchSuggestion.objects.create(
            keyword='hot search',
            search_count=100,
            is_hot=True
        )
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0

    def test_search_with_highlight(self, authenticated_client, test_articles, es_client):
        """测试搜索结果高亮功能"""
        # 索引测试文章
        index_name = f"{settings.ELASTICSEARCH_INDEX_PREFIX}news_articles"
        for article in test_articles:
            es_client.index(
                index=index_name,
                id=article.id,
                body={
                    'title': article.title,
                    'content': article.content,
                    'category': article.category.id,
                    'source': article.source
                }
            )
        es_client.indices.refresh(index=index_name)

        url = reverse('api:news_search:news-search-search')
        response = authenticated_client.get(url, {
            'q': 'Test',
            'highlight': 'true'
        })
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0
        assert '<em>' in response.data['results'][0]['title']

    def test_search_with_field_filter(self, authenticated_client, test_articles, es_client):
        """测试特定字段搜索功能"""
        # 索引测试文章
        index_name = f"{settings.ELASTICSEARCH_INDEX_PREFIX}news_articles"
        for article in test_articles:
            es_client.index(
                index=index_name,
                id=article.id,
                body={
                    'title': article.title,
                    'content': article.content,
                    'category': article.category.id,
                    'source': article.source
                }
            )
        es_client.indices.refresh(index=index_name)

        url = reverse('api:news_search:news-search-search')
        response = authenticated_client.get(url, {
            'q': 'Test',
            'fields': 'title,content'
        })
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0
        assert 'title' in response.data['results'][0]
        assert 'content' in response.data['results'][0]
