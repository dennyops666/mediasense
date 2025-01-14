import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from crawler.models import CrawlerConfig, CrawlerTask
from .factories import UserFactory, CrawlerConfigFactory, CrawlerTaskFactory
from unittest.mock import patch
import json

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

class TestCrawlerManagement:
    """TC-CRAWLER-001: 爬虫配置管理测试"""

    @pytest.fixture
    def crawler_config_data(self):
        return {
            'name': 'Test Crawler',
            'site_name': 'Test News Site',
            'site_url': 'https://test-news.com',
            'frequency': 'daily',
            'config_type': 'rss',
            'config': {
                'rss_url': 'https://test-news.com/feed',
                'article_selector': '.article-content'
            }
        }

    def test_create_crawler_config(self, authenticated_client, crawler_config_data):
        """测试创建爬虫配置"""
        url = reverse('crawler-config-list')
        response = authenticated_client.post(url, crawler_config_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert CrawlerConfig.objects.filter(name=crawler_config_data['name']).exists()
        
        config = CrawlerConfig.objects.get(name=crawler_config_data['name'])
        assert config.site_url == crawler_config_data['site_url']
        assert config.frequency == crawler_config_data['frequency']

    def test_modify_crawler_rules(self, authenticated_client, crawler_config_data):
        """测试修改爬虫规则"""
        config = CrawlerConfigFactory(**crawler_config_data)
        url = reverse('crawler-config-detail', kwargs={'pk': config.id})
        
        # 修改配置
        modified_data = crawler_config_data.copy()
        modified_data['frequency'] = 'hourly'
        modified_data['config']['article_selector'] = '.news-content'
        
        response = authenticated_client.put(url, modified_data)
        assert response.status_code == status.HTTP_200_OK
        
        # 验证修改结果
        config.refresh_from_db()
        assert config.frequency == 'hourly'
        assert config.config['article_selector'] == '.news-content'

    def test_start_crawler_task(self, authenticated_client):
        """测试启动爬虫任务"""
        config = CrawlerConfigFactory()
        url = reverse('start-crawler', kwargs={'pk': config.id})
        
        with patch('crawler.tasks.crawl_website.delay') as mock_crawl:
            response = authenticated_client.post(url)
            assert response.status_code == status.HTTP_202_ACCEPTED
            assert mock_crawl.called
            
            # 验证任务创建
            task = CrawlerTask.objects.latest('id')
            assert task.config == config
            assert task.status == 'pending'

    def test_pause_crawler_task(self, authenticated_client):
        """测试暂停爬虫任务"""
        task = CrawlerTaskFactory(status='running')
        url = reverse('pause-crawler', kwargs={'pk': task.id})
        
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        
        # 验证任务状态
        task.refresh_from_db()
        assert task.status == 'paused'

    def test_view_task_status(self, authenticated_client):
        """测试查看任务状态"""
        task = CrawlerTaskFactory(
            status='running',
            items_count=50,
            error_message=None
        )
        url = reverse('crawler-task-detail', kwargs={'pk': task.id})
        
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'running'
        assert response.data['items_count'] == 50

    def test_crawler_scheduling(self, authenticated_client):
        """测试爬虫调度功能"""
        config = CrawlerConfigFactory(frequency='hourly')
        url = reverse('crawler-schedule')
        
        with patch('crawler.tasks.schedule_crawlers.delay') as mock_schedule:
            response = authenticated_client.post(url)
            assert response.status_code == status.HTTP_200_OK
            assert mock_schedule.called

    def test_error_handling(self, authenticated_client):
        """测试错误处理机制"""
        config = CrawlerConfigFactory()
        task = CrawlerTaskFactory(
            config=config,
            status='failed',
            error_message='Connection timeout'
        )
        
        # 获取错误详情
        url = reverse('crawler-task-error', kwargs={'pk': task.id})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['error_message'] == 'Connection timeout'
        assert response.data['status'] == 'failed'

    def test_proxy_management(self, authenticated_client):
        """测试代理管理功能"""
        # 添加代理
        url = reverse('add-proxy')
        proxy_data = {
            'address': '192.168.1.100',
            'port': 8080,
            'protocol': 'http'
        }
        
        response = authenticated_client.post(url, proxy_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        # 验证代理可用性
        check_url = reverse('check-proxy', kwargs={'pk': response.data['id']})
        response = authenticated_client.post(check_url)
        assert response.status_code == status.HTTP_200_OK

    def test_crawler_statistics(self, authenticated_client):
        """测试爬虫统计信息"""
        config = CrawlerConfigFactory()
        tasks = [
            CrawlerTaskFactory(
                config=config,
                status='completed',
                items_count=i * 10
            ) for i in range(5)
        ]
        
        url = reverse('crawler-statistics', kwargs={'pk': config.id})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_tasks'] == 5
        assert response.data['total_items'] == sum(task.items_count for task in tasks)
        assert 'success_rate' in response.data 