import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from monitoring.models import (
    MonitoringVisualization,
    AlertRule,
    AlertHistory,
    AlertNotificationConfig,
    Dashboard,
    DashboardWidget
)
from tests.factories import UserFactory

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def test_user():
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )

@pytest.mark.django_db
class TestMonitoringAPI:
    """监控模块API测试"""

    def test_system_status_overview(self, api_client, test_user):
        """测试系统状态概览"""
        login_url = reverse('api:auth:token_obtain')
        url = reverse('api:monitoring:system-status-overview')
        
        # 登录获取 token
        login_response = api_client.post(login_url, {
            'username': test_user.username,
            'password': 'testpass123'
        })
        access_token = login_response.data['access']
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "healthy"
        assert 'memory_usage' in response.data
        assert 'disk_usage' in response.data

    def test_create_visualization(self, api_client, test_user):
        """测试创建可视化"""
        login_url = reverse('api:auth:token_obtain')
        url = reverse('api:monitoring:visualization-list')
        
        # 登录获取 token
        login_response = api_client.post(login_url, {
            'username': test_user.username,
            'password': 'testpass123'
        })
        access_token = login_response.data['access']
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        data = {
            'title': 'CPU Usage Over Time',
            'chart_type': 'line',
            'metric': 'cpu_usage',
            'time_range': '24h'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == data['title']

    def test_create_alert_rule(self, api_client, test_user):
        """测试创建告警规则"""
        login_url = reverse('api:auth:token_obtain')
        url = reverse('api:monitoring:alert-rules-list')
        
        # 登录获取 token
        login_response = api_client.post(login_url, {
            'username': test_user.username,
            'password': 'testpass123'
        })
        access_token = login_response.data['access']
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        data = {
            'name': 'High CPU Usage Alert',
            'metric': 'cpu_usage',
            'condition': 'gt',
            'threshold': 90,
            'duration': '5m'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == data['name']

    def test_create_dashboard(self, api_client, test_user):
        """测试创建仪表盘"""
        login_url = reverse('api:auth:token_obtain')
        url = reverse('api:monitoring:visualization-list')
        
        # 登录获取 token
        login_response = api_client.post(login_url, {
            'username': test_user.username,
            'password': 'testpass123'
        })
        access_token = login_response.data['access']
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        data = {
            'title': 'System Overview',
            'description': 'System performance metrics dashboard'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == data['title']

    def test_create_dashboard_widget(self, api_client, test_user):
        """测试创建仪表盘小部件"""
        login_url = reverse('api:auth:token_obtain')
        dashboard_url = reverse('api:monitoring:visualization-list')
        
        # 登录获取 token
        login_response = api_client.post(login_url, {
            'username': test_user.username,
            'password': 'testpass123'
        })
        access_token = login_response.data['access']
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # 创建仪表板
        dashboard_data = {
            'title': 'System Overview',
            'description': 'System performance metrics dashboard'
        }
        dashboard_response = api_client.post(dashboard_url, dashboard_data)
        dashboard_id = dashboard_response.data['id']
        
        # 创建小部件
        widget_url = reverse('api:monitoring:dashboard-widgets-list', args=[dashboard_id])
        widget_data = {
            'title': 'CPU Usage Widget',
            'widget_type': 'gauge',
            'metric': 'cpu_usage',
            'position': {'x': 0, 'y': 0, 'w': 6, 'h': 4}
        }
        response = api_client.post(widget_url, widget_data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == widget_data['title']

    def test_create_alert_notification(self, api_client, test_user):
        """测试创建告警通知配置"""
        login_url = reverse('api:auth:token_obtain')
        url = reverse('api:monitoring:alert-notifications-list')
        
        # 登录获取 token
        login_response = api_client.post(login_url, {
            'username': test_user.username,
            'password': 'testpass123'
        })
        access_token = login_response.data['access']
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        data = {
            'name': 'Email Notification',
            'type': 'email',
            'config': {
                'recipients': ['admin@example.com'],
                'subject_template': 'Alert: {alert_name}',
                'body_template': 'Alert {alert_name} was triggered at {timestamp}'
            }
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == data['name'] 