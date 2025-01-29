from django.core.management.base import BaseCommand
from django.utils import timezone
from monitoring.models import (
    AlertRule, AlertNotificationConfig, Dashboard,
    DashboardWidget, SystemMetrics
)
import json

class Command(BaseCommand):
    help = '初始化监控模块的基础数据'

    def handle(self, *args, **kwargs):
        self.stdout.write('开始初始化监控模块基础数据...')

        try:
            # 创建基础告警规则
            self.create_basic_alert_rules()
            
            # 创建告警通知配置
            self.create_notification_configs()
            
            # 创建默认仪表盘
            self.create_default_dashboard()

            self.stdout.write(self.style.SUCCESS('监控模块基础数据初始化完成！'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'初始化过程中发生错误: {str(e)}'))
            raise

    def create_basic_alert_rules(self):
        """创建基础告警规则"""
        alert_rules = [
            {
                'name': 'CPU使用率告警',
                'description': 'CPU使用率超过80%时触发告警',
                'metric_type': 'cpu_usage',
                'operator': 'gt',
                'threshold': 80.0,
                'alert_level': 'warning',
                'is_enabled': True,
            },
            {
                'name': '内存使用率告警',
                'description': '内存使用率超过85%时触发告警',
                'metric_type': 'memory_usage',
                'operator': 'gt',
                'threshold': 85.0,
                'alert_level': 'warning',
                'is_enabled': True,
            },
            {
                'name': '磁盘使用率告警',
                'description': '磁盘使用率超过90%时触发严重告警',
                'metric_type': 'disk_usage',
                'operator': 'gt',
                'threshold': 90.0,
                'alert_level': 'critical',
                'is_enabled': True,
            }
        ]

        for rule_data in alert_rules:
            try:
                rule, created = AlertRule.objects.get_or_create(
                    name=rule_data['name'],
                    defaults=rule_data
                )
                self.stdout.write(f"告警规则 '{rule.name}' {'已创建' if created else '已存在'}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"创建告警规则 '{rule_data['name']}' 失败: {str(e)}"))
                raise

        self.stdout.write('基础告警规则创建完成')

    def create_notification_configs(self):
        """创建告警通知配置"""
        notification_configs = [
            {
                'name': '默认邮件通知',
                'notification_type': 'email',
                'config': json.dumps({
                    'recipients': ['admin@example.com'],
                }),
                'alert_levels': ['warning', 'critical'],
                'is_active': True,
            },
            {
                'name': '严重告警通知',
                'notification_type': 'email',
                'config': json.dumps({
                    'recipients': ['admin@example.com', 'emergency@example.com'],
                }),
                'alert_levels': ['critical'],
                'is_active': True,
            }
        ]

        for config_data in notification_configs:
            try:
                config, created = AlertNotificationConfig.objects.get_or_create(
                    name=config_data['name'],
                    defaults=config_data
                )
                self.stdout.write(f"通知配置 '{config.name}' {'已创建' if created else '已存在'}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"创建通知配置 '{config_data['name']}' 失败: {str(e)}"))
                raise

        self.stdout.write('告警通知配置创建完成')

    def create_default_dashboard(self):
        """创建默认仪表盘"""
        try:
            # 创建主仪表盘
            dashboard, created = Dashboard.objects.get_or_create(
                name='系统监控概览',
                defaults={
                    'description': '显示系统关键指标的概览信息',
                    'layout': json.dumps({'type': 'grid', 'columns': 3})
                }
            )
            self.stdout.write(f"仪表盘 '{dashboard.name}' {'已创建' if created else '已存在'}")

            # 创建仪表盘组件
            widgets = [
                {
                    'name': 'CPU使用率趋势',
                    'visualization_type': 'line_chart',
                    'metric_type': 'cpu_usage',
                    'position': json.dumps({'x': 0, 'y': 0, 'w': 1, 'h': 1}),
                    'config': json.dumps({
                        'time_range': '24h',
                        'refresh_interval': 300
                    })
                },
                {
                    'name': '内存使用率趋势',
                    'visualization_type': 'line_chart',
                    'metric_type': 'memory_usage',
                    'position': json.dumps({'x': 1, 'y': 0, 'w': 1, 'h': 1}),
                    'config': json.dumps({
                        'time_range': '24h',
                        'refresh_interval': 300
                    })
                },
                {
                    'name': '磁盘使用率',
                    'visualization_type': 'gauge',
                    'metric_type': 'disk_usage',
                    'position': json.dumps({'x': 2, 'y': 0, 'w': 1, 'h': 1}),
                    'config': json.dumps({
                        'refresh_interval': 3600
                    })
                }
            ]

            for widget_data in widgets:
                try:
                    widget, created = DashboardWidget.objects.get_or_create(
                        name=widget_data['name'],
                        dashboard=dashboard,
                        defaults={
                            **widget_data,
                            'dashboard': dashboard
                        }
                    )
                    self.stdout.write(f"仪表盘组件 '{widget.name}' {'已创建' if created else '已存在'}")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"创建仪表盘组件 '{widget_data['name']}' 失败: {str(e)}"))
                    raise

            self.stdout.write('默认仪表盘创建完成')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"创建默认仪表盘失败: {str(e)}"))
            raise 