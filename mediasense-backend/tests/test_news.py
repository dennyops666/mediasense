import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from news.models import NewsArticle, NewsCategory
from .factories import NewsArticleFactory, NewsCategoryFactory, UserFactory
from django.utils import timezone
from django.db import transaction
from custom_auth.models import User
from tests.base import BaseTestCase, BaseAPITestCase
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

class TestNewsCRUD(BaseAPITestCase):
    """测试新闻 CRUD 操作"""

    def test_create_news(self):
        """测试创建新闻"""
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

class TestNewsCategory(BaseAPITestCase):
    """测试新闻分类视图集"""

    def test_create_category(self):
        """测试创建分类"""
        data = {'name': '测试分类'}
        response = self.client.post('/v1/news/categories/', data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(NewsCategory.objects.count(), 1)
        self.assertEqual(NewsCategory.objects.first().name, '测试分类')

    def test_edit_category(self):
        """测试编辑分类"""
        category = NewsCategory.objects.create(name='原始分类')
        data = {'name': '更新的分类'}
        response = self.client.patch(f'/v1/news/categories/{category.id}/', data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        category.refresh_from_db()
        self.assertEqual(category.name, '更新的分类')

    def test_delete_category(self):
        """测试删除分类"""
        category = NewsCategory.objects.create(name='测试分类')
        response = self.client.delete(f'/v1/news/categories/{category.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(NewsCategory.objects.count(), 0)

    def test_category_news_association(self):
        """测试分类与新闻的关联"""
        category1 = NewsCategory.objects.create(name='分类1')
        category2 = NewsCategory.objects.create(name='分类2')
        
        news = NewsArticle.objects.create(
            title='测试新闻',
            content='测试内容',
            category=category1,
            url='http://example.com/news/association/1',
            status='draft'
        )
        
        data = {'category': category2.id}
        response = self.client.patch(reverse('api:news:news-article-detail', args=[news.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        news.refresh_from_db()
        self.assertEqual(news.category, category2)

    def test_category_statistics(self):
        """测试分类统计"""
        category = NewsCategory.objects.create(name='测试分类')
        
        # 创建不同状态的新闻
        NewsArticle.objects.create(
            title='已发布新闻1',
            content='内容1',
            category=category,
            url='http://example.com/news/stats/1',
            status='published'
        )
        NewsArticle.objects.create(
            title='已发布新闻2',
            content='内容2',
            category=category,
            url='http://example.com/news/stats/2',
            status='published'
        )
        NewsArticle.objects.create(
            title='草稿新闻',
            content='内容3',
            category=category,
            url='http://example.com/news/stats/3',
            status='draft'
        )
        NewsArticle.objects.create(
            title='待审核新闻',
            content='内容4',
            category=category,
            url='http://example.com/news/stats/4',
            status='pending'
        )
        
        response = self.client.get(reverse('api:news:category-statistics', args=[category.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_articles'], 4)
        self.assertEqual(response.data['published_articles'], 2)

class TestNewsViewSet(BaseAPITestCase):
    """测试新闻视图集"""

    def test_list_news(self):
        """测试获取新闻列表"""
        category = NewsCategory.objects.create(name='测试分类')
        for i in range(3):
            NewsArticle.objects.create(
                title=f'测试新闻{i+1}',
                content=f'测试内容{i+1}',
                category=category,
                url=f'http://example.com/news/list/{i+1}',
                status='published'
            )
        
        response = self.client.get(reverse('api:news:news-article-list'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_create_news(self):
        """测试创建新闻"""
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