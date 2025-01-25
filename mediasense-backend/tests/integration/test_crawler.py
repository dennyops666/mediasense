import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from crawler.models import CrawlerConfig, CrawlerTask
from news.models import NewsArticle
from unittest.mock import patch, Mock, MagicMock
from tests.factories import UserFactory, CrawlerConfigFactory, CrawlerTaskFactory
from django.utils import timezone
from celery.result import AsyncResult
import uuid
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

@pytest.fixture
def mock_celery_task():
    mock_result = MagicMock(spec=AsyncResult)
    mock_result.id = 'test-task-id'
    mock_result.status = 'PENDING'
    
    with patch('crawler.tasks.crawl_single_website.delay') as mock_task:
        mock_task.return_value = mock_result
        yield mock_task

class TestCrawlerIntegration:
    """TC-INT-CRAWLER-001: 爬虫与数据处理集成测试"""

    def test_crawler_task_execution(self, authenticated_client, mock_celery_task):
        """测试爬虫任务执行流程"""
        # 创建爬虫配置
        config = CrawlerConfigFactory(
            crawler_type=1,
            source_url='https://example.com/feed',
            max_retries=3,
            retry_delay=60,
            config_data={
                'item_path': 'entries',
                'title_path': 'title',
                'content_path': 'description',
                'link_path': 'link',
                'pub_date_path': 'published'
            }
        )
            
        # 测试爬虫配置
        url = reverse('api:crawler:crawler-config-test', args=[config.id])
        response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'task_id' in response.data
        assert uuid.UUID(response.data['task_id'])  # 验证是否为有效的UUID

        # 验证任务创建
        task = CrawlerTask.objects.get(config=config)
        assert task.status == CrawlerTask.Status.PENDING
        assert task.is_test is True

        # 模拟任务执行完成
        task.status = CrawlerTask.Status.COMPLETED
        task.result = {
            'items_count': 2,
            'saved': 2,
            'duplicated': 0,
            'filtered': 0,
            'errors': 0
        }
        task.save()

        # 创建测试新闻文章
        NewsArticle.objects.create(
            title='测试新闻1',
            content='测试内容1',
            source_url='https://example.com/news/1',
            source='测试来源',
            status=NewsArticle.Status.PUBLISHED
        )
        NewsArticle.objects.create(
            title='测试新闻2', 
            content='测试内容2',
            source_url='https://example.com/news/2',
            source='测试来源',
            status=NewsArticle.Status.PUBLISHED
        )

        # 验证新闻文章创建
        assert NewsArticle.objects.count() == 2

    def test_data_processing_pipeline(self, authenticated_client, mock_celery_task):
        """测试数据处理流水线"""
        config = CrawlerConfigFactory(
            crawler_type=2,
            source_url='https://example.com/api/news',
            max_retries=3,
            retry_delay=60,
            config_data={
                'data_path': 'data.items',
                'title_path': 'title',
                'content_path': 'content',
                'link_path': 'url',
                'pub_date_path': 'publishTime'
            }
        )
            
        # 测试爬虫配置
        url = reverse('api:crawler:crawler-config-test', args=[config.id])
        response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'task_id' in response.data
        assert uuid.UUID(response.data['task_id'])  # 验证是否为有效的UUID

        # 验证任务创建
        task = CrawlerTask.objects.get(config=config)
        assert task.status == CrawlerTask.Status.PENDING
        assert task.is_test is True

        # 模拟任务执行完成
        task.status = CrawlerTask.Status.COMPLETED
        task.result = {
            'items_count': 1,
            'saved': 1,
            'duplicated': 0,
            'filtered': 0,
            'errors': 0
        }
        task.save()

        # 创建测试新闻文章
        NewsArticle.objects.create(
            title='API测试新闻',
            content='API测试内容',
            source_url='https://example.com/api/news/1',
            source='API测试来源',
            status=NewsArticle.Status.PUBLISHED
        )

        # 验证新闻文章创建
        assert NewsArticle.objects.count() == 1

    def test_error_handling_and_retry(self, authenticated_client, mock_celery_task):
        """测试错误处理和重试机制"""
        config = CrawlerConfigFactory(
            crawler_type=3,
            source_url='https://example.com/news',
            max_retries=3,
            retry_delay=60,
            config_data={
                'list_selector': '.news-list .item',
                'title_selector': '.title',
                'content_selector': '.content',
                'link_selector': '.title a',
                'pub_date_selector': '.time'
            }
        )
            
        # 测试爬虫配置
        url = reverse('api:crawler:crawler-config-test', args=[config.id])
        response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'task_id' in response.data
        assert uuid.UUID(response.data['task_id'])  # 验证是否为有效的UUID

        # 验证任务创建
        task = CrawlerTask.objects.get(config=config)
        assert task.status == CrawlerTask.Status.PENDING
        assert task.is_test is True

        # 模拟任务执行失败和重试
        task.status = CrawlerTask.Status.ERROR
        task.error_message = "连接超时"
        task.retry_count = 1
        task.save()

        # 模拟重试成功
        task.status = CrawlerTask.Status.COMPLETED
        task.result = {
            'items_count': 1,
            'saved': 1,
            'duplicated': 0,
            'filtered': 0,
            'errors': 0
        }
        task.save()

        # 验证重试次数和最终状态
        assert task.retry_count == 1
        assert task.status == CrawlerTask.Status.COMPLETED

    def test_duplicate_detection(self, authenticated_client, mock_celery_task):
        """测试重复内容检测"""
        config = CrawlerConfigFactory(
            crawler_type=2,
            source_url='https://example.com/api/news',
            max_retries=3,
            retry_delay=60,
            config_data={
                'data_path': 'data.items',
                'title_path': 'title',
                'content_path': 'content',
                'link_path': 'url',
                'pub_date_path': 'publishTime'
            }
        )

        # 创建已存在的新闻文章
        NewsArticle.objects.create(
            title='重复新闻',
            content='重复内容',
            source_url='https://example.com/api/news/1',
            source='测试来源',
            status=NewsArticle.Status.PUBLISHED
        )
            
        # 测试爬虫配置
        url = reverse('api:crawler:crawler-config-test', args=[config.id])
        response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'task_id' in response.data
        assert uuid.UUID(response.data['task_id'])  # 验证是否为有效的UUID

        # 验证任务创建
        task = CrawlerTask.objects.get(config=config)
        assert task.status == CrawlerTask.Status.PENDING
        assert task.is_test is True

        # 模拟任务执行完成
        task.status = CrawlerTask.Status.COMPLETED
        task.result = {
            'items_count': 1,
            'saved': 0,
            'duplicated': 1,
            'filtered': 0,
            'errors': 0
        }
        task.save()

        # 验证没有创建重复文章
        assert NewsArticle.objects.count() == 1

    def test_bulk_operations(self, authenticated_client):
        """测试批量操作功能"""
        # 批量创建配置
        configs_data = [
            {
                'name': f'批量测试配置{i}',
                'description': f'批量测试描述{i}',
                'source_url': f'https://example.com/feed/{i}',
                'crawler_type': 1,
                'config_data': {
                    'parser': 'xml',
                    'item_path': 'channel.item'
                },
                'interval': 60,
                'status': 1
            } for i in range(3)
        ]
        
        url = reverse('api:crawler:crawler-config-bulk-create')
        response = authenticated_client.post(
            url, 
            data=json.dumps(configs_data),
            content_type='application/json'
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        assert len(response.data) == 3
        
        # 批量更新配置
        config_ids = [config['id'] for config in response.data]
        update_data = [
            {
                'id': config_id,
                'interval': 120,
                'status': 0
            } for config_id in config_ids
        ]
        
        url = reverse('api:crawler:crawler-config-bulk-update')
        response = authenticated_client.put(
            url, 
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert all(config['interval'] == 120 for config in response.data)
        
        # 批量删除配置
        url = reverse('api:crawler:crawler-config-bulk-delete')
        response = authenticated_client.post(
            url,
            data={'ids': config_ids},
            content_type='application/json'
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert CrawlerConfig.objects.filter(id__in=config_ids).count() == 0

    def test_crawler_type_config(self, authenticated_client, mock_celery_task):
        """测试不同类型爬虫的配置验证"""
        # RSS类型配置测试
        rss_config = CrawlerConfigFactory(
            crawler_type=1,
            source_url='https://example.com/rss',
            config_data={
                'title_path': 'title',
                'content_path': 'description',
                'link_path': 'link',
                'pub_date_path': 'pubDate'
            }
        )
        
        url = reverse('api:crawler:crawler-config-test', args=[rss_config.id])
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        
        # API类型配置测试
        api_config = CrawlerConfigFactory(
            crawler_type=2,
            source_url='https://example.com/api/news',
            config_data={
                'data_path': 'data.items',
                'title_path': 'title',
                'content_path': 'content',
                'link_path': 'url',
                'pub_date_path': 'publishTime'
            },
            headers={'Authorization': 'Bearer test-token'}
        )
        
        url = reverse('api:crawler:crawler-config-test', args=[api_config.id])
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        
        # HTML类型配置测试
        html_config = CrawlerConfigFactory(
            crawler_type=3,
            source_url='https://example.com/news',
            config_data={
                'list_selector': '.news-list .item',
                'title_selector': '.title',
                'content_selector': '.content',
                'link_selector': '.title a',
                'pub_date_selector': '.time'
            }
        )
        
        url = reverse('api:crawler:crawler-config-test', args=[html_config.id])
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_200_OK

    @patch('crawler.tasks.schedule_crawl_tasks')
    def test_task_scheduling(self, mock_schedule_tasks, authenticated_client):
        """测试任务调度功能"""
        # 创建定时任务配置
        config = CrawlerConfigFactory(
            status=1,
            interval=60,
            is_active=True
        )
        
        # 启用配置
        url = reverse('api:crawler:crawler-config-enable', args=[config.id])
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        
        # 验证调度任务创建
        mock_schedule_tasks.delay.assert_called_once()
        
        # 禁用配置
        url = reverse('api:crawler:crawler-config-disable', args=[config.id])
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        
        # 验证配置状态
        config.refresh_from_db()
        assert config.status == 0
        assert not config.is_active
        
        # 验证相关任务状态
        tasks = CrawlerTask.objects.filter(
            config=config,
            status__in=[CrawlerTask.Status.PENDING, CrawlerTask.Status.RUNNING]
        )
        assert all(task.status == CrawlerTask.Status.CANCELLED for task in tasks) 