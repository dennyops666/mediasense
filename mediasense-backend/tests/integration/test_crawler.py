import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from unittest.mock import patch, Mock, MagicMock
from django.test import TestCase
from django.utils import timezone
from celery.result import AsyncResult
import uuid
import json
import environ
import requests
import feedparser

# 初始化环境变量
env = environ.Env()
environ.Env.read_env()

from crawler.models import CrawlerConfig, CrawlerTask
from crawler.services import CrawlerService
from crawler.tasks import run_crawler, schedule_crawlers
from news.models import NewsArticle
from tests.factories import UserFactory, CrawlerConfigFactory, CrawlerTaskFactory

pytestmark = pytest.mark.django_db

class TestCrawlerIntegration(TestCase):
    """爬虫集成测试"""
    
    databases = {'default'}
    
    def setUp(self):
        """测试准备工作"""
        # 清理数据库
        CrawlerTask.objects.all().delete()
        NewsArticle.objects.all().delete()
        CrawlerConfig.objects.all().delete()

        # 创建测试配置
        self.configs = [
            CrawlerConfigFactory(
                name=f'测试爬虫{i}',
                crawler_type=1,  # RSS类型
                source_url=f'https://example.com/feed{i}',
                status=1,  # 启用状态
                is_active=True
            ) for i in range(2)
        ]

    @patch('requests.Session.get')
    def test_full_crawler_workflow(self, mock_get):
        """测试完整的爬虫工作流程"""
        # 清理数据库
        NewsArticle.objects.all().delete()
        CrawlerConfig.objects.all().delete()
        CrawlerTask.objects.all().delete()

        # 创建一个测试源
        source = CrawlerConfig.objects.create(
            name="测试源",
            description="测试源",
            source_url="http://test.com",
            crawler_type=1,
            headers={},
            interval=30,
            status=1
        )

        # Mock RSS数据
        mock_entry = {
            'title': 'Test Title',
            'url': 'http://test.com/article/1',
            'content': 'Test Content',
            'description': 'Test Description',
            'author': 'Test Author',
            'source': '测试源',
            'pub_time': timezone.now(),
            'tags': ['test'],
            'images': ['http://test.com/image.jpg']
        }

        # Mock RSSCrawler的run方法
        with patch('crawler.crawlers.rss_crawler.RSSCrawler.run') as mock_run:
            mock_run.return_value = {
                'status': 'success',
                'message': '成功获取并解析RSS数据',
                'data': [mock_entry]
            }

            # 创建并执行爬虫任务
            service = CrawlerService()
            task = service.create_task(source)
            self.assertEqual(task.status, 0)  # 初始状态为未开始

            # 运行任务
            result = service.run_task(task)
            self.assertTrue(result)  # 任务应该成功执行

            # 验证任务状态
            task.refresh_from_db()
            self.assertEqual(task.status, 2)  # 任务状态应为已完成

            # 验证文章是否创建成功
            self.assertEqual(NewsArticle.objects.count(), 1)
            article = NewsArticle.objects.first()
            self.assertEqual(article.title, 'Test Title')
            self.assertEqual(article.source_url, 'http://test.com/article/1')
            self.assertEqual(article.content, 'Test Content')
            self.assertEqual(article.summary, 'Test Description')
            self.assertEqual(article.author, 'Test Author')
            self.assertEqual(article.source, '测试源')

    def test_data_integrity(self):
        """测试数据完整性"""
        # 创建任务
        task = CrawlerTask.objects.create(
            config=self.configs[0],
            status=0  # pending状态
        )
        
        # 验证任务创建
        self.assertIsNotNone(task.task_id)
        self.assertEqual(task.status, 0)
        self.assertIsNone(task.start_time)
        self.assertIsNone(task.end_time)
        
        # 开始任务
        task.start()
        self.assertEqual(task.status, 1)
        self.assertIsNotNone(task.start_time)
        
        # 完成任务
        result = {
            'status': 'success',
            'items_count': 10
        }
        task.complete(result)
        self.assertEqual(task.status, 2)
        self.assertIsNotNone(task.end_time)
        self.assertEqual(task.result, result)
        
        # 验证任务历史完整性
        self.assertLess(task.start_time, task.end_time)
        self.assertLess(task.created_at, task.updated_at)

    def test_error_handling(self):
        """测试错误处理"""
        task = CrawlerTask.objects.create(
            config=self.configs[0],
            status=0
        )
        
        # 模拟错误
        error_message = "测试错误"
        task.fail(error_message)
        
        # 验证错误状态
        self.assertEqual(task.status, 4)  # error状态
        self.assertEqual(task.error_message, error_message)
        self.assertIsNotNone(task.end_time)

    def test_scheduler_interval(self):
        """测试调度器间隔"""
        config = self.configs[0]
        config.interval = 30  # 30分钟间隔
        config.save()
        
        # 创建并完成一个任务
        task = CrawlerTask.objects.create(
            config=config,
            status=0
        )
        task.complete()
        
        # 更新配置的最后运行时间
        config.last_run_time = task.end_time
        config.save()
        
        # 运行调度器
        schedule_crawlers()
        
        # 验证没有创建新任务
        new_tasks = CrawlerTask.objects.filter(
            config=config,
            created_at__gt=task.created_at
        )
        self.assertEqual(len(new_tasks), 0)

class TestCrawlerAPI(APITestCase):
    """爬虫API测试"""

    def setUp(self):
        """测试准备工作"""
        # 清理数据库
        CrawlerTask.objects.all().delete()
        NewsArticle.objects.all().delete()
        CrawlerConfig.objects.all().delete()

        # 创建测试用户
        self.user = UserFactory(is_staff=True)
        self.client.force_authenticate(user=self.user)

    @patch('crawler.tasks.run_crawler.delay')
    def test_crawler_task_execution(self, mock_delay):
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
            
        # 模拟 Celery 任务
        mock_task = MagicMock()
        mock_task.id = str(uuid.uuid4())
        mock_delay.return_value = mock_task
            
        # 测试爬虫配置
        url = reverse('crawler:crawler-config-test', args=[config.id])
        with self.settings(MIDDLEWARE=[
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
        ]):
            response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('task_id', response.data)
        self.assertTrue(uuid.UUID(response.data['task_id']))  # 验证是否为有效的UUID

        # 验证任务创建
        task = CrawlerTask.objects.get(config=config)
        self.assertEqual(task.status, 0)  # pending状态
        self.assertTrue(task.is_test)

        # 模拟任务执行完成
        task.status = 2  # completed状态
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
            title='测试文章1',
            content='测试内容1',
            source_url='https://example.com/article/1',
            crawler=config,
            status='draft',
            publish_time=timezone.now()
        )
        NewsArticle.objects.create(
            title='测试文章2',
            content='测试内容2',
            source_url='https://example.com/article/2',
            crawler=config,
            status='draft',
            publish_time=timezone.now()
        )

        # 验证文章数量
        articles = NewsArticle.objects.filter(crawler=config)
        self.assertEqual(len(articles), 2)

        # 验证文章内容
        for article in articles:
            self.assertTrue(article.title.startswith('测试文章'))
            self.assertTrue(article.content.startswith('测试内容'))
            # 验证URL格式
            self.assertTrue(article.source_url.startswith('http'))

    @patch('requests.Session.get')
    def test_crawl_website(self, mock_get):
        """测试爬取网站"""
        # 清理数据库
        NewsArticle.objects.all().delete()
        CrawlerConfig.objects.all().delete()

        # 创建一个测试源
        source = CrawlerConfig.objects.create(
            name="测试源",
            description="测试源",
            source_url="http://test.com",
            crawler_type=1,
            headers={},
            interval=30,
            status=1
        )

        # Mock RSS数据
        mock_entry = {
            'title': 'Test Title',
            'url': 'http://test.com/article/1',
            'content': 'Test Content',
            'description': 'Test Description',
            'author': 'Test Author',
            'source': '测试源',
            'pub_time': timezone.now(),
            'tags': ['test'],
            'images': ['http://test.com/image.jpg']
        }

        # Mock RSSCrawler的run方法
        with patch('crawler.crawlers.rss_crawler.RSSCrawler.run') as mock_run:
            mock_run.return_value = {
                'status': 'success',
                'message': '成功获取并解析RSS数据',
                'data': [mock_entry]
            }

            # 执行爬虫任务
            service = CrawlerService()
            result = service.crawl_website(source)

            # 验证结果
            self.assertEqual(result['status'], 'success')
            self.assertEqual(NewsArticle.objects.count(), 1)

            # 验证文章内容
            article = NewsArticle.objects.first()
            self.assertEqual(article.title, 'Test Title')
            self.assertEqual(article.source_url, 'http://test.com/article/1')
            self.assertEqual(article.content, 'Test Content')
            self.assertEqual(article.summary, 'Test Description')
            self.assertEqual(article.author, 'Test Author')
            self.assertEqual(article.source, '测试源')