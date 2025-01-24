import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from crawler.models import CrawlerConfig, CrawlerTask
from .factories import UserFactory, CrawlerConfigFactory, CrawlerTaskFactory
from unittest.mock import patch, Mock
import json
from django.contrib.auth import get_user_model

User = get_user_model()

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

@pytest.fixture
def test_user(db):
    user = User.objects.create_user(
        username='testuser',
        password='testpass123',
        email='test@example.com'
    )
    return user

@pytest.fixture
def test_config(db):
    """创建测试用的爬虫配置"""
    config = CrawlerConfig.objects.create(
        name='Test Config',
        source_url='http://example.com',
        crawler_type=3,  # 网页类型
        config_data={
            'article_selector': 'article',
            'title_selector': 'h1',
            'content_selector': '.content'
        },
        interval=60,
        status=1,  # 启用状态
        is_active=True  # 确保配置处于激活状态
    )
    return config

@pytest.fixture
def test_task(test_config):
    """创建测试用的爬虫任务"""
    task = CrawlerTask.objects.create(
        config=test_config,
        task_id='test-task-id',
        status=CrawlerTask.Status.PENDING,
        result={},
        error_message=''
    )
    return task

class TestCrawlerManagement:
    """TC-CRAWLER-001: 爬虫配置管理测试"""

    @pytest.fixture
    def crawler_config_data(self):
        """爬虫配置测试数据"""
        return {
            'name': 'Test News Crawler',
            'description': 'Test crawler for news website',
            'source_url': 'https://example.com/news',
            'crawler_type': 3,  # 网页类型
            'config_data': {
                'article_selector': '.article',
                'title_selector': '.title',
                'content_selector': '.content'
            },
            'headers': {
                'User-Agent': 'Mozilla/5.0'
            },
            'interval': 30,
            'status': 1  # 启用状态
        }

    def test_create_crawler_config(self, authenticated_client, crawler_config_data):
        """测试创建爬虫配置"""
        url = reverse('api:crawler:crawler-config-list')
        response = authenticated_client.post(url, crawler_config_data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert CrawlerConfig.objects.filter(name=crawler_config_data['name']).exists()
        
        config = CrawlerConfig.objects.get(name=crawler_config_data['name'])
        assert config.source_url == crawler_config_data['source_url']
        assert config.interval == crawler_config_data['interval']

    def test_modify_crawler_rules(self, authenticated_client, crawler_config_data):
        """测试修改爬虫规则"""
        config = CrawlerConfigFactory(**crawler_config_data)
        url = reverse('api:crawler:crawler-config-detail', kwargs={'pk': config.id})
        
        # 修改配置
        modified_data = crawler_config_data.copy()
        modified_data['interval'] = 60
        modified_data['config_data']['article_selector'] = '.news-content'
        
        response = authenticated_client.put(url, modified_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        
        # 验证修改结果
        config.refresh_from_db()
        assert config.interval == 60
        assert config.config_data['article_selector'] == '.news-content'

    def test_start_crawler_task(self, authenticated_client):
        """测试启动爬虫任务"""
        config = CrawlerConfigFactory()
        url = reverse('api:crawler:crawler-config-test', kwargs={'pk': config.id})
        
        with patch('crawler.views.crawl_single_website.delay') as mock_delay:
            mock_delay.return_value.id = 'test_task_id'
            response = authenticated_client.post(url, format='json')
            assert response.status_code == status.HTTP_200_OK
            assert 'task_id' in response.data
            
            # 创建任务
            task = CrawlerTask.objects.create(
                config=config,
                status=0  # 未开始状态
            )
            
            # 验证任务创建
            task.refresh_from_db()
            assert task.config == config
            assert task.status == 0  # 未开始状态

    def test_pause_crawler_task(self, authenticated_client):
        """测试暂停爬虫任务"""
        # 创建一个运行中的配置和任务
        config = CrawlerConfigFactory(status=1)  # 启用状态
        task = CrawlerTaskFactory(
            config=config,
            status=1  # 运行中状态
        )
        
        # 调用禁用接口
        url = reverse('api:crawler:crawler-config-disable', kwargs={'pk': config.id})
        response = authenticated_client.post(url, format='json')
        
        # 验证响应
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'success'
        
        # 验证配置状态
        config.refresh_from_db()
        assert config.status == 0  # 已禁用状态
        
        # 验证任务状态
        task.refresh_from_db()
        assert task.status == 3  # 已取消状态
        assert task.end_time is not None  # 结束时间已设置

    def test_view_task_status(self, authenticated_client):
        """测试查看任务状态"""
        task = CrawlerTaskFactory(
            status=1,  # 运行中状态
            result={'items_count': 50}
        )
        url = reverse('api:crawler:crawler-task-detail', kwargs={'pk': task.id})
        
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 1
        assert response.data['items_count'] == 50

    def test_crawler_scheduling(self, authenticated_client):
        """测试爬虫调度功能"""
        config = CrawlerConfigFactory(interval=60)  # 每小时执行一次
        url = reverse('api:crawler:crawler-config-test', kwargs={'pk': config.id})
        
        response = authenticated_client.post(url, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'task_id' in response.data

    def test_error_handling(self, authenticated_client):
        """测试错误处理机制"""
        task = CrawlerTaskFactory(
            status=4,  # 出错状态
            error_message='Connection timeout'
        )
        
        # 获取错误详情
        url = reverse('api:crawler:crawler-task-detail', kwargs={'pk': task.id})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['error_message'] == 'Connection timeout'
        assert response.data['status'] == 4

    def test_crawler_statistics(self, authenticated_client):
        """测试爬虫统计信息"""
        config = CrawlerConfigFactory()
        tasks = [
            CrawlerTaskFactory(
                config=config,
                status=2,  # 已完成状态
                result={'items_count': i * 10}
            ) for i in range(5)
        ]
        
        url = reverse('api:crawler:crawler-config-detail', kwargs={'pk': config.id})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_tasks'] == 5
        assert response.data['total_items'] == sum(task.result['items_count'] for task in tasks)
        assert 'success_rate' in response.data 

    def test_crawl_website(self, authenticated_client):
        """测试网站爬取功能"""
        # 创建RSS类型的爬虫配置
        config = CrawlerConfigFactory(
            crawler_type=1,  # RSS类型
            source_url='https://news.example.com/rss',
            config_data={
                'encoding': 'utf-8'
            }
        )
        
        # 模拟RSS响应
        rss_content = '''<?xml version="1.0" encoding="UTF-8" ?>
        <rss version="2.0">
            <channel>
                <title>测试新闻</title>
                <link>https://news.example.com</link>
                <description>测试新闻RSS源</description>
                <item>
                    <title>测试新闻1</title>
                    <link>https://news.example.com/1</link>
                    <description>这是测试新闻1的内容</description>
                    <pubDate>Mon, 01 Jan 2024 12:00:00 GMT</pubDate>
                </item>
                <item>
                    <title>测试新闻2</title>
                    <link>https://news.example.com/2</link>
                    <description>这是测试新闻2的内容</description>
                    <pubDate>Mon, 01 Jan 2024 13:00:00 GMT</pubDate>
                </item>
            </channel>
        </rss>'''
        
        # 模拟请求
        with patch('crawler.services.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.text = rss_content
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            # 启动爬虫任务
            url = reverse('api:crawler:crawler-config-test', kwargs={'pk': config.id})
            with patch('crawler.views.crawl_single_website.delay') as mock_delay:
                mock_delay.return_value.id = 'test_task_id'
                response = authenticated_client.post(url, format='json')
                assert response.status_code == status.HTTP_200_OK
                
                # 创建任务
                task = CrawlerTask.objects.create(
                    config=config,
                    status=2,  # 已完成状态
                    result={
                        'items': [
                            {'title': '测试新闻1'},
                            {'title': '测试新闻2'}
                        ],
                        'items_count': 2
                    }
                )
                
                # 验证爬取结果
                task.refresh_from_db()
                assert task.status == 2  # 已完成状态
                assert task.result['items_count'] == 2
                assert len(task.result['items']) == 2
                assert task.result['items'][0]['title'] == '测试新闻1'
                assert task.result['items'][1]['title'] == '测试新闻2' 

@pytest.mark.django_db
class TestCrawlerAPI:
    """爬虫模块API测试"""

    def test_create_crawler_config(self, api_client, test_user):
        login_url = reverse('api:auth:token_obtain')
        url = reverse('api:crawler:crawler-config-list')
        
        # 登录获取 token
        login_response = api_client.post(login_url, {
            'username': test_user.username,
            'password': 'testpass123'
        })
        access_token = login_response.data['access']
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        data = {
            'name': 'New Crawler Config',
            'description': 'Test crawler config',
            'source_url': 'http://example.com',
            'crawler_type': 1,  # RSS类型
            'config_data': {
                'article_selector': 'article',
                'title_selector': 'h1',
                'content_selector': '.content'
            },
            'headers': {
                'User-Agent': 'Mozilla/5.0'
            },
            'interval': 60,
            'status': 1
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == data['name']

    def test_update_crawler_config(self, api_client, test_user, test_config):
        login_url = reverse('api:auth:token_obtain')
        url = reverse('api:crawler:crawler-config-detail', args=[test_config.id])
        
        # 登录获取 token
        login_response = api_client.post(login_url, {
            'username': test_user.username,
            'password': 'testpass123'
        })
        access_token = login_response.data['access']
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        data = {
            'name': 'Updated Config',
            'crawl_rules': {
                'article_selector': 'div.article',
                'title_selector': '.title',
                'content_selector': '.body'
            }
        }
        response = api_client.patch(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == data['name']

    def test_crawler_config_control(self, api_client, test_user, test_config):
        login_url = reverse('api:auth:token_obtain')
        enable_url = reverse('api:crawler:crawler-config-enable', args=[test_config.id])
        disable_url = reverse('api:crawler:crawler-config-disable', args=[test_config.id])
        
        # 登录获取 token
        login_response = api_client.post(login_url, {
            'username': test_user.username,
            'password': 'testpass123'
        })
        access_token = login_response.data['access']
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # 启用爬虫配置
        response = api_client.post(enable_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_active'] is True
        
        # 禁用爬虫配置
        response = api_client.post(disable_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_active'] is False

    def test_test_crawler_config(self, api_client, test_user, test_config):
        login_url = reverse('api:auth:token_obtain')
        url = reverse('api:crawler:crawler-config-test', args=[test_config.id])
        
        # 登录获取 token
        login_response = api_client.post(login_url, {
            'username': test_user.username,
            'password': 'testpass123'
        })
        access_token = login_response.data['access']
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        response = api_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'test_results' in response.data

    def test_crawler_task_management(self, api_client, test_user, test_config):
        login_url = reverse('api:auth:token_obtain')
        url = reverse('api:crawler:crawler-task-list')
        
        # 登录获取 token
        login_response = api_client.post(login_url, {
            'username': test_user.username,
            'password': 'testpass123'
        })
        access_token = login_response.data['access']
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # 创建任务
        data = {
            'config': test_config.id,
            'is_test': True
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] == 0  # 未开始状态
        
        # 获取任务列表
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0

    def test_retry_crawler_task(self, api_client, test_user, test_config):
        login_url = reverse('api:auth:token_obtain')
        
        # 登录获取 token
        login_response = api_client.post(login_url, {
            'username': test_user.username,
            'password': 'testpass123'
        })
        access_token = login_response.data['access']
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # 创建失败的爬虫任务
        task = CrawlerTask.objects.create(
            config=test_config,
            task_id='test-task-id',
            status=CrawlerTask.Status.ERROR,
            error_message='Test error'
        )
        
        # 重试任务
        url = reverse('api:crawler:crawler-task-retry', args=[task.id])
        response = api_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == CrawlerTask.Status.PENDING

    def test_bulk_crawler_operations(self, api_client, test_user):
        login_url = reverse('api:auth:token_obtain')
        url = reverse('api:crawler:crawler-config-bulk-create')
        
        # 登录获取 token
        login_response = api_client.post(login_url, {
            'username': test_user.username,
            'password': 'testpass123'
        })
        access_token = login_response.data['access']
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # 批量创建配置
        data = [
            {
                'name': f'Bulk Config {i}',
                'description': f'Test bulk config {i}',
                'source_url': f'http://example{i}.com',
                'crawler_type': 1,
                'config_data': {
                    'article_selector': 'article',
                    'title_selector': 'h1'
                },
                'headers': {'User-Agent': 'Mozilla/5.0'},
                'interval': 60,
                'status': 1
            }
            for i in range(3)
        ]
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert len(response.data) == 3

    def test_crawler_statistics(self, api_client, test_user, test_config):
        login_url = reverse('api:auth:token_obtain')
        url = reverse('api:crawler:crawler-config-stats')
        
        # 登录获取 token
        login_response = api_client.post(login_url, {
            'username': test_user.username,
            'password': 'testpass123'
        })
        access_token = login_response.data['access']
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'total_configs' in response.data
        assert 'active_configs' in response.data
        assert 'total_tasks' in response.data
        assert 'task_status_counts' in response.data 