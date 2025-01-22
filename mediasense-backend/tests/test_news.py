import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from news.models import NewsArticle, NewsCategory
from .factories import NewsArticleFactory, NewsCategoryFactory, UserFactory
from django.utils import timezone
from django.db import transaction
from custom_auth.models import User
from tests.base import BaseTestCase
from asgiref.sync import sync_to_async

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
            'url': f'https://example.com/test-news-{timezone.now().timestamp()}',
            'category': category.id,
            'tags': ['test', 'news'],
            'status': 'draft',
            'publish_time': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    def test_create_news(self, authenticated_client, news_data):
        """测试创建新闻文章"""
        url = reverse('api:news:news-article-list')
        response = authenticated_client.post(url, news_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert NewsArticle.objects.filter(title=news_data['title']).exists()

    def test_read_news_detail(self, authenticated_client):
        """测试读取新闻详情"""
        news = NewsArticleFactory()
        url = reverse('api:news:news-article-detail', args=[news.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == news.title

    def test_update_news(self, authenticated_client, news_data):
        """测试更新新闻内容"""
        news = NewsArticleFactory()
        news_data['title'] = 'Updated Title'
        url = reverse('api:news:news-article-detail', args=[news.id])
        response = authenticated_client.put(url, news_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        news.refresh_from_db()
        assert news.title == 'Updated Title'

    def test_delete_news(self, authenticated_client):
        """测试删除新闻文章"""
        news = NewsArticleFactory()
        url = reverse('api:news:news-article-detail', args=[news.id])
        response = authenticated_client.delete(url)
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
        response = authenticated_client.put('/v1/news/news-articles/bulk-update/', update_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        
        # 验证更新结果
        for news in news_list:
            news.refresh_from_db()
            assert news.status == 'published'
        
        # 批量删除
        delete_data = {'ids': [news.id for news in news_list]}
        response = authenticated_client.post('/v1/news/news-articles/bulk-delete/', delete_data, format='json')
        assert response.status_code == status.HTTP_204_NO_CONTENT

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
        url = reverse('api:news:category-list')
        response = authenticated_client.post(url, category_data)
        assert response.status_code == status.HTTP_201_CREATED
        assert NewsCategory.objects.filter(name=category_data['name']).exists()

    def test_edit_category(self, authenticated_client, category_data):
        """测试编辑分类信息"""
        category = NewsCategoryFactory()
        category_data['name'] = 'Updated Category'
        url = reverse('api:news:category-detail', args=[category.id])
        response = authenticated_client.put(url, category_data)
        assert response.status_code == status.HTTP_200_OK
        category.refresh_from_db()
        assert category.name == 'Updated Category'

    def test_delete_category(self, authenticated_client):
        """测试删除新闻分类"""
        category = NewsCategoryFactory()
        url = reverse('api:news:category-detail', args=[category.id])
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not NewsCategory.objects.filter(id=category.id).exists()

    def test_category_news_association(self, authenticated_client):
        """测试新闻文章与分类的关联."""
        # 创建一个管理员用户并设置认证
        admin_user = UserFactory(user_type='admin', is_staff=True, is_superuser=True)
        authenticated_client.force_authenticate(user=admin_user)

        # 创建新闻分类，确保is_active为1
        category = NewsCategoryFactory(is_active=1)
        new_category = NewsCategoryFactory(is_active=1)

        # 创建新闻文章
        news = NewsArticleFactory(category=category)

        # 更新文章分类
        url = reverse('api:news:news-article-detail', args=[news.id])
        data = {'category': new_category.id}
        response = authenticated_client.patch(url, data, format='json')
        
        # 添加详细的错误信息
        if response.status_code != status.HTTP_200_OK:
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.data}")
            print(f"Request URL: {url}")
            print(f"Request data: {data}")
            print(f"New category ID: {new_category.id}")
            print(f"New category is_active: {new_category.is_active}")
        
        assert response.status_code == status.HTTP_200_OK

        # 验证分类是否更新成功
        news.refresh_from_db()
        assert news.category == new_category

    def test_category_statistics(self, authenticated_client):
        """测试分类统计查看"""
        category = NewsCategoryFactory()
        news_list = [NewsArticleFactory(category=category) for _ in range(3)]
        
        url = reverse('api:news:category-statistics', args=[category.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        
        # 验证统计数据
        assert response.data['total_news'] == 3
        assert response.data['published_news'] == len([
            news for news in news_list if news.status == 'published'
        ])
        assert 'latest_news' in response.data
        assert 'news_by_status' in response.data

class TestNewsViewSet(BaseTestCase):
    async def test_list_news(self):
        await sync_to_async(NewsArticleFactory.create_batch)(5)
        url = '/v1/news/news-articles/'
        print(f"Request URL: {url}")
        response = await self.client.get(url)
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.data}")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)

    async def test_create_news(self):
        category = await sync_to_async(NewsCategoryFactory.create)()
        data = {
            'title': '测试新闻',
            'content': '测试内容',
            'category': category.id,
            'status': 'draft'
        }
        url = '/v1/news/news-articles/'
        print(f"Request URL: {url}")
        print(f"Request data: {data}")
        response = await self.client.post(url, data)
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.data}")
        self.assertEqual(response.status_code, 201)

    async def test_retrieve_news(self):
        news = await sync_to_async(NewsArticleFactory.create)()
        url = f'/v1/news/news-articles/{news.id}/'
        print(f"Request URL: {url}")
        response = await self.client.get(url)
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.data}")
        self.assertEqual(response.status_code, 200)

    async def test_update_news(self):
        news = await sync_to_async(NewsArticleFactory.create)()
        data = {'title': '更新的标题'}
        url = f'/v1/news/news-articles/{news.id}/'
        print(f"Request URL: {url}")
        print(f"Request data: {data}")
        response = await self.client.patch(url, data)
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.data}")
        self.assertEqual(response.status_code, 200)

    async def test_delete_news(self):
        news = await sync_to_async(NewsArticleFactory.create)()
        url = f'/v1/news/news-articles/{news.id}/'
        print(f"Request URL: {url}")
        response = await self.client.delete(url)
        print(f"Response status: {response.status_code}")
        self.assertEqual(response.status_code, 204)

    async def test_batch_news_operations(self):
        # 创建测试数据
        news_list = await sync_to_async(NewsArticleFactory.create_batch)(3)
        news_ids = [news.id for news in news_list]

        # 批量更新
        data = {
            'ids': news_ids,
            'status': 'published'
        }
        bulk_update_url = '/v1/news/news-articles/bulk-update/'
        print(f"Request URL: {bulk_update_url}")
        print(f"Request data: {data}")
        response = await self.client.put(bulk_update_url, data)
        print(f"Bulk update response status: {response.status_code}")
        print(f"Bulk update response data: {response.data}")
        self.assertEqual(response.status_code, 200)

        # 批量删除
        bulk_delete_url = '/v1/news/news-articles/bulk-delete/'
        response = await self.client.post(bulk_delete_url, {'ids': news_ids})
        print(f"Bulk delete response status: {response.status_code}")
        print(f"Bulk delete response data: {response.data}")
        self.assertEqual(response.status_code, 204) 