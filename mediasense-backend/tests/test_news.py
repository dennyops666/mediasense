import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from news.models import News, Category
from .factories import NewsFactory, CategoryFactory, UserFactory

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
    def news_data(self):
        return {
            'title': 'Test News Title',
            'content': 'Test news content',
            'summary': 'Test summary',
            'source': 'Test Source',
            'author': 'Test Author',
            'status': 'draft'
        }

    def test_create_news(self, authenticated_client, news_data):
        """测试创建新闻文章"""
        url = reverse('news-list')
        response = authenticated_client.post(url, news_data)
        assert response.status_code == status.HTTP_201_CREATED
        assert News.objects.filter(title=news_data['title']).exists()

    def test_read_news_detail(self, authenticated_client):
        """测试读取新闻详情"""
        news = NewsFactory()
        url = reverse('news-detail', kwargs={'pk': news.id})
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == news.title

    def test_update_news(self, authenticated_client, news_data):
        """测试更新新闻内容"""
        news = NewsFactory()
        url = reverse('news-detail', kwargs={'pk': news.id})
        news_data['title'] = 'Updated Title'
        response = authenticated_client.put(url, news_data)
        assert response.status_code == status.HTTP_200_OK
        news.refresh_from_db()
        assert news.title == 'Updated Title'

    def test_delete_news(self, authenticated_client):
        """测试删除新闻文章"""
        news = NewsFactory()
        url = reverse('news-detail', kwargs={'pk': news.id})
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not News.objects.filter(id=news.id).exists()

    def test_batch_news_operations(self, authenticated_client, news_data):
        """测试批量操作新闻"""
        # 批量创建
        news_list = [NewsFactory() for _ in range(3)]
        
        # 批量更新
        url = reverse('news-bulk-update')
        update_data = {
            'items': [{'id': news.id, 'status': 'published'} for news in news_list]
        }
        response = authenticated_client.put(url, update_data)
        assert response.status_code == status.HTTP_200_OK
        
        # 验证更新结果
        for news in news_list:
            news.refresh_from_db()
            assert news.status == 'published'
        
        # 批量删除
        url = reverse('news-bulk-delete')
        delete_data = {'ids': [news.id for news in news_list]}
        response = authenticated_client.post(url, delete_data)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # 验证删除结果
        assert not News.objects.filter(id__in=[news.id for news in news_list]).exists()

class TestNewsCategory:
    """TC-NEWS-002: 新闻分类功能测试"""

    @pytest.fixture
    def category_data(self):
        return {
            'name': 'Test Category',
            'description': 'Test category description',
            'status': 'active'
        }

    def test_create_category(self, authenticated_client, category_data):
        """测试创建新闻分类"""
        url = reverse('category-list')
        response = authenticated_client.post(url, category_data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Category.objects.filter(name=category_data['name']).exists()

    def test_edit_category(self, authenticated_client, category_data):
        """测试编辑分类信息"""
        category = CategoryFactory()
        url = reverse('category-detail', kwargs={'pk': category.id})
        category_data['name'] = 'Updated Category'
        response = authenticated_client.put(url, category_data)
        assert response.status_code == status.HTTP_200_OK
        category.refresh_from_db()
        assert category.name == 'Updated Category'

    def test_delete_category(self, authenticated_client):
        """测试删除新闻分类"""
        category = CategoryFactory()
        url = reverse('category-detail', kwargs={'pk': category.id})
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Category.objects.filter(id=category.id).exists()

    def test_category_news_association(self, authenticated_client, news_data):
        """测试分类新闻关联"""
        category = CategoryFactory()
        news = NewsFactory(category=category)
        
        # 验证关联关系
        assert news.category == category
        assert category.news_set.filter(id=news.id).exists()
        
        # 测试更改新闻分类
        new_category = CategoryFactory()
        url = reverse('news-detail', kwargs={'pk': news.id})
        news_data['category'] = new_category.id
        response = authenticated_client.patch(url, {'category': new_category.id})
        assert response.status_code == status.HTTP_200_OK
        
        # 验证新的关联关系
        news.refresh_from_db()
        assert news.category == new_category
        assert not category.news_set.filter(id=news.id).exists()
        assert new_category.news_set.filter(id=news.id).exists()

    def test_category_statistics(self, authenticated_client):
        """测试分类统计查看"""
        category = CategoryFactory()
        news_list = [NewsFactory(category=category) for _ in range(3)]
        
        url = reverse('category-statistics', kwargs={'pk': category.id})
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        
        # 验证统计数据
        assert response.data['total_news'] == 3
        assert response.data['published_news'] == len([
            news for news in news_list if news.status == 'published'
        ])
        assert 'latest_news' in response.data
        assert 'news_by_status' in response.data 