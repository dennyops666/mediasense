import pytest
import pytest_asyncio
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from monitoring.models import (
    SystemMetrics,
    AlertRule,
    AlertHistory,
    MonitoringVisualization,
    ErrorLog
)
from tests.factories import (
    UserFactory,
    SystemMetricsFactory,
    AlertRuleFactory,
    AlertHistoryFactory,
    MonitoringVisualizationFactory,
    ErrorLogFactory
)
from tests.async_client import AsyncAPIClient
from django.db.models.query import sync_to_async
from django.urls import reverse, include, path
from rest_framework import status
from django.urls.resolvers import URLPattern, URLResolver

User = get_user_model()
API_VERSION = 'v1'

@pytest.mark.django_db
class TestSystemMonitoring:
    """系统监控测试类"""

    @pytest_asyncio.fixture
    async def setup(self):
        """设置测试数据"""
        # 创建用户
        self.user = await UserFactory.acreate()
        
        # 创建认证令牌
        token = await sync_to_async(Token.objects.create)(user=self.user)
        
        # 设置客户端
        self.client = AsyncAPIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        
        # 创建测试数据
        self.alert_rule = await AlertRuleFactory.acreate(created_by=self.user)
        self.visualization = await MonitoringVisualizationFactory.acreate(created_by=self.user)
        
        # 清理
        yield
        await sync_to_async(SystemMetrics.objects.all().delete)()
        await sync_to_async(AlertRule.objects.all().delete)()
        await sync_to_async(AlertHistory.objects.all().delete)()
        await sync_to_async(MonitoringVisualization.objects.all().delete)()
        await sync_to_async(ErrorLog.objects.all().delete)()
        await sync_to_async(Token.objects.all().delete)()

    def get_url(self, name, *args):
        """获取完整的 URL"""
        if name == 'system-metrics-list':
            return reverse('api:monitoring:system-metrics-list')
        elif name == 'system-status-overview':
            return reverse('api:monitoring:system-status-overview')
        elif name == 'alert-rules-list':
            return reverse('api:monitoring:alert-rules-list')
        elif name == 'alert-history-list':
            return reverse('api:monitoring:alert-history-list')
        elif name == 'visualization-list':
            return reverse('api:monitoring:visualization-list')
        elif name == 'error-logs-list':
            return reverse('api:monitoring:error-logs-list')
        elif name == 'error-log-statistics':
            return reverse('api:monitoring:error-log-statistics')
        elif name == 'system-status-health':
            return reverse('api:monitoring:system-status-health')
        elif name == 'system-performance':
            return reverse('api:monitoring:system-performance')
        elif name == 'alert-rule-enable':
            return reverse('api:monitoring:alert-rule-enable', args=[args[0]])
        elif name == 'alert-rule-disable':
            return reverse('api:monitoring:alert-rule-disable', args=[args[0]])
        elif name == 'alert-history-notify':
            return reverse('api:monitoring:alert-history-notify', args=[args[0]])
        elif name == 'alert-history-acknowledge':
            return reverse('api:monitoring:alert-history-acknowledge', args=[args[0]])
        elif name == 'alert-history-resolve':
            return reverse('api:monitoring:alert-history-resolve', args=[args[0]])
        elif name == 'visualization-data':
            return reverse('api:monitoring:visualization-data', args=[args[0]])
        else:
            raise ValueError(f'Unknown URL name: {name}')

    async def test_system_metrics(self, setup):
        """测试系统指标"""
        # 创建系统指标
        await sync_to_async(SystemMetricsFactory.create)(
            metric_type='cpu',
            value=80,
            created_by=self.user
        )
        
        url = self.get_url('system-metrics-list')
        response = await self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]['metric_type'] == 'cpu'
        assert data[0]['value'] == 80

    async def test_system_metrics_unauthorized(self, setup):
        """测试未授权访问系统指标"""
        # 创建系统指标
        await sync_to_async(SystemMetricsFactory.create)(
            metric_type='cpu',
            value=80,
            created_by=self.user
        )
        
        # 使用未认证的客户端
        client = AsyncAPIClient()
        url = self.get_url('system-metrics-list')
        response = await client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_system_status(self, setup):
        """测试系统状态"""
        url = self.get_url('system-status-overview')
        response = await self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'cpu' in data
        assert 'memory' in data
        assert 'disk' in data

    async def test_alert_rules(self, setup):
        """测试告警规则"""
        url = self.get_url('alert-rules-list')
        response = await self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]['name'] == self.alert_rule.name

    async def test_alert_history(self, setup):
        """测试告警历史"""
        # 创建告警历史
        alert = await sync_to_async(AlertHistoryFactory.create)(
            rule=self.alert_rule,
            status='active',
            metric_value=95,
            created_by=self.user
        )
        
        url = self.get_url('alert-history-list')
        response = await self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]['status'] == 'active'
        assert data[0]['metric_value'] == 95

    async def test_alert_notification(self, setup):
        """测试告警通知"""
        # 创建告警历史
        alert = await sync_to_async(AlertHistoryFactory.create)(
            rule=self.alert_rule,
            status='active',
            metric_value=95,
            created_by=self.user
        )
        
        url = self.get_url('alert-history-notify', alert.id)
        response = await self.client.post(url)
        
        assert response.status_code == status.HTTP_200_OK

    async def test_monitoring_visualization(self, setup):
        """测试监控可视化"""
        url = self.get_url('visualization-list')
        response = await self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]['name'] == self.visualization.name

    async def test_error_logs(self, setup):
        """测试错误日志"""
        # 创建错误日志
        error_log = await sync_to_async(ErrorLogFactory.create)(
            message='Test error',
            severity='ERROR',
            source='test',
            created_by=self.user
        )
        
        url = self.get_url('error-logs-list')
        response = await self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]['message'] == 'Test error'
        assert data[0]['severity'] == 'ERROR'

    async def test_error_log_statistics(self, setup):
        """测试错误日志统计"""
        # 创建错误日志
        await sync_to_async(ErrorLog.objects.create)(
            message='Error 1',
            severity='ERROR',
            source='test',
            created_by=self.user
        )
        await sync_to_async(ErrorLog.objects.create)(
            message='Warning 1',
            severity='WARNING',
            source='test',
            created_by=self.user
        )
        
        url = self.get_url('error-log-statistics')
        response = await self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['total_count'] == 2
        assert data['error_count'] == 1
        assert data['warning_count'] == 1

    async def test_system_health(self, setup):
        """测试系统健康状态"""
        # 创建系统指标
        await sync_to_async(SystemMetrics.objects.create)(
            metric_type='cpu',
            value=80,
            created_by=self.user
        )
        
        url = self.get_url('system-status-health')
        response = await self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'status' in data
        assert 'checks' in data

    async def test_performance_monitor(self, setup):
        """测试性能监控"""
        # 创建系统指标
        await sync_to_async(SystemMetrics.objects.create)(
            metric_type='cpu',
            value=80,
            created_by=self.user
        )
        await sync_to_async(SystemMetrics.objects.create)(
            metric_type='memory',
            value=70,
            created_by=self.user
        )
        
        url = self.get_url('system-performance')
        response = await self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'cpu' in data
        assert 'memory' in data

    async def test_alert_rule_enable_disable(self, setup):
        """测试启用/禁用告警规则"""
        # 禁用告警规则
        url = self.get_url('alert-rule-disable', self.alert_rule.id)
        response = await self.client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert not data['is_enabled']
        
        # 启用告警规则
        url = self.get_url('alert-rule-enable', self.alert_rule.id)
        response = await self.client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['is_enabled']

    async def test_alert_history_management(self, setup):
        """测试告警历史管理"""
        # 创建告警历史
        alert = await sync_to_async(AlertHistoryFactory.create)(
            rule=self.alert_rule,
            status='active',
            metric_value=95,
            created_by=self.user
        )
        
        # 确认告警
        url = self.get_url('alert-history-acknowledge', alert.id)
        response = await self.client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['status'] == 'acknowledged'
        
        # 解决告警
        url = self.get_url('alert-history-resolve', alert.id)
        response = await self.client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['status'] == 'resolved'

    async def test_alert_rule_crud(self, setup):
        """测试告警规则的CRUD操作"""
        url = self.get_url('alert-rules-list')

        # 创建告警规则
        data = {
            'name': 'Test Alert Rule',
            'description': 'Test Description',
            'metric_type': 'cpu',
            'operator': 'gt',
            'threshold': 90.0,
            'duration': 5,
            'alert_level': 'warning'
        }
        response = await self.client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        rule_id = response.json()['id']
        
        # 读取告警规则
        response = await self.client.get(f"{url}{rule_id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['name'] == 'Test Alert Rule'
        
        # 更新告警规则
        data['threshold'] = 95.0
        response = await self.client.put(f"{url}{rule_id}/", data)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['threshold'] == 95.0
        
        # 删除告警规则
        response = await self.client.delete(f"{url}{rule_id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    async def test_alert_rule_validation(self, setup):
        """测试告警规则验证"""
        url = self.get_url('alert-rules-list')
        
        # 测试无效的阈值
        data = {
            'name': 'Invalid Rule',
            'metric_type': 'cpu',
            'operator': 'gt',
            'threshold': -1,  # 无效的阈值
            'duration': 5,
            'alert_level': 'warning'
        }
        response = await self.client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # 测试无效的持续时间
        data['threshold'] = 90
        data['duration'] = 0  # 无效的持续时间
        response = await self.client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # 测试无效的告警级别
        data['duration'] = 5
        data['alert_level'] = 'invalid'  # 无效的告警级别
        response = await self.client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_concurrent_metric_creation(self, setup):
        """测试并发创建系统指标"""
        url = self.get_url('system-metrics-list')
        
        async def create_metric(value):
            data = {
                'metric_type': 'cpu',
                'value': value,
                'metadata': {'host': f'server-{value}'}
            }
            return await self.client.post(url, data)
        
        # 并发创建10个指标
        import asyncio
        tasks = [create_metric(i) for i in range(10)]
        responses = await asyncio.gather(*tasks)

        # 验证所有请求都成功
        for response in responses:
            assert response.status_code == status.HTTP_201_CREATED
        
        # 验证数据库中的记录数
        metrics_count = await sync_to_async(SystemMetrics.objects.count)()
        assert metrics_count == 10

    async def test_alert_history_lifecycle(self, setup):
        """测试告警历史的生命周期"""
        # 创建告警历史
        alert = await sync_to_async(AlertHistoryFactory.create)(
            rule=self.alert_rule,
            status='active',
            metric_value=95,
            created_by=self.user
        )
        
        # 确认告警
        url = self.get_url('alert-history-acknowledge', alert.id)
        response = await self.client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['status'] == 'acknowledged'
        
        # 解决告警
        url = self.get_url('alert-history-resolve', alert.id)
        response = await self.client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['status'] == 'resolved'
        
        # 验证时间戳
        alert = await sync_to_async(AlertHistory.objects.get)(id=alert.id)
        assert alert.acknowledged_at is not None
        assert alert.resolved_at is not None

    async def test_visualization_data_aggregation(self, setup):
        """测试可视化数据聚合"""
        # 创建测试数据
        now = timezone.now()
        for i in range(5):
            await sync_to_async(SystemMetricsFactory.create)(
                metric_type='cpu',
                value=80 + i,
                created_by=self.user,
                timestamp=now - timedelta(minutes=i*10)
            )
        
        # 获取可视化数据
        url = self.get_url('visualization-list')
        response = await self.client.get(f"{url}{self.visualization.id}/data/")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert len(data) == 5
        # 验证数据按时间排序
        timestamps = [item['timestamp'] for item in data]
        assert timestamps == sorted(timestamps, reverse=True)

    async def test_system_metrics_boundary(self, setup):
        """测试系统指标的边界条件"""
        url = self.get_url('system-metrics-list')
        
        # 测试最大值
        data = {
            'metric_type': 'cpu',
            'value': 100,
            'metadata': {'host': 'test-server'}
        }
        response = await self.client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        
        # 测试最小值
        data['value'] = 0
        response = await self.client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        
        # 测试超出范围的值
        data['value'] = 101
        response = await self.client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        data['value'] = -1
        response = await self.client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_error_log_filtering(self, setup):
        """测试错误日志过滤"""
        # 创建不同级别的错误日志
        await sync_to_async(ErrorLogFactory.create)(
            message='Error 1',
            severity='ERROR',
            source='test',
            created_by=self.user
        )
        await sync_to_async(ErrorLogFactory.create)(
            message='Warning 1',
            severity='WARNING',
            source='test',
            created_by=self.user
        )
        await sync_to_async(ErrorLogFactory.create)(
            message='Info 1',
            severity='INFO',
            source='test',
            created_by=self.user
        )
        
        url = self.get_url('error-logs-list')
        
        # 按严重程度过滤
        response = await self.client.get(f"{url}?severity=ERROR")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 1
        
        # 按时间范围过滤
        end_time = timezone.now().isoformat()
        start_time = (timezone.now() - timedelta(hours=1)).isoformat()
        response = await self.client.get(
            f"{url}?start_time={start_time}&end_time={end_time}"
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 3

    async def test_dashboard_integration(self, setup):
        """测试仪表板集成"""
        # 创建系统指标数据
        await sync_to_async(SystemMetricsFactory.create)(
            metric_type='cpu',
            value=85,
            created_by=self.user
        )
        await sync_to_async(SystemMetricsFactory.create)(
            metric_type='memory',
            value=75,
            created_by=self.user
        )
        await sync_to_async(SystemMetricsFactory.create)(
            metric_type='disk',
            value=65,
            created_by=self.user
        )
        
        # 获取系统概览
        url = self.get_url('system-status-overview')
        response = await self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # 验证所有指标都存在
        assert all(key in data for key in ['cpu', 'memory', 'disk'])
        assert all(isinstance(data[key], (int, float)) for key in ['cpu', 'memory', 'disk'])
        
        # 验证健康状态
        url = self.get_url('system-status-health')
        response = await self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['status'] in ['healthy', 'unhealthy']