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

    name = factory.Sequence(lambda n: f'测试分类{n}')
    description = factory.LazyAttribute(lambda obj: f'这是{obj.name}的描述')
    is_active = True
    level = 1

class NewsArticleFactory(BaseFactory):
    """新闻文章工厂类"""

    class Meta:
        model = NewsArticle

    title = factory.Sequence(lambda n: f'测试新闻{n}')
    content = factory.LazyAttribute(lambda obj: f'这是{obj.title}的内容')
    source_url = factory.LazyAttribute(lambda obj: f'https://example.com/news/{obj.title}')
    source = '测试来源'
    summary = factory.LazyAttribute(lambda obj: f'这是{obj.title}的摘要')
    author = '测试作者'
    category = factory.SubFactory(NewsCategoryFactory)
    status = 'draft'
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