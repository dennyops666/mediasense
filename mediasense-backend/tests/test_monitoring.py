import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.utils import timezone
from monitoring.models import (
    SystemMetrics,
    AlertRule,
    AlertHistory,
    MonitoringVisualization,
    ErrorLog,
    AlertNotificationConfig
)

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def test_user():
    return User.objects.create_user(
        username='testuser',
        password='testpass',
        email='test@example.com'
    )

@pytest.mark.django_db
def test_system_status_overview(api_client, test_user):
    """测试系统状态概览"""
    api_client.force_authenticate(user=test_user)
    url = reverse('api:monitoring:system-status-overview')
    response = api_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert 'status' in response.data
    assert 'last_check' in response.data
    assert 'memory_usage' in response.data
    assert 'services' in response.data
    
    assert isinstance(response.data['memory_usage'], dict)
    assert 'total' in response.data['memory_usage']
    assert 'used' in response.data['memory_usage']
    assert 'free' in response.data['memory_usage']

@pytest.mark.django_db
def test_create_visualization(api_client, test_user):
    """测试创建可视化"""
    api_client.force_authenticate(user=test_user)
    url = reverse('api:monitoring:visualization-list')
    data = {
        'name': 'CPU使用率',
        'description': 'CPU使用率监控图表',
        'chart_type': 'line',
        'metric_type': 'cpu_usage',
        'time_range': 60,
        'interval': 5,
        'warning_threshold': 80,
        'critical_threshold': 90,
        'is_active': True,
        'refresh_interval': 300
    }
    response = api_client.post(url, data)
    
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['name'] == data['name']

@pytest.mark.django_db
def test_create_alert_rule(api_client, test_user):
    """测试创建告警规则"""
    api_client.force_authenticate(user=test_user)
    url = reverse('api:monitoring:alert-rules-list')
    data = {
        'name': 'CPU告警',
        'description': 'CPU使用率超过90%告警',
        'metric_type': 'cpu_usage',
        'operator': 'gt',
        'threshold': 90,
        'duration': 300,
        'alert_level': 'critical',
        'is_enabled': True
    }
    response = api_client.post(url, data)
    
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['name'] == data['name']

@pytest.mark.django_db
def test_create_dashboard(api_client, test_user):
    """测试创建仪表板"""
    api_client.force_authenticate(user=test_user)
    url = reverse('api:monitoring:dashboard-list')
    data = {
        'name': '系统监控',
        'description': '系统监控仪表板',
        'layout_type': 'grid',
        'is_default': True
    }
    response = api_client.post(url, data)
    
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['name'] == data['name']

@pytest.mark.django_db
def test_create_dashboard_widget(api_client, test_user):
    """测试创建仪表板组件"""
    api_client.force_authenticate(user=test_user)
    
    # 先创建一个仪表板
    dashboard_url = reverse('api:monitoring:dashboard-list')
    dashboard_data = {
        'name': '系统监控',
        'description': '系统监控仪表板',
        'layout_type': 'grid',
        'is_default': True
    }
    dashboard_response = api_client.post(dashboard_url, dashboard_data, format='json')
    assert dashboard_response.status_code == status.HTTP_201_CREATED
    
    # 创建仪表板组件
    url = reverse('api:monitoring:dashboard-widgets-list')
    data = {
        'dashboard': dashboard_response.data['id'],
        'name': '测试组件',
        'widget_type': 'chart',
        'config': {
            'metric_type': 'cpu_usage',
            'duration': 3600,
            'refresh_interval': 300
        },
        'position': {'x': 0, 'y': 0, 'w': 6, 'h': 4},
        'is_visible': True
    }
    response = api_client.post(url, data, format='json')
    
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['name'] == data['name']
    assert response.data['widget_type'] == data['widget_type']

@pytest.mark.django_db
def test_create_alert_notification(api_client, test_user):
    """测试创建告警通知配置"""
    api_client.force_authenticate(user=test_user)
    url = reverse('api:monitoring:alert-notifications-list')
    data = {
        'name': '测试通知',
        'notification_type': 'email',
        'config': {
            'email': 'test@example.com',
            'template': 'default'
        },
        'alert_levels': ['warning', 'critical'],
        'is_active': True
    }
    response = api_client.post(url, data, format='json')
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['name'] == data['name']
    assert response.data['notification_type'] == data['notification_type']

@pytest.mark.django_db
def test_create_system_metrics(api_client, test_user):
    """测试创建系统指标"""
    api_client.force_authenticate(user=test_user)
    url = reverse('api:monitoring:system-metrics-list')
    data = {
        'metric_type': 'cpu_usage',
        'value': 85.5,
        'metadata': {
            'host': 'server-01',
            'process_count': 120
        }
    }
    response = api_client.post(url, data, format='json')
    
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['metric_type'] == data['metric_type']
    assert response.data['value'] == data['value']

@pytest.mark.django_db
def test_error_log_statistics(api_client, test_user):
    """测试错误日志统计"""
    api_client.force_authenticate(user=test_user)
    
    # 创建一些测试数据
    ErrorLog.objects.create(
        message='Test error',
        severity='ERROR',
        source='test_source',
        created_by=test_user
    )
    ErrorLog.objects.create(
        message='Test warning',
        severity='WARNING',
        source='test_source',
        created_by=test_user
    )
    
    url = reverse('api:monitoring:error-log-statistics')
    response = api_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data['error_count'] == 1
    assert response.data['warning_count'] == 1

@pytest.mark.django_db
def test_alert_rule_trigger(api_client, test_user):
    """测试告警规则触发"""
    api_client.force_authenticate(user=test_user)
    
    # 创建告警规则
    rule_url = reverse('api:monitoring:alert-rules-list')
    rule_data = {
        'name': 'CPU告警测试',
        'description': 'CPU使用率超过90%告警',
        'metric_type': 'cpu_usage',
        'operator': 'gt',
        'threshold': 90,
        'duration': 60,
        'alert_level': 'critical',
        'is_enabled': True
    }
    rule_response = api_client.post(rule_url, rule_data)
    assert rule_response.status_code == status.HTTP_201_CREATED
    
    # 创建超过阈值的系统指标
    metrics_url = reverse('api:monitoring:system-metrics-list')
    metrics_data = {
        'metric_type': 'cpu_usage',
        'value': 95.0
    }
    metrics_response = api_client.post(metrics_url, metrics_data)
    assert metrics_response.status_code == status.HTTP_201_CREATED
    
    # 检查是否生成告警历史
    history_url = reverse('api:monitoring:alert-history-list')
    history_response = api_client.get(history_url)
    assert history_response.status_code == status.HTTP_200_OK
    assert len(history_response.data) > 0

@pytest.mark.django_db
def test_alert_notification_config(api_client, test_user):
    """测试告警通知配置"""
    api_client.force_authenticate(user=test_user)
    url = reverse('api:monitoring:alert-notifications-list')
    data = {
        'name': '邮件通知测试',
        'notification_type': 'email',
        'config': {
            'email': 'test@example.com',
            'template': 'default'
        },
        'alert_levels': ['warning', 'critical'],
        'is_active': True
    }
    response = api_client.post(url, data, format='json')
    
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['name'] == data['name']
    assert response.data['notification_type'] == data['notification_type']
    assert response.data['is_active'] == True

    # 测试发送测试通知
    notification_id = response.data['id']
    test_url = reverse('api:monitoring:alert-notifications-test', kwargs={'pk': notification_id})
    test_response = api_client.post(test_url)
    assert test_response.status_code == status.HTTP_200_OK