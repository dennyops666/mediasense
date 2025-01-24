import factory
import uuid
from django.utils import timezone
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory
from asgiref.sync import sync_to_async

from monitoring.models import (
    SystemMetrics, AlertRule, AlertHistory,
    MonitoringVisualization, ErrorLog, Dashboard, DashboardWidget, AlertNotificationConfig
)
from crawler.models import CrawlerConfig, CrawlerTask
from news.models import NewsArticle, NewsCategory

User = get_user_model()

class UserFactory(DjangoModelFactory):
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

    @classmethod
    async def acreate(cls, **kwargs):
        """异步创建实例"""
        return await sync_to_async(cls.create)(**kwargs)

class AsyncFactoryMixin:
    """异步工厂混入类"""

    @classmethod
    async def acreate(cls, **kwargs):
        """异步创建实例"""
        return await sync_to_async(cls.create)(**kwargs)

    @classmethod
    async def acreate_batch(cls, size, **kwargs):
        """异步批量创建实例"""
        return await sync_to_async(cls.create_batch)(size, **kwargs)

class NewsCategoryFactory(DjangoModelFactory, AsyncFactoryMixin):
    """新闻分类工厂类"""

    class Meta:
        model = NewsCategory
        django_get_or_create = ('name',)

    name = factory.Sequence(lambda n: f'测试分类{n}')
    description = factory.LazyAttribute(lambda obj: f'这是{obj.name}的描述')
    is_active = True
    level = 1

class NewsArticleFactory(DjangoModelFactory, AsyncFactoryMixin):
    """新闻文章工厂类"""

    class Meta:
        model = NewsArticle

    title = factory.Sequence(lambda n: f'测试新闻{n}')
    content = factory.LazyAttribute(lambda obj: f'这是{obj.title}的内容')
    url = factory.LazyAttribute(lambda obj: f'https://example.com/news/{obj.title}')
    source = '测试来源'
    summary = factory.LazyAttribute(lambda obj: f'这是{obj.title}的摘要')
    author = '测试作者'
    category = factory.SubFactory(NewsCategoryFactory)
    status = 'draft'
    publish_time = factory.LazyFunction(timezone.now)

class SystemMetricsFactory(AsyncFactoryMixin, DjangoModelFactory):
    """系统指标工厂类"""

    class Meta:
        model = SystemMetrics

    metric_type = 'cpu'
    value = factory.Faker('pyfloat', min_value=0, max_value=100)
    timestamp = factory.LazyFunction(timezone.now)
    metadata = factory.Dict({
        'host': factory.Sequence(lambda n: f'server-{n}'),
        'core': 'all'
    })
    created_by = factory.SubFactory(UserFactory)

class AlertRuleFactory(DjangoModelFactory):
    """告警规则工厂类"""

    class Meta:
        model = AlertRule

    name = factory.Sequence(lambda n: f'Rule {n}')
    description = factory.Faker('text')
    metric_type = 'cpu'
    operator = 'gt'
    threshold = 90.0
    duration = 5
    alert_level = 'warning'
    is_enabled = True
    created_by = factory.SubFactory(UserFactory)

    @classmethod
    async def acreate(cls, **kwargs):
        """异步创建实例"""
        return await sync_to_async(cls.create)(**kwargs)

class AlertHistoryFactory(DjangoModelFactory):
    """告警历史工厂类"""

    class Meta:
        model = AlertHistory

    rule = factory.SubFactory(AlertRuleFactory)
    status = 'active'
    metric_value = factory.Faker('pyfloat', min_value=0, max_value=100)
    note = factory.Faker('sentence')
    created_by = factory.SubFactory(UserFactory)

    @classmethod
    async def acreate(cls, **kwargs):
        """异步创建实例"""
        return await sync_to_async(cls.create)(**kwargs)

class MonitoringVisualizationFactory(DjangoModelFactory):
    """监控可视化工厂类"""

    class Meta:
        model = MonitoringVisualization

    name = factory.Sequence(lambda n: f'Visualization {n}')
    description = factory.Faker('text')
    chart_type = 'line'
    metric_type = 'cpu'
    time_range = 60
    interval = 60
    aggregation_method = 'avg'
    warning_threshold = 80.0
    critical_threshold = 90.0
    is_active = 1
    refresh_interval = 30
    created_by = factory.SubFactory(UserFactory)

    @classmethod
    async def acreate(cls, **kwargs):
        """异步创建实例"""
        return await sync_to_async(cls.create)(**kwargs)

class ErrorLogFactory(DjangoModelFactory):
    """错误日志工厂类"""

    class Meta:
        model = ErrorLog

    severity = 'ERROR'
    message = factory.Faker('sentence')
    source = factory.Faker('word')
    stack_trace = factory.Faker('text')
    timestamp = factory.LazyFunction(timezone.now)

    @classmethod
    async def acreate(cls, **kwargs):
        """异步创建实例"""
        instance = await sync_to_async(cls.create)(**kwargs)
        return instance

class DashboardFactory(AsyncFactoryMixin, DjangoModelFactory):
    """仪表板工厂类"""

    class Meta:
        model = Dashboard

    name = factory.Sequence(lambda n: f'Dashboard {n}')
    description = factory.Faker('text', max_nb_chars=200)
    layout_type = 'grid'
    layout = factory.Dict({
        'widgets': [],
        'settings': {'columns': 12, 'margin': 10, 'responsive': True}
    })
    is_default = False
    created_by = factory.SubFactory(UserFactory)

class DashboardWidgetFactory(AsyncFactoryMixin, DjangoModelFactory):
    """仪表板组件工厂类"""

    class Meta:
        model = DashboardWidget

    dashboard = factory.SubFactory(DashboardFactory)
    name = factory.Sequence(lambda n: f'Widget {n}')
    widget_type = 'chart'
    visualization = factory.SubFactory(MonitoringVisualizationFactory)
    config = factory.Dict({
        'metric_type': 'cpu',
        'chart_type': 'line',
        'refresh_interval': 30
    })
    position = factory.Dict({
        'x': 0,
        'y': 0,
        'w': 2,
        'h': 2
    })
    is_visible = True

class AlertNotificationConfigFactory(AsyncFactoryMixin, DjangoModelFactory):
    """告警通知配置工厂类"""

    class Meta:
        model = AlertNotificationConfig

    name = factory.Sequence(lambda n: f'Notification Config {n}')
    notification_type = 'email'
    config = factory.Dict({
        'email': factory.Faker('email'),
        'template': 'default',
        'subject_prefix': '[ALERT]'
    })
    alert_levels = ['warning', 'critical']
    is_active = True
    user = factory.SubFactory(UserFactory)

class CrawlerConfigFactory(DjangoModelFactory):
    """爬虫配置工厂类"""

    class Meta:
        model = CrawlerConfig

    name = factory.Sequence(lambda n: f'Crawler {n}')
    description = factory.Faker('text')
    source_url = factory.Faker('url')
    crawler_type = 1  # RSS类型
    config_data = factory.Dict({
        'categories': ['news', 'tech'],
        'encoding': 'utf-8',
        'timeout': 30
    })
    headers = factory.Dict({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    interval = 60
    status = 1  # 启用状态
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyFunction(timezone.now)

class CrawlerTaskFactory(DjangoModelFactory):
    """爬虫任务工厂类"""

    class Meta:
        model = CrawlerTask

    config = factory.SubFactory(CrawlerConfigFactory)
    status = 0  # 未开始状态
    start_time = None
    end_time = None
    result = None
    error_message = None
    retry_count = 0
    is_test = False
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyFunction(timezone.now) 