import json
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate
from django.utils import timezone
from asgiref.sync import sync_to_async
from custom_auth.models import User
from monitoring.models import (
    AlertRule, AlertHistory, SystemMetrics,
    ErrorLog, AlertNotificationConfig
)
import uuid

@pytest.mark.django_db
class TestMonitorIntegration:
    """TC-INT-MONITOR-001: 监控服务集成测试"""

    @pytest.fixture
    def api_client(self):
        factory = APIRequestFactory()
        factory.default_format = 'json'
        return factory

    @pytest.fixture
    async def test_user(self):
        username = f"test_user_{uuid.uuid4().hex[:8]}"
        return await sync_to_async(User.objects.create_user)(
            username=username,
            email=f"{username}@example.com",
            password="test_password"
        )

    @pytest.fixture
    async def test_rule(self, test_user):
        user = await test_user
        return await sync_to_async(AlertRule.objects.create)(
            name='CPU使用率告警',
            metric_type='cpu_usage',
            operator='gt',
            threshold=90,
            duration=300,
            alert_level='critical',
            is_enabled=True,
            created_by=user
        )

    @pytest.mark.asyncio
    async def test_system_metrics_collection(self, api_client, test_user):
        """测试系统指标收集功能"""
        try:
            # 清理已存在的测试数据
            await sync_to_async(SystemMetrics.objects.all().delete)()
            
            url = reverse('api:monitoring:system-metrics-list')
            request = api_client.get(url)
            force_authenticate(request, user=await test_user)
            
            # 创建测试数据
            required_metrics = ['cpu_usage', 'memory_usage', 'disk_usage', 'network_in']
            for metric_type in required_metrics:
                metric_data = {
                    'metric_type': metric_type,
                    'value': 50.0,
                    'metadata': {
                        'host': 'test-server',
                        'timestamp': timezone.now().isoformat()
                    }
                }
                await sync_to_async(SystemMetrics.objects.create)(**metric_data)
            
            # 验证指标存储
            stored_metrics = await sync_to_async(SystemMetrics.objects.filter(metric_type__in=required_metrics).count)()
            assert stored_metrics == len(required_metrics)
            
            # 验证API响应
            from monitoring.views import SystemMetricsViewSet
            view = SystemMetricsViewSet.as_view({'get': 'list'})
            response = view(request)
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == len(required_metrics)

        except Exception as e:
            pytest.fail(f"测试系统指标收集失败: {str(e)}")

    @pytest.mark.asyncio
    async def test_alert_rule_management(self, api_client, test_user):
        """测试告警规则管理功能"""
        try:
            # 等待获取测试用户
            user = await test_user
            
            url = reverse('api:monitoring:alert-rules-list')
            
            # 创建告警规则
            rule_data = {
                'name': 'Test CPU Alert',
                'description': 'Alert when CPU usage is high',
                'metric_type': 'cpu_usage',
                'operator': 'gt',
                'threshold': 90.0,
                'duration': 300,
                'alert_level': 'critical',
                'is_enabled': True
            }
            
            request = api_client.post(
                url, 
                data=json.dumps(rule_data),
                content_type='application/json'
            )
            force_authenticate(request, user=user)
            
            from monitoring.views import AlertRuleViewSet
            view = AlertRuleViewSet.as_view({'post': 'create'})
            response = view(request)
            
            assert response.status_code == status.HTTP_201_CREATED
            rule_id = response.data['id']
            
            # 获取规则列表
            request = api_client.get(url)
            force_authenticate(request, user=user)
            view = AlertRuleViewSet.as_view({'get': 'list'})
            response = view(request)
            
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) > 0
            
            # 禁用规则
            disable_url = reverse('api:monitoring:alert-rule-disable', args=[rule_id])
            request = api_client.post(disable_url)
            force_authenticate(request, user=user)
            view = AlertRuleViewSet.as_view({'post': 'disable'})
            response = view(request, pk=rule_id)
            
            assert response.status_code == status.HTTP_200_OK
            assert not response.data['is_enabled']

        except Exception as e:
            pytest.fail(f"测试告警规则管理失败: {str(e)}")

    @pytest.mark.asyncio
    async def test_alert_history_management(self, api_client, test_user):
        """测试告警历史记录管理功能"""
        try:
            user = await test_user
            
            # 首先创建一个监控规则
            rule = await sync_to_async(AlertRule.objects.create)(
                name='High CPU Usage Alert',
                description='CPU usage exceeded threshold',
                metric_type='cpu_usage',
                operator='gt',
                threshold=90.0,
                duration=300,
                alert_level='critical',
                is_enabled=True,
                created_by=user
            )
            
            # 创建告警记录
            alert = await sync_to_async(AlertHistory.objects.create)(
                rule=rule,
                metric_value=95.5,
                status='active',
                message='CPU usage exceeded threshold (95.5% > 90.0%)',
                created_by=user
            )
            
            # 获取告警历史
            url = reverse('api:monitoring:alert-history-list')
            request = api_client.get(url)
            force_authenticate(request, user=user)
            
            from monitoring.views import AlertHistoryViewSet
            view = AlertHistoryViewSet.as_view({'get': 'list'})
            response = view(request)
            
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) > 0
            
            # 获取特定告警详情
            detail_url = reverse('api:monitoring:alert-history-detail', args=[alert.id])
            request = api_client.get(detail_url)
            force_authenticate(request, user=user)
            view = AlertHistoryViewSet.as_view({'get': 'retrieve'})
            response = view(request, pk=alert.id)
            
            assert response.status_code == status.HTTP_200_OK
            assert response.data['status'] == 'active'
            
            # 解决告警
            resolve_url = reverse('api:monitoring:alert-history-resolve', args=[alert.id])
            request = api_client.post(resolve_url)
            force_authenticate(request, user=user)
            view = AlertHistoryViewSet.as_view({'post': 'resolve'})
            response = view(request, pk=alert.id)
            
            assert response.status_code == status.HTTP_200_OK
            assert response.data['status'] == 'resolved'

        except Exception as e:
            pytest.fail(f"测试告警历史记录管理失败: {str(e)}")

    @pytest.mark.asyncio
    async def test_system_health_check(self, api_client, test_user):
        """测试系统健康状态检查功能"""
        try:
            user = await test_user
            
            # 获取系统健康状态
            url = reverse('api:monitoring:system-status-health')
            request = api_client.get(url)
            force_authenticate(request, user=user)
            
            from monitoring.views import SystemStatusViewSet
            view = SystemStatusViewSet.as_view({'get': 'health'})
            response = view(request)
            
            assert response.status_code == status.HTTP_200_OK
            assert 'status' in response.data
            assert response.data['status'] == 'ok'
            
            # 获取系统概览
            overview_url = reverse('api:monitoring:system-status-overview')
            request = api_client.get(overview_url)
            force_authenticate(request, user=user)
            
            view = SystemStatusViewSet.as_view({'get': 'overview'})
            response = view(request)
            
            assert response.status_code == status.HTTP_200_OK
            assert 'memory_usage' in response.data
            assert 'cpu_usage' in response.data
            assert 'disk_usage' in response.data
            assert 'services' in response.data

        except Exception as e:
            pytest.fail(f"测试系统健康状态检查失败: {str(e)}")

    @pytest.mark.asyncio
    async def test_error_log_management(self, api_client, test_user):
        """测试错误日志管理功能"""
        try:
            user = await test_user

            # 清理所有现有的错误日志
            await sync_to_async(ErrorLog.objects.all().delete)()

            # 创建一些测试数据
            await sync_to_async(ErrorLog.objects.create)(
                message='Test error',
                severity='ERROR',
                source='test_source',
                created_by=user
            )
            await sync_to_async(ErrorLog.objects.create)(
                message='Test warning',
                severity='WARNING',
                source='test_source',
                created_by=user
            )
            await sync_to_async(ErrorLog.objects.create)(
                message='Test critical',
                severity='CRITICAL',
                source='test_source',
                created_by=user
            )

            # 获取错误日志列表
            url = reverse('api:monitoring:error-logs-list')
            request = api_client.get(url)
            force_authenticate(request, user=user)

            from monitoring.views import ErrorLogViewSet
            view = ErrorLogViewSet.as_view({'get': 'list'})
            response = view(request)

            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 3

            # 获取统计数据
            stats_url = reverse('api:monitoring:error-logs-statistics')
            request = api_client.get(stats_url)
            force_authenticate(request, user=user)

            view = ErrorLogViewSet.as_view({'get': 'statistics'})
            response = view(request)

            assert response.status_code == status.HTTP_200_OK
            assert 'statistics' in response.data
            assert response.data['statistics']['total_count'] == 3
            assert 'severity_distribution' in response.data['statistics']
            assert 'source_distribution' in response.data['statistics']

        except Exception as e:
            pytest.fail(f"测试错误日志管理失败: {str(e)}") 