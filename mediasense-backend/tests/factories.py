import factory
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory
from faker import Faker

from news.models import NewsCategory
from monitoring.models import (
    MonitoringVisualization, AlertRule, Dashboard,
    DashboardWidget, SystemMetrics, AlertHistory
)

fake = Faker('zh_CN')

class UserFactory(DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'password123')
    is_active = True

class NewsCategoryFactory(DjangoModelFactory):
    class Meta:
        model = NewsCategory

    name = factory.LazyFunction(lambda: fake.word())
    description = factory.LazyFunction(lambda: fake.sentence())
    level = factory.LazyFunction(lambda: fake.random_int(min=1, max=3))
    sort_order = factory.Sequence(lambda n: n)
    is_active = 1

class MonitoringVisualizationFactory(DjangoModelFactory):
    class Meta:
        model = MonitoringVisualization

    name = factory.LazyFunction(lambda: fake.word() + '监控')
    description = factory.LazyFunction(lambda: fake.sentence())
    chart_type = factory.Iterator(['line', 'bar', 'gauge', 'pie'])
    metric_type = factory.Iterator(['cpu', 'memory', 'disk', 'network'])
    time_range = factory.LazyFunction(lambda: fake.random_int(min=30, max=1440))
    interval = factory.LazyFunction(lambda: fake.random_int(min=30, max=300))
    aggregation_method = factory.Iterator(['avg', 'max', 'min', 'sum'])
    warning_threshold = factory.LazyFunction(lambda: fake.random_int(min=70, max=80))
    critical_threshold = factory.LazyFunction(lambda: fake.random_int(min=85, max=95))
    is_active = 1
    refresh_interval = factory.LazyFunction(lambda: fake.random_int(min=30, max=300))
    created_by = factory.SubFactory(UserFactory)

class AlertRuleFactory(DjangoModelFactory):
    class Meta:
        model = AlertRule

    name = factory.LazyFunction(lambda: fake.word() + '告警规则')
    description = factory.LazyFunction(lambda: fake.sentence())
    metric_type = factory.Iterator(['cpu', 'memory', 'disk', 'network'])
    operator = factory.Iterator(['gt', 'lt', 'gte', 'lte'])
    threshold = factory.LazyFunction(lambda: fake.random_int(min=70, max=95))
    duration = factory.LazyFunction(lambda: fake.random_int(min=1, max=15))
    alert_level = factory.Iterator(['info', 'warning', 'critical'])
    is_active = 1
    created_by = factory.SubFactory(UserFactory)

class DashboardFactory(DjangoModelFactory):
    class Meta:
        model = Dashboard

    name = factory.LazyFunction(lambda: fake.word() + '仪表板')
    description = factory.LazyFunction(lambda: fake.sentence())
    layout_type = factory.Iterator(['GRID', 'FLOW'])
    is_default = factory.Iterator([0, 1])
    created_by = factory.SubFactory(UserFactory)

class DashboardWidgetFactory(DjangoModelFactory):
    class Meta:
        model = DashboardWidget

    dashboard = factory.SubFactory(DashboardFactory)
    name = factory.LazyFunction(lambda: fake.word() + '组件')
    widget_type = factory.Iterator(['SYSTEM_OVERVIEW', 'PERFORMANCE_TREND', 'ALERT_STATISTICS'])
    config = factory.Dict({
        'visualization_id': factory.SelfAttribute('..visualization.id'),
        'refresh_interval': 30
    })
    position = factory.Dict({
        'x': factory.LazyFunction(lambda: fake.random_int(min=0, max=11)),
        'y': factory.LazyFunction(lambda: fake.random_int(min=0, max=11)),
        'w': factory.LazyFunction(lambda: fake.random_int(min=3, max=12)),
        'h': factory.LazyFunction(lambda: fake.random_int(min=2, max=8))
    })
    is_visible = 1
    visualization = factory.SubFactory(MonitoringVisualizationFactory)

class SystemMetricsFactory(DjangoModelFactory):
    class Meta:
        model = SystemMetrics

    metric_type = factory.Iterator(['cpu', 'memory', 'disk', 'network'])
    value = factory.LazyFunction(lambda: fake.random_int(min=0, max=100))
    metadata = factory.Dict({
        'host': factory.LazyFunction(lambda: fake.hostname()),
        'timestamp': factory.LazyFunction(lambda: fake.date_time().isoformat())
    })

class AlertHistoryFactory(DjangoModelFactory):
    class Meta:
        model = AlertHistory

    rule = factory.SubFactory(AlertRuleFactory)
    status = factory.Iterator(['active', 'resolved', 'acknowledged'])
    metric_value = factory.LazyFunction(lambda: fake.random_int(min=0, max=100))
    triggered_at = factory.LazyFunction(lambda: fake.date_time_this_month())
    resolved_at = factory.LazyFunction(lambda: fake.date_time_this_month())
    acknowledged_at = factory.LazyFunction(lambda: fake.date_time_this_month())
    acknowledged_by = factory.SubFactory(UserFactory)
    note = factory.LazyFunction(lambda: fake.sentence()) 