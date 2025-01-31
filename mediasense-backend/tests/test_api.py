 from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from monitoring.models import (
    AlertRule,
    AlertHistory,
    SystemMetrics,
    ErrorLog,
    Dashboard,
    DashboardWidget,
    AlertNotificationConfig
)

User = get_user_model()

class MonitoringAPITests(TestCase):
    def setUp(self):
        """测试前的准备工作"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

        # 创建测试数据
        self.alert_rule = AlertRule.objects.create(
            name='Test Alert Rule',
            description='Test Description',
            metric_type='cpu_usage',
            operator='gt',
            threshold=90.0,
            alert_level='warning',
            created_by=self.user
        )

        self.system_metrics = SystemMetrics.objects.create(
            metric_type='cpu_usage',
            value=95.0
        )

        self.alert_history = AlertHistory.objects.create(
            rule=self.alert_rule,
            status='active',
            metric_value=95.0,
            created_by=self.user
        )

        self.error_log = ErrorLog.objects.create(
            error_type='TestError',
            error_message='Test error message',
            severity='error',
            source='test_source',
            created_by=self.user
        )

        self.dashboard = Dashboard.objects.create(
            name='Test Dashboard',
            description='Test Dashboard Description',
            created_by=self.user
        )

        self.dashboard_widget = DashboardWidget.objects.create(
            name='Test Widget',
            dashboard=self.dashboard,
            widget_type='chart'
        )

        self.notification_config = AlertNotificationConfig.objects.create(
            name='Test Notification',
            notification_type='email',
            config={'email': 'test@example.com'},
            alert_levels=['warning', 'critical'],
            user=self.user
        )

    def test_alert_rule_list(self):
        """测试告警规则列表接口"""
        url = reverse('alert-rules-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_alert_rule_detail(self):
        """测试告警规则详情接口"""
        url = reverse('alert-rules-detail', args=[self.alert_rule.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Alert Rule')

    def test_alert_history_list(self):
        """测试告警历史列表接口"""
        url = reverse('alert-history-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_system_metrics_list(self):
        """测试系统指标列表接口"""
        url = reverse('system-metrics-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_error_log_list(self):
        """测试错误日志列表接口"""
        url = reverse('error-logs-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_dashboard_list(self):
        """测试仪表盘列表接口"""
        url = reverse('dashboards-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_dashboard_widget_list(self):
        """测试仪表盘小部件列表接口"""
        url = reverse('dashboard-widgets-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_notification_config_list(self):
        """测试告警通知配置列表接口"""
        url = reverse('alert-notification-config-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_alert_rule_create(self):
        """测试创建告警规则"""
        url = reverse('alert-rules-list')
        data = {
            'name': 'New Alert Rule',
            'description': 'New Description',
            'metric_type': 'memory_usage',
            'operator': 'gt',
            'threshold': 85.0,
            'alert_level': 'warning'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AlertRule.objects.count(), 2)

    def test_alert_rule_update(self):
        """测试更新告警规则"""
        url = reverse('alert-rules-detail', args=[self.alert_rule.id])
        data = {
            'name': 'Updated Alert Rule',
            'threshold': 95.0
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.alert_rule.refresh_from_db()
        self.assertEqual(self.alert_rule.name, 'Updated Alert Rule')
        self.assertEqual(self.alert_rule.threshold, 95.0)

    def test_alert_rule_delete(self):
        """测试删除告警规则"""
        url = reverse('alert-rules-detail', args=[self.alert_rule.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(AlertRule.objects.count(), 0)

    def test_error_log_create(self):
        """测试创建错误日志"""
        url = reverse('error-logs-list')
        data = {
            'error_type': 'NewError',
            'error_message': 'New error message',
            'severity': 'critical',
            'source': 'test'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ErrorLog.objects.count(), 2)

    def test_dashboard_create(self):
        """测试创建仪表盘"""
        url = reverse('dashboards-list')
        data = {
            'name': 'New Dashboard',
            'description': 'New Dashboard Description'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Dashboard.objects.count(), 2)

    def test_notification_config_create(self):
        """测试创建告警通知配置"""
        url = reverse('alert-notification-config-list')
        data = {
            'name': 'New Notification',
            'notification_type': 'webhook',
            'config': {'url': 'http://example.com/webhook'},
            'alert_levels': ['critical']
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AlertNotificationConfig.objects.count(), 2)