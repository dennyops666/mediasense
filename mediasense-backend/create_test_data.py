import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediasense.settings')
django.setup()

from django.utils import timezone
from datetime import timedelta
from monitoring.models import (
    SystemMetrics,
    AlertRule,
    AlertHistory,
    MonitoringVisualization,
    ErrorLog,
    Dashboard,
    DashboardWidget,
    AlertNotificationConfig
)

# 创建系统指标数据
def create_system_metrics():
    metrics_types = ['cpu_usage', 'memory_usage', 'disk_usage', 'network_in', 'network_out']
    for metric_type in metrics_types:
        for i in range(5):
            SystemMetrics.objects.create(
                metric_type=metric_type,
                value=float(f"{(i + 1) * 10}.{i}"),
                timestamp=timezone.now() - timedelta(hours=i),
                metadata={'host': 'server-01', 'environment': 'production'}
            )
    print("系统指标数据创建完成")

# 创建告警规则
def create_alert_rules():
    rules = [
        {
            'name': 'CPU 使用率过高',
            'description': 'CPU 使用率超过 90%',
            'metric_type': 'cpu_usage',
            'operator': 'gt',
            'threshold': 90.0,
            'duration': 300,
            'alert_level': 'critical',
            'is_enabled': True
        },
        {
            'name': '内存使用率过高',
            'description': '内存使用率超过 85%',
            'metric_type': 'memory_usage',
            'operator': 'gt',
            'threshold': 85.0,
            'duration': 300,
            'alert_level': 'warning',
            'is_enabled': True
        },
        {
            'name': '磁盘空间不足',
            'description': '磁盘使用率超过 95%',
            'metric_type': 'disk_usage',
            'operator': 'gt',
            'threshold': 95.0,
            'duration': 300,
            'alert_level': 'critical',
            'is_enabled': True
        }
    ]
    
    for rule in rules:
        AlertRule.objects.create(**rule)
    print("告警规则创建完成")

# 创建告警历史
def create_alert_history():
    statuses = ['active', 'resolved', 'acknowledged']
    for i in range(5):
        AlertHistory.objects.create(
            rule=AlertRule.objects.first(),
            status=statuses[i % 3],
            message=f'检测到系统指标异常 #{i+1}',
            metric_value=95.0 + i,
            triggered_at=timezone.now() - timedelta(hours=i),
            resolved_at=timezone.now() - timedelta(hours=i-1) if i > 0 else None,
            note=f'自动恢复 #{i}' if i > 0 else None
        )
    print("告警历史创建完成")

# 创建监控可视化
def create_visualizations():
    viz_types = ['line_chart', 'gauge']
    metric_types = ['cpu_usage', 'memory_usage', 'disk_usage', 'network_in']
    for i, (viz_type, metric_type) in enumerate(zip(viz_types * 2, metric_types)):
        MonitoringVisualization.objects.create(
            name=f'{viz_type.replace("_", " ").title()} #{i+1}',
            description=f'显示{metric_type}的{viz_type}',
            visualization_type=viz_type,
            metric_type=metric_type,
            config={'time_range': '24h', 'refresh_interval': 60},
            is_active=True
        )
    print("监控可视化创建完成")

# 创建错误日志
def create_error_logs():
    severities = ['info', 'warning', 'error', 'critical']
    sources = ['application', 'database', 'system', 'network']
    for i in range(10):
        ErrorLog.objects.create(
            error_type=f'TestError{i+1}',
            error_message=f'测试错误消息 #{i+1}',
            severity=severities[i % 4],
            source=sources[i % 4],
            stack_trace=f'Traceback (most recent call last):\n  File "test.py", line {i+1}\n    raise Exception("测试异常")\nException: 测试异常'
        )
    print("错误日志创建完成")

# 创建仪表板
def create_dashboards():
    dashboard = Dashboard.objects.create(
        name='系统监控仪表板',
        description='显示系统关键指标的仪表板',
        layout_type='grid',
        layout={'columns': 2, 'rows': 2},
        is_default=True
    )
    
    # 创建仪表板组件
    for i, viz in enumerate(MonitoringVisualization.objects.all()):
        DashboardWidget.objects.create(
            dashboard=dashboard,
            name=f'Widget #{i+1}',
            widget_type='chart',
            visualization=viz,
            config={'refresh_interval': 60},
            position={'x': i % 2, 'y': i // 2},
            is_visible=True
        )
    print("仪表板和组件创建完成")

# 创建告警通知配置
def create_alert_notification_configs():
    notification_types = ['email', 'sms', 'webhook', 'wechat']
    for notification_type in notification_types:
        AlertNotificationConfig.objects.create(
            name=f'{notification_type.title()} 通知',
            notification_type=notification_type,
            config={'endpoint': f'http://example.com/{notification_type}'},
            alert_levels=['warning', 'critical'],
            is_active=True,
            notification_interval=300,
            recovery_notify=True
        )
    print("告警通知配置创建完成")

if __name__ == '__main__':
    # 清理现有数据
    SystemMetrics.objects.all().delete()
    AlertRule.objects.all().delete()
    AlertHistory.objects.all().delete()
    MonitoringVisualization.objects.all().delete()
    ErrorLog.objects.all().delete()
    Dashboard.objects.all().delete()
    DashboardWidget.objects.all().delete()
    AlertNotificationConfig.objects.all().delete()
    print("现有数据清理完成")
    
    # 创建新数据
    create_system_metrics()
    create_alert_rules()
    create_alert_history()
    create_visualizations()
    create_error_logs()
    create_dashboards()
    create_alert_notification_configs()
    print("所有测试数据创建完成") 