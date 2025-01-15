import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from news.models import NewsArticle, NewsCategory
from .factories import NewsArticleFactory, NewsCategoryFactory, UserFactory
from django.utils import timezone

pytestmark = pytest.mark.django_db

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def admin_user():
    return UserFactory(is_staff=True, is_superuser=True)

@pytest.fixture
def authenticated_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client

class TestNewsCRUD:
    """TC-NEWS-001: 新闻CRUD操作测试"""

    @pytest.fixture
    def news_data(self, admin_user):
        category = NewsCategoryFactory()
        return {
            'title': 'Test News Title',
            'content': 'Test news content',
            'summary': 'Test summary',
            'source': 'Test Source',
            'author': 'Test Author',
            'url': 'https://example.com/test-news',
            'category': category.id,
            'tags': ['test', 'news'],
            'status': 'draft',
            'publish_time': timezone.now().isoformat()
        }

    def test_create_news(self, authenticated_client, news_data):
        """测试创建新闻文章"""
        response = authenticated_client.post('/api/v1/news/news-articles/', news_data)
        assert response.status_code == status.HTTP_201_CREATED
        assert NewsArticle.objects.filter(title=news_data['title']).exists()

    def test_read_news_detail(self, authenticated_client):
        """测试读取新闻详情"""
        news = NewsArticleFactory()
        response = authenticated_client.get(f'/api/v1/news/news-articles/{news.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == news.title

    def test_update_news(self, authenticated_client, news_data):
        """测试更新新闻内容"""
        news = NewsArticleFactory()
        news_data['title'] = 'Updated Title'
        response = authenticated_client.put(f'/api/v1/news/news-articles/{news.id}/', news_data)
        assert response.status_code == status.HTTP_200_OK
        news.refresh_from_db()
        assert news.title == 'Updated Title'

    def test_delete_news(self, authenticated_client):
        """测试删除新闻文章"""
        news = NewsArticleFactory()
        response = authenticated_client.delete(f'/api/v1/news/news-articles/{news.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not NewsArticle.objects.filter(id=news.id).exists()

    def test_batch_news_operations(self, authenticated_client, news_data):
        """测试批量操作新闻"""
        # 批量创建
        news_list = [NewsArticleFactory() for _ in range(3)]
        
        # 批量更新
        update_data = {
            'items': [{'id': news.id, 'status': 'published'} for news in news_list]
        }
        response = authenticated_client.put('/api/v1/news/news-articles/bulk-update/', update_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        
        # 验证更新结果
        for news in news_list:
            news.refresh_from_db()
            assert news.status == 'published'
        
        # 批量删除
        delete_data = {'ids': [news.id for news in news_list]}
        response = authenticated_client.post('/api/v1/news/news-articles/bulk-delete/', delete_data, format='json')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # 验证删除结果
        assert not NewsArticle.objects.filter(id__in=[news.id for news in news_list]).exists()

class TestNewsCategory:
    """TC-NEWS-002: 新闻分类功能测试"""

    @pytest.fixture
    def category_data(self):
        return {
            'name': 'Test Category',
            'description': 'Test category description',
            'is_active': 1
        }

    def test_create_category(self, authenticated_client, category_data):
        """测试创建新闻分类"""
        response = authenticated_client.post('/api/v1/news/categories/', category_data)
        assert response.status_code == status.HTTP_201_CREATED
        assert NewsCategory.objects.filter(name=category_data['name']).exists()

    def test_edit_category(self, authenticated_client, category_data):
        """测试编辑分类信息"""
        category = NewsCategoryFactory()
        category_data['name'] = 'Updated Category'
        response = authenticated_client.put(f'/api/v1/news/categories/{category.id}/', category_data)
        assert response.status_code == status.HTTP_200_OK
        category.refresh_from_db()
        assert category.name == 'Updated Category'

    def test_delete_category(self, authenticated_client):
        """测试删除新闻分类"""
        category = NewsCategoryFactory()
        response = authenticated_client.delete(f'/api/v1/news/categories/{category.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not NewsCategory.objects.filter(id=category.id).exists()

    def test_category_news_association(self, authenticated_client, news_data):
        """测试分类新闻关联"""
        category = NewsCategoryFactory()
        news = NewsArticleFactory(category=category)
        
        # 验证关联关系
        assert news.category == category
        assert category.articles.filter(id=news.id).exists()
        
        # 测试更改新闻分类
        new_category = NewsCategoryFactory()
        response = authenticated_client.patch(f'/api/v1/news/news-articles/{news.id}/', {'category': new_category.id})
        assert response.status_code == status.HTTP_200_OK
        
        # 验证新的关联关系
        news.refresh_from_db()
        assert news.category == new_category
        assert not category.articles.filter(id=news.id).exists()
        assert new_category.articles.filter(id=news.id).exists()

    def test_category_statistics(self, authenticated_client):
        """测试分类统计查看"""
        category = NewsCategoryFactory()
        news_list = [NewsArticleFactory(category=category) for _ in range(3)]
        
        response = authenticated_client.get(f'/api/v1/news/categories/{category.id}/statistics/')
        assert response.status_code == status.HTTP_200_OK
        
        # 验证统计数据
        assert response.data['total_news'] == 3
        assert response.data['published_news'] == len([
            news for news in news_list if news.status == 'published'
        ])
        assert 'latest_news' in response.data
        assert 'news_by_status' in response.data 