import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from django.contrib.auth import get_user_model
from news.models import NewsArticle, NewsCategory
from .factories import NewsArticleFactory, NewsCategoryFactory, UserFactory
from django.utils import timezone
from django.db import transaction
from custom_auth.models import User
from tests.base import BaseTestCase, BaseAPITestCase
from asgiref.sync import sync_to_async

pytestmark = pytest.mark.django_db

User = get_user_model()

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

@pytest.fixture
def test_user(db):
    user = User.objects.create_user(
        username='testuser',
        password='testpass123',
        email='test@example.com'
    )
    return user

@pytest.fixture
def test_category(db):
    category = NewsCategory.objects.create(
        name='Test Category',
        description='Test category description'
    )
    return category

@pytest.fixture
def test_article(test_category):
    return NewsArticle.objects.create(
        title='Test Article',
        content='Test article content',
        summary='Test article summary',
        source='Test Source',
        author='Test Author',
        url='http://example.com/test-article',
        category=test_category,
        tags=['test', 'article'],
        status='published'
    )

@pytest.mark.django_db
class TestNewsAPI:
    """新闻模块API测试"""

    def test_create_article(self, api_client, test_user, test_category):
        """测试创建新闻文章"""
        login_url = reverse('api:auth:token_obtain')
        url = reverse('api:news:news-article-list')
        
        # 登录获取 token
        login_response = api_client.post(login_url, {
            'username': test_user.username,
            'password': 'testpass123'
        })
        access_token = login_response.data['access']
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        data = {
            'title': 'New Article',
            'content': 'New article content',
            'source': 'Test Source',
            'url': 'http://example.com/new-article',
            'category': test_category.id
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == data['title']

    def test_get_article_list(self, authenticated_client, test_article):
        """测试获取新闻文章列表"""
        url = reverse('api:news:news-article-list')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0

    def test_get_article_detail(self, authenticated_client, test_article):
        """测试获取新闻文章详情"""
        url = reverse('api:news:news-article-detail', args=[test_article.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == test_article.title

    def test_update_article(self, api_client, test_user, test_article):
        """测试更新新闻文章"""
        login_url = reverse('api:auth:token_obtain')
        url = reverse('api:news:news-article-detail', args=[test_article.id])
        
        # 登录获取 token
        login_response = api_client.post(login_url, {
            'username': test_user.username,
            'password': 'testpass123'
        })
        access_token = login_response.data['access']
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        data = {
            'title': 'Updated Article',
            'content': test_article.content,
            'source': test_article.source,
            'url': test_article.url,
            'category': test_article.category.id
        }
        response = api_client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == data['title']

    def test_delete_article(self, api_client, test_user, test_article):
        """测试删除新闻文章"""
        login_url = reverse('api:auth:token_obtain')
        url = reverse('api:news:news-article-detail', args=[test_article.id])
        
        # 登录获取 token
        login_response = api_client.post(login_url, {
            'username': test_user.username,
            'password': 'testpass123'
        })
        access_token = login_response.data['access']
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_bulk_create_articles(self, api_client, test_user, test_category):
        """测试批量创建新闻文章"""
        # 先登录获取token
        login_url = reverse('api:auth:token_obtain')
        login_data = {
            'username': test_user.username,
            'password': 'testpass123'
        }
        login_response = api_client.post(login_url, login_data)
        access_token = login_response.data['access']
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # 批量创建文章
        url = reverse('api:news:news-article-bulk-create')
        data = [
            {
                'title': f'测试新闻{i}',
                'content': f'测试内容{i}',
                'summary': f'测试摘要{i}',
                'category': test_category.id,
                'source': '测试来源',
                'author': '测试作者',
                'url': f'http://example.com/test-{i}',
                'tags': ['test', 'article'],
                'publish_time': timezone.now().isoformat()
            }
            for i in range(3)
        ]
        response = api_client.post(url, data, format='json')
        print(f"Response data: {response.data}")
        assert response.status_code == status.HTTP_201_CREATED
        assert len(response.data) == 3

    def test_bulk_delete_articles(self, api_client, test_user, test_article):
        """测试批量删除新闻文章"""
        # 先登录获取token
        login_url = reverse('api:auth:token_obtain')
        login_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        login_response = api_client.post(login_url, login_data)
        access_token = login_response.data['access']
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # 批量删除文章
        url = reverse('api:news:news-article-bulk-delete')
        data = {'ids': [test_article.id]}
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_204_NO_CONTENT

@pytest.mark.django_db
class TestNewsCategoryAPI:
    """新闻分类API测试"""

    def test_create_category(self, api_client, test_user):
        """测试创建新闻分类"""
        login_url = reverse('api:auth:token_obtain')
        url = reverse('api:news:category-list')
        
        # 登录获取 token
        login_response = api_client.post(login_url, {
            'username': test_user.username,
            'password': 'testpass123'
        })
        access_token = login_response.data['access']
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        data = {
            'name': 'New Category',
            'description': 'New category description'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == data['name']

    def test_get_category_list(self, api_client, test_category):
        """测试获取分类列表."""
        url = reverse('api:news:category-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) > 0

    def test_get_category_detail(self, api_client, test_category):
        """测试获取分类详情."""
        url = reverse('api:news:category-detail', args=[test_category.id])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == test_category.name

    def test_update_category(self, api_client, test_user, test_category):
        """测试更新新闻分类"""
        login_url = reverse('api:auth:token_obtain')
        url = reverse('api:news:category-detail', args=[test_category.id])
        
        # 登录获取 token
        login_response = api_client.post(login_url, {
            'username': test_user.username,
            'password': 'testpass123'
        })
        access_token = login_response.data['access']
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        data = {
            'name': 'Updated Category',
            'description': test_category.description
        }
        response = api_client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == data['name']

    def test_delete_category(self, api_client, test_user, test_category):
        """测试删除新闻分类"""
        login_url = reverse('api:auth:token_obtain')
        url = reverse('api:news:category-detail', args=[test_category.id])
        
        # 登录获取 token
        login_response = api_client.post(login_url, {
            'username': test_user.username,
            'password': 'testpass123'
        })
        access_token = login_response.data['access']
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

class TestNewsCRUD(BaseAPITestCase):
    """测试新闻 CRUD 操作"""

    def setUp(self):
        """测试前准备"""
        super().setUp()
        # 清理已有数据
        NewsArticle.objects.all().delete()
        NewsCategory.objects.all().delete()

    def test_create_news(self):
        """测试创建新闻"""
        # 清理已有数据
        NewsArticle.objects.all().delete()
        NewsCategory.objects.all().delete()
        
        category = NewsCategory.objects.create(name='测试分类')
        data = {
            'title': '测试新闻',
            'content': '测试内容',
            'category': category.id,
            'url': 'http://example.com/news/1',
            'status': 'draft'
        }
        response = self.client.post(reverse('api:news:news-article-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(NewsArticle.objects.count(), 1)
        news = NewsArticle.objects.first()
        self.assertEqual(news.title, '测试新闻')
        self.assertEqual(news.content, '测试内容')
        self.assertEqual(news.category, category)
        self.assertEqual(news.status, 'draft')

    def test_read_news_detail(self):
        """测试读取新闻详情"""
        category = NewsCategory.objects.create(name='测试分类')
        news = NewsArticle.objects.create(
            title='测试新闻',
            content='测试内容',
            category=category,
            url='http://example.com/news/2',
            status='draft'
        )
        response = self.client.get(reverse('api:news:news-article-detail', args=[news.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], '测试新闻')
        self.assertEqual(response.data['content'], '测试内容')
        self.assertEqual(response.data['category'], category.id)
        self.assertEqual(response.data['status'], 'draft')

    def test_update_news(self):
        """测试更新新闻"""
        category = NewsCategory.objects.create(name='测试分类')
        news = NewsArticle.objects.create(
            title='测试新闻',
            content='测试内容',
            category=category,
            url='http://example.com/news/3',
            status='draft'
        )
        data = {'title': '更新后的标题'}
        response = self.client.patch(reverse('api:news:news-article-detail', args=[news.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        news.refresh_from_db()
        self.assertEqual(news.title, '更新后的标题')

    def test_delete_news(self):
        """测试删除新闻"""
        # 清理已有数据
        NewsArticle.objects.all().delete()
        NewsCategory.objects.all().delete()
        
        category = NewsCategory.objects.create(name='测试分类')
        news = NewsArticle.objects.create(
            title='测试新闻',
            content='测试内容',
            category=category,
            url='http://example.com/news/4',
            status='draft'
        )
        response = self.client.delete(reverse('api:news:news-article-detail', args=[news.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(NewsArticle.objects.count(), 0)

    def test_batch_news_operations(self):
        """测试批量操作新闻"""
        category = NewsCategory.objects.create(name='测试分类')
        news_list = []
        for i in range(3):
            news = NewsArticle.objects.create(
                title=f'测试新闻{i+1}',
                content=f'测试内容{i+1}',
                category=category,
                url=f'http://example.com/news/batch/{i+1}',
                status='draft'
            )
            news_list.append(news)
        
        data = {
            'items': [{'id': news.id, 'status': 'published'} for news in news_list]
        }
        response = self.client.put(reverse('api:news:news-article-bulk-update'), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        for news in news_list:
            news.refresh_from_db()
            self.assertEqual(news.status, 'published')

class TestNewsCategory(APITestCase):
    """测试新闻分类功能."""

    def setUp(self):
        """测试前创建测试数据."""
        self.user = User.objects.create_user(username='testuser', password='testpass', email='test@example.com')
        self.client.force_authenticate(user=self.user)
        self.category = NewsCategory.objects.create(
            name='Test Category',
            description='Test Description'
        )

    def test_create_category(self):
        """测试创建分类."""
        url = reverse('api:news:category-list')
        data = {
            'name': 'New Category',
            'description': 'New Description'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], data['name'])

    def test_edit_category(self):
        """测试编辑分类."""
        url = reverse('api:news:category-detail', args=[self.category.id])
        data = {
            'name': 'Updated Category',
            'description': 'Updated Description'
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], data['name'])

    def test_delete_category(self):
        """测试删除分类."""
        url = reverse('api:news:category-detail', args=[self.category.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

class TestNewsViewSet(BaseAPITestCase):
    """测试新闻视图集"""

    def setUp(self):
        """测试前准备"""
        super().setUp()
        # 清理已有数据
        NewsArticle.objects.all().delete()
        NewsCategory.objects.all().delete()

    def test_list_news(self):
        """测试获取新闻列表."""
        url = reverse('api:news:news-article-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 0)  # 初始应该没有文章

    def test_create_news(self):
        """测试创建新闻"""
        # 清理已有数据
        NewsArticle.objects.all().delete()
        NewsCategory.objects.all().delete()
        
        category = NewsCategory.objects.create(name='测试分类')
        data = {
            'title': '测试新闻',
            'content': '测试内容',
            'category': category.id,
            'url': 'http://example.com/news/1',
            'status': 'draft'
        }
        response = self.client.post(reverse('api:news:news-article-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(NewsArticle.objects.count(), 1)
        news = NewsArticle.objects.first()
        self.assertEqual(news.title, '测试新闻')
        self.assertEqual(news.content, '测试内容')
        self.assertEqual(news.category, category)
        self.assertEqual(news.status, 'draft')

    def test_retrieve_news(self):
        """测试获取新闻详情"""
        category = NewsCategory.objects.create(name='测试分类')
        news = NewsArticle.objects.create(
            title='测试新闻',
            content='测试内容',
            category=category,
            url='http://example.com/news/retrieve/1',
            status='published'
        )
        
        response = self.client.get(reverse('api:news:news-article-detail', args=[news.id]))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], '测试新闻')
        self.assertEqual(response.data['content'], '测试内容')
        self.assertEqual(response.data['category'], category.id)
        self.assertEqual(response.data['status'], 'published')

    def test_update_news(self):
        """测试更新新闻"""
        category = NewsCategory.objects.create(name='测试分类')
        news = NewsArticle.objects.create(
            title='测试新闻',
            content='测试内容',
            category=category,
            url='http://example.com/news/3',
            status='draft'
        )
        data = {'title': '更新后的标题'}
        
        response = self.client.patch(reverse('api:news:news-article-detail', args=[news.id]), data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        news.refresh_from_db()
        self.assertEqual(news.title, '更新后的标题')

    def test_delete_news(self):
        """测试删除新闻"""
        # 清理已有数据
        NewsArticle.objects.all().delete()
        NewsCategory.objects.all().delete()
        
        category = NewsCategory.objects.create(name='测试分类')
        news = NewsArticle.objects.create(
            title='测试新闻',
            content='测试内容',
            category=category,
            url='http://example.com/news/4',
            status='draft'
        )
        
        response = self.client.delete(reverse('api:news:news-article-detail', args=[news.id]))
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(NewsArticle.objects.count(), 0)

    def test_batch_news_operations(self):
        """测试批量操作新闻"""
        category = NewsCategory.objects.create(name='测试分类')
        news_list = []
        for i in range(3):
            news = NewsArticle.objects.create(
                title=f'测试新闻{i+1}',
                content=f'测试内容{i+1}',
                category=category,
                url=f'http://example.com/news/batch/{i+1}',
                status='draft'
            )
            news_list.append(news)
        
        data = {
            'items': [{'id': news.id, 'status': 'published'} for news in news_list]
        }
        response = self.client.put(reverse('api:news:news-article-bulk-update'), data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for news in news_list:
            news.refresh_from_db()
            self.assertEqual(news.status, 'published') 