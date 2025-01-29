import pytest
import time
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient
from monitoring.models import (
    Dashboard,
    DashboardWidget,
    MonitoringVisualization,
    ErrorLog,
    AlertRule,
    AlertHistory,
    SystemMetrics,
    AlertNotificationConfig
)
from asgiref.sync import sync_to_async
import asyncio
import json
import uuid
from django.test import AsyncClient
from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate

User = get_user_model()

class AsyncAPIClient(AsyncClient):
    """异步API测试客户端"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.factory = APIRequestFactory()
        self.user = None
        self.handler = None
        self.server_name = 'testserver'
        self.server_port = 80

    async def force_authenticate(self, user=None):
        """强制认证用户"""
        self.user = user

    async def generic(self, method, path, data=None, content_type='application/json', **extra):
        """通用请求方法"""
        if data is not None and content_type == 'application/json':
            data = json.dumps(data)

        request = self.factory.generic(
            method,
            path,
            data=data,
            content_type=content_type,
            **extra
        )

        # 添加必要的请求头
        request.META.update({
            'SERVER_NAME': self.server_name,
            'SERVER_PORT': str(self.server_port),
            'HTTP_HOST': f'{self.server_name}:{self.server_port}',
            'HTTP_USER_AGENT': 'AsyncAPIClient/1.0',
            'REMOTE_ADDR': '127.0.0.1',
            'wsgi.url_scheme': 'http',
        })

        if self.user:
            force_authenticate(request, user=self.user)

        response = await self._make_request(request)
        
        # 解析响应内容
        if response.content and content_type == 'application/json':
            try:
                response.data = json.loads(response.content.decode())
            except json.JSONDecodeError:
                response.data = None
        else:
            response.data = None

        return response

    async def get(self, path, data=None, **extra):
        """GET请求"""
        return await self.generic('GET', path, data, **extra)

    async def post(self, path, data=None, **extra):
        """POST请求"""
        return await self.generic('POST', path, data, **extra)

    async def put(self, path, data=None, **extra):
        """PUT请求"""
        return await self.generic('PUT', path, data, **extra)

    async def patch(self, path, data=None, **extra):
        """PATCH请求"""
        return await self.generic('PATCH', path, data, **extra)

    async def delete(self, path, data=None, **extra):
        """DELETE请求"""
        return await self.generic('DELETE', path, data, **extra)

    async def _make_request(self, request):
        """执行请求"""
        from django.core.handlers.asgi import ASGIHandler
        from django.http import HttpResponse
        from django.urls import set_urlconf
        from django.conf import settings
        from django.http.response import HttpResponseBase

        # 设置 URL 配置
        set_urlconf(settings.ROOT_URLCONF)

        # 创建 ASGI 请求范围
        scope = {
            'type': 'http',
            'method': request.method,
            'path': request.path,
            'raw_path': request.path.encode(),
            'query_string': request.META.get('QUERY_STRING', '').encode(),
            'headers': [
                (key.lower().encode(), value.encode())
                for key, value in request.META.items()
                if key.startswith('HTTP_') or key in ('CONTENT_TYPE', 'CONTENT_LENGTH')
            ],
            'server': (self.server_name, self.server_port),
            'client': ('127.0.0.1', 50000),
            'scheme': 'http',
            'asgi': {'version': '3.0'},
        }

        # 创建异步请求处理器
        if not self.handler:
            self.handler = ASGIHandler()

        # 创建响应对象
        response = HttpResponse()
        response._headers = {}  # 使用字典而不是列表来存储头部
        response._content = b''

        # 定义接收和发送函数
        async def receive():
            body = request.body
            if not isinstance(body, bytes):
                body = body.encode('utf-8')
            return {
                'type': 'http.request',
                'body': body,
                'more_body': False,
            }

        async def send(message):
            nonlocal response
            if message['type'] == 'http.response.start':
                response.status_code = message['status']
                # 将头部信息存储为字典
                for key, value in message.get('headers', []):
                    key = key.decode('latin1')
                    value = value.decode('latin1')
                    response._headers[key] = ('X-' + key, value)
            elif message['type'] == 'http.response.body':
                response._content += message.get('body', b'')

        # 执行请求
        await self.handler(scope, receive, send)

        return response

@pytest.fixture
async def api_client():
    return AsyncAPIClient()

@pytest.fixture
def test_password():
    return 'testpass123'

@pytest.fixture
@pytest.mark.django_db
async def test_user(test_password):
    username = f'testuser_{uuid.uuid4().hex[:8]}'
    return await sync_to_async(User.objects.create_user)(
        username=username,
        password=test_password,
        email=f'{username}@example.com'
    )

@pytest.fixture
@pytest.mark.django_db
async def authenticated_client(api_client, test_user):
    await api_client.force_authenticate(user=test_user)
    return api_client

@pytest.mark.django_db
@pytest.mark.asyncio
class TestMonitoring:
    async def test_create_system_metrics(self, authenticated_client):
        """测试创建系统指标"""
        url = reverse('monitoring:system-metrics-list')
        data = {
            'metric_type': 'cpu_usage',
            'value': '85.5',
            'metadata': {'core': 0}
        }
        response = await authenticated_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert await sync_to_async(SystemMetrics.objects.count)() == 1
        first_metric = await sync_to_async(SystemMetrics.objects.first)()
        assert first_metric.value == '85.5'

    async def test_create_alert_rule(self, authenticated_client):
        """测试创建告警规则"""
        url = reverse('monitoring:alert-rules-list')
        data = {
            'name': 'CPU 使用率过高',
            'metric_type': 'cpu_usage',
            'operator': 'gt',
            'threshold': '80',
            'alert_level': 'warning',
            'is_enabled': True
        }
        response = await authenticated_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert await sync_to_async(AlertRule.objects.count)() == 1
        first_rule = await sync_to_async(AlertRule.objects.first)()
        assert first_rule.name == 'CPU 使用率过高'

    async def test_alert_rule_trigger(self, authenticated_client):
        """测试告警规则触发"""
        # 创建告警规则
        rule_url = reverse('monitoring:alert-rules-list')
        rule_data = {
            'name': 'CPU 使用率过高',
            'metric_type': 'cpu_usage',
            'operator': 'gt',
            'threshold': '80',
            'alert_level': 'warning',
            'is_enabled': True
        }
        await authenticated_client.post(rule_url, rule_data)

        # 创建触发告警的系统指标
        metrics_url = reverse('monitoring:system-metrics-list')
        metrics_data = {
            'metric_type': 'cpu_usage',
            'value': '85.5',
            'metadata': {'core': 0}
        }
        await authenticated_client.post(metrics_url, metrics_data)

        # 验证是否创建了告警历史
        assert await sync_to_async(AlertHistory.objects.count)() == 1
        first_alert = await sync_to_async(AlertHistory.objects.first)()
        assert first_alert.status == 'active'

    async def test_alert_history_operations(self, authenticated_client):
        """测试告警历史操作"""
        # 创建告警规则
        rule = await AlertRule.objects.acreate(
            name='CPU 使用率过高',
            metric_type='cpu_usage',
            operator='gt',
            threshold='80',
            alert_level='warning',
            is_enabled=True
        )

        # 创建告警历史
        alert = await AlertHistory.objects.acreate(
            rule=rule,
            metric_value=85.5,
            message='CPU 使用率超过阈值',
            status='active'
        )

        # 测试确认告警
        ack_url = reverse('monitoring:alert-history-acknowledge', args=[alert.id])
        response = await authenticated_client.post(ack_url)
        assert response.status_code == status.HTTP_200_OK
        alert = await AlertHistory.objects.aget(id=alert.id)
        assert alert.status == 'acknowledged'

        # 测试解决告警
        resolve_url = reverse('monitoring:alert-history-resolve', args=[alert.id])
        response = await authenticated_client.post(resolve_url)
        assert response.status_code == status.HTTP_200_OK
        alert = await AlertHistory.objects.aget(id=alert.id)
        assert alert.status == 'resolved'

    async def test_alert_rule_enable_disable(self, authenticated_client):
        """测试启用/禁用告警规则"""
        # 创建告警规则
        rule = await AlertRule.objects.acreate(
            name='CPU 使用率过高',
            metric_type='cpu_usage',
            operator='gt',
            threshold='80',
            alert_level='warning',
            is_enabled=True
        )

        # 测试禁用告警规则
        disable_url = reverse('monitoring:alert-rule-disable', args=[rule.id])
        response = await authenticated_client.post(disable_url)
        assert response.status_code == status.HTTP_200_OK
        rule = await AlertRule.objects.aget(id=rule.id)
        assert not rule.is_enabled

        # 测试启用告警规则
        enable_url = reverse('monitoring:alert-rule-enable', args=[rule.id])
        response = await authenticated_client.post(enable_url)
        assert response.status_code == status.HTTP_200_OK
        rule = await AlertRule.objects.aget(id=rule.id)
        assert rule.is_enabled

    async def test_create_visualization(self, authenticated_client):
        """测试创建可视化"""
        url = reverse('monitoring:visualizations-list')
        data = {
            'name': 'CPU使用率趋势图',
            'visualization_type': 'line_chart',
            'metric_type': 'cpu_usage',
            'config': {
                'time_range': '1h',
                'refresh_interval': '5m'
            }
        }
        response = await authenticated_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert await sync_to_async(MonitoringVisualization.objects.count)() == 1
        visualization = await sync_to_async(MonitoringVisualization.objects.first)()
        assert visualization.name == 'CPU使用率趋势图'

    async def test_system_metrics(self, authenticated_client):
        """测试系统指标"""
        # 创建多个系统指标
        url = reverse('monitoring:system-metrics-list')
        metrics_data = [
            {
                'metric_type': 'cpu_usage',
                'value': '85.5',
                'metadata': {'core': 0}
            },
            {
                'metric_type': 'memory_usage',
                'value': '75.2',
                'metadata': {'type': 'physical'}
            }
        ]
        
        for data in metrics_data:
            response = await authenticated_client.post(url, data)
            assert response.status_code == status.HTTP_201_CREATED

        # 获取系统指标列表
        response = await authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    async def test_alert_notifications(self, authenticated_client):
        """测试告警通知"""
        # 创建告警通知配置
        config_url = reverse('monitoring:alert-notification-config-list')
        config_data = {
            'name': '邮件通知',
            'notification_type': 'email',
            'config': {
                'recipients': ['test@example.com'],
                'subject_template': '系统告警: {alert_level}',
                'body_template': '告警详情: {alert_message}'
            },
            'is_enabled': True
        }
        response = await authenticated_client.post(config_url, config_data)
        assert response.status_code == status.HTTP_201_CREATED
        assert await sync_to_async(AlertNotificationConfig.objects.count)() == 1

        # 验证配置详情
        config = await sync_to_async(AlertNotificationConfig.objects.first)()
        assert config.name == '邮件通知'
        assert config.is_enabled

    async def test_create_dashboard(self, authenticated_client):
        """测试创建仪表板"""
        url = reverse('monitoring:dashboards-list')
        data = {
            'name': '系统监控仪表板',
            'description': '显示系统关键指标',
            'layout': {
                'type': 'grid',
                'columns': 3
            }
        }
        response = await authenticated_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert await sync_to_async(Dashboard.objects.count)() == 1
        dashboard = await sync_to_async(Dashboard.objects.first)()
        assert dashboard.name == '系统监控仪表板'

    async def test_create_dashboard_widget(self, authenticated_client):
        """测试创建仪表板组件"""
        # 创建仪表板
        dashboard = await sync_to_async(Dashboard.objects.create)(
            name='系统监控仪表板',
            description='显示系统关键指标',
            layout={'type': 'grid', 'columns': 3}
        )

        # 创建可视化
        visualization = await sync_to_async(MonitoringVisualization.objects.create)(
            name='CPU使用率趋势图',
            visualization_type='line_chart',
            metric_type='cpu_usage',
            config={'time_range': '1h', 'refresh_interval': '5m'}
        )

        # 创建仪表板组件
        url = reverse('monitoring:dashboard-widgets-list')
        data = {
            'dashboard': dashboard.id,
            'visualization': visualization.id,
            'position': {'x': 0, 'y': 0, 'w': 1, 'h': 1}
        }
        response = await authenticated_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert await sync_to_async(DashboardWidget.objects.count)() == 1
        widget = await sync_to_async(DashboardWidget.objects.first)()
        assert widget.dashboard.id == dashboard.id
        assert widget.visualization.id == visualization.id

    async def test_system_status_overview(self, authenticated_client):
        """测试系统状态概览"""
        url = reverse('monitoring:system-status-list')
        response = await authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'cpu_usage' in response.data
        assert 'memory_usage' in response.data
        assert 'disk_usage' in response.data

    async def test_error_log_statistics(self, authenticated_client):
        """测试错误日志统计"""
        # 创建一些错误日志
        for _ in range(3):
            await sync_to_async(ErrorLog.objects.create)(
                error_type='RuntimeError',
                error_message='测试错误',
                stack_trace='测试堆栈跟踪',
                severity='error'
            )

        url = reverse('monitoring:error-logs-statistics')
        response = await authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_errors'] == 3
        assert 'error_types' in response.data
        assert 'severity_distribution' in response.data

    async def test_alert_notification_config(self, authenticated_client):
        """测试告警通知配置"""
        url = reverse('monitoring:alert-notification-config-list')
        data = {
            'name': '邮件通知',
            'notification_type': 'email',
            'config': {
                'recipients': ['test@example.com'],
                'subject_template': '系统告警: {alert_level}',
                'body_template': '告警详情: {alert_message}'
            },
            'is_enabled': True
        }
        response = await authenticated_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED

        # 获取配置列表
        response = await authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['name'] == '邮件通知'