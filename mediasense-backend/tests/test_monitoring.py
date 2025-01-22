import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from monitoring.models import (
    SystemMetrics,
    AlertRule,
    AlertHistory,
    ErrorLog
)
from tests.factories import (
    UserFactory,
    SystemMetricsFactory,
    AlertRuleFactory,
    AlertHistoryFactory
)
from django.urls import reverse
from rest_framework import status

User = get_user_model()

@pytest.mark.django_db
class TestSystemMonitoring:
    """系统监控测试类"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """设置测试数据"""
        # 创建用户
        self.user = UserFactory()
        
        # 创建认证令牌
        self.token = Token.objects.create(user=self.user)
        
        # 设置客户端
        self.client = APIClient()
        self.client.force_authenticate(user=self.user, token=self.token)
        
        # 创建测试数据
        self.alert_rule = AlertRuleFactory(created_by=self.user)
        
        # 清理
        yield
        SystemMetrics.objects.all().delete()
        AlertRule.objects.all().delete()
        AlertHistory.objects.all().delete()
        ErrorLog.objects.all().delete()
        Token.objects.all().delete()
        User.objects.all().delete()

    def get_url(self, url_name, pk=None):
        """获取URL"""
        if pk:
            return reverse(f'api:monitoring:{url_name}', args=[pk])
        return reverse(f'api:monitoring:{url_name}')

    def test_system_metrics(self, setup):
        """测试系统指标"""
        # 创建系统指标
        SystemMetricsFactory.create(
            metric_type='cpu',
            value=80,
            created_by=self.user
        )
        
        url = self.get_url('system-metrics-list')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]['metric_type'] == 'cpu'
        assert data[0]['value'] == 80

    def test_alert_rule_crud(self, setup):
        """测试告警规则的CRUD操作"""
        # 创建告警规则
        data = {
            'name': 'Test Alert Rule',
            'description': 'Test Description',
            'metric_type': 'cpu',
            'operator': 'gt',
            'threshold': 90.0,
            'duration': 5,
            'alert_level': 'warning',
            'is_enabled': True
        }
        
        url = self.get_url('alert-rules-list')
        response = self.client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        
        # 获取告警规则列表
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 2  # 包括setup中创建的规则
        
        # 启用/禁用告警规则
        alert_rule = AlertRule.objects.first()
        url = self.get_url('alert-rule-enable', alert_rule.id)
        response = self.client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['is_enabled'] is True
        
        url = self.get_url('alert-rule-disable', alert_rule.id)
        response = self.client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['is_enabled'] is False

    def test_alert_history_lifecycle(self, setup):
        """测试告警历史记录的生命周期"""
        # 创建告警历史记录
        alert_history = AlertHistory.objects.create(
            rule=self.alert_rule,
            message='Test Alert',
            metric_value=95.0,
            status='active'
        )
        
        # 获取告警历史记录列表
        url = self.get_url('alert-history-list')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 1
        
        # 确认告警
        url = self.get_url('alert-history-acknowledge', pk=alert_history.id)
        response = self.client.post(url)
        assert response.status_code == status.HTTP_200_OK
        
        # 解决告警
        url = self.get_url('alert-history-resolve', pk=alert_history.id)
        response = self.client.post(url)
        assert response.status_code == status.HTTP_200_OK

    def test_error_logs(self, setup):
        """测试错误日志功能"""
        # 创建错误日志
        ErrorLog.objects.create(
            message='Test error message',
            severity='ERROR',
            source='test_source',
            created_by=self.user
        )
        
        # 获取错误日志列表
        url = self.get_url('error-logs-list')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]['message'] == 'Test error message'
        assert data[0]['severity'] == 'ERROR'
        assert data[0]['source'] == 'test_source'

    def test_system_health(self, setup):
        """测试系统健康状态"""
        # 创建系统指标
        SystemMetrics.objects.create(
            metric_type='cpu',
            value=80,
            created_by=self.user
        )
        
        url = self.get_url('system-status-health')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'status' in data
        assert 'checks' in data