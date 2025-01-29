import factory
import uuid
from django.utils import timezone
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory
from asgiref.sync import sync_to_async
from custom_auth.models import Role, Permission
from faker import Faker
from django.db import transaction

from monitoring.models import (
    SystemMetrics, AlertRule, AlertHistory,
    MonitoringVisualization, ErrorLog, Dashboard, DashboardWidget, AlertNotificationConfig
)
from crawler.models import CrawlerConfig, CrawlerTask
from news.models import NewsArticle, NewsCategory
from ai_service.models import AnalysisRule
from monitor.models import MonitorRule, MonitorAlert, SystemMetric

User = get_user_model()
fake = Faker()

class BaseFactory(DjangoModelFactory):
    """基础工厂类"""
    
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """重写创建方法，使用事务"""
        with transaction.atomic():
            return super()._create(model_class, *args, **kwargs)
            
    @classmethod
    async def acreate(cls, **kwargs):
        """异步创建实例"""
        return await sync_to_async(cls.create)(**kwargs)

    @classmethod
    async def acreate_batch(cls, size, **kwargs):
        """异步批量创建实例"""
        return await sync_to_async(cls.create_batch)(size, **kwargs)

class PermissionFactory(BaseFactory):
    """权限工厂类"""

    class Meta:
        model = Permission
        django_get_or_create = ('name',)

    name = factory.Sequence(lambda n: f'test_permission_{n}')
    description = factory.LazyAttribute(lambda obj: f'这是{obj.name}的描述')
    code = factory.LazyAttribute(lambda obj: f'TEST_PERM_{obj.name.upper()}')

class RoleFactory(BaseFactory):
    """角色工厂类"""

    class Meta:
        model = Role
        django_get_or_create = ('name',)

    name = factory.Sequence(lambda n: f'test_role_{n}')
    description = factory.LazyAttribute(lambda obj: f'这是{obj.name}的描述')

    @factory.post_generation
    def permissions(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for permission in extracted:
                self.permissions.add(permission)

class UserFactory(BaseFactory):
    """用户工厂类"""

    class Meta:
        model = User
        django_get_or_create = ('username',)

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'password123')
    is_active = True
    user_type = 'user'
    status = 'active'

class NewsCategoryFactory(BaseFactory):
    """新闻分类工厂类"""

    class Meta:
        model = NewsCategory
        django_get_or_create = ('name',)

    name = factory.Sequence(lambda n: f'Category {n}')
    description = factory.LazyAttribute(lambda obj: f'Description for {obj.name}')
    is_active = True

class NewsArticleFactory(BaseFactory):
    """新闻文章工厂类"""

    class Meta:
        model = NewsArticle

    title = factory.Sequence(lambda n: f'Article {n}')
    content = factory.LazyAttribute(lambda obj: f'Content for {obj.title}')
    summary = factory.LazyAttribute(lambda obj: f'Summary for {obj.title}')
    source = 'Test Source'
    author = 'Test Author'
    source_url = factory.Sequence(lambda n: f'http://example.com/article-{n}')
    category = factory.SubFactory(NewsCategoryFactory)
    tags = ['test', 'article']
    status = 'published'
    publish_time = factory.LazyFunction(timezone.now)

class AnalysisRuleFactory(BaseFactory):
    """分析规则工厂类"""

    class Meta:
        model = AnalysisRule

    name = factory.Sequence(lambda n: f'测试规则{n}')
    rule_type = 'sentiment'
    system_prompt = '你是一个文本分析助手'
    user_prompt_template = '分析以下文本的情感倾向：{content}'
    is_active = True

class MonitorRuleFactory(DjangoModelFactory):
    class Meta:
        model = MonitorRule

    name = factory.Sequence(lambda n: f'测试规则 {n}')
    metric = 'cpu_usage'
    condition = 'gt'
    threshold = 90
    duration = 300
    description = factory.LazyAttribute(lambda obj: f'当{obj.metric}超过{obj.threshold}持续{obj.duration}秒时触发告警')
    is_active = True
    created_by = factory.SubFactory(UserFactory)

class MonitorAlertFactory(DjangoModelFactory):
    class Meta:
        model = MonitorAlert

    rule = factory.SubFactory(MonitorRuleFactory)
    metric_value = 95
    status = MonitorAlert.Status.ACTIVE
    message = factory.LazyAttribute(lambda obj: f'{obj.rule.name}告警: 当前值{obj.metric_value}超过阈值{obj.rule.threshold}')
    created_at = factory.Faker('date_time')

class SystemMetricFactory(DjangoModelFactory):
    class Meta:
        model = SystemMetric

    metric_name = factory.Iterator(['cpu_usage', 'memory_usage', 'disk_usage', 'network_io'])
    metric_value = factory.Faker('pyfloat', min_value=0, max_value=100)
    unit = factory.LazyAttribute(lambda obj: '%' if obj.metric_name in ['cpu_usage', 'memory_usage', 'disk_usage'] else 'MB/s')
    timestamp = factory.Faker('date_time')

class CrawlerConfigFactory(BaseFactory):
    """爬虫配置工厂类"""

    class Meta:
        model = CrawlerConfig

    name = factory.Sequence(lambda n: f'测试爬虫配置{n}')
    description = factory.LazyAttribute(lambda obj: f'这是{obj.name}的描述')
    source_url = factory.LazyAttribute(lambda obj: f'https://example.com/{obj.name}/*')
    crawler_type = 3  # 网页类型
    config_data = {
        'selectors': {
            'title': 'h1',
            'content': 'article',
            'date': '.publish-date'
        }
    }
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }
    interval = 60
    max_retries = 3
    retry_delay = 60
    status = 1  # 启用
    is_active = True

class CrawlerTaskFactory(BaseFactory):
    """爬虫任务工厂类"""

    class Meta:
        model = CrawlerTask

    config = factory.SubFactory(CrawlerConfigFactory)
    task_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    status = CrawlerTask.Status.PENDING
    start_time = None
    end_time = None
    result = None
    error_message = None
    retry_count = 0
    is_test = True
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyFunction(timezone.now)