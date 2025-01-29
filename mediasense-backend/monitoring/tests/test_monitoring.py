from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch
from monitoring.models import MonitoringVisualization, SystemMetrics, AlertRule
from monitoring.services import MonitoringService


class MonitoringTests(TestCase):
    """监控模块核心功能测试"""

    def setUp(self):
        """测试数据初始化"""
        # 清除所有现有的告警规则
        AlertRule.objects.all().delete()
        
        # 创建测试用的系统指标数据
        self.metrics_data = [
            {'metric_type': SystemMetrics.MetricType.CPU_USAGE, 'value': 75.5},
            {'metric_type': SystemMetrics.MetricType.MEMORY_USAGE, 'value': 80.2},
            {'metric_type': SystemMetrics.MetricType.DISK_USAGE, 'value': 65.8},
            {'metric_type': SystemMetrics.MetricType.NETWORK_IN, 'value': 1024},
            {'metric_type': SystemMetrics.MetricType.NETWORK_OUT, 'value': 2048},
        ]
        self.metrics = []
        for data in self.metrics_data:
            metric = SystemMetrics.objects.create(**data)
            self.metrics.append(metric)

        # 创建测试用的可视化配置
        self.visualization = MonitoringVisualization.objects.create(
            name="CPU使用率监控",
            visualization_type=MonitoringVisualization.ChartType.LINE_CHART,
            metric_type=SystemMetrics.MetricType.CPU_USAGE,
            config={'time_range': 30}  # 30分钟
        )

        # 创建测试用的告警规则
        self.alert_rule = AlertRule.objects.create(
            name="CPU使用率过高告警",
            metric_type=SystemMetrics.MetricType.CPU_USAGE,
            operator=AlertRule.Operator.GT,
            threshold=90.0,
            alert_level=AlertRule.AlertLevel.WARNING
        )

    def test_system_metrics_model(self):
        """测试系统指标模型"""
        # 验证初始测试数据是否正确创建
        self.assertEqual(SystemMetrics.objects.count(), len(self.metrics_data))
        
        # 验证各类型指标是否都存在
        metric_types = set(SystemMetrics.objects.values_list('metric_type', flat=True))
        expected_types = {data['metric_type'] for data in self.metrics_data}
        self.assertEqual(metric_types, expected_types)

    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('psutil.net_io_counters')
    def test_collect_system_metrics(self, mock_net, mock_disk, mock_memory, mock_cpu):
        """测试系统指标收集功能"""
        # 模拟系统指标数据
        mock_cpu.return_value = 70.0
        mock_memory.return_value.percent = 75.0
        mock_disk.return_value.percent = 60.0
        mock_net.return_value.bytes_recv = 1024
        mock_net.return_value.bytes_sent = 2048

        # 执行指标收集
        initial_count = SystemMetrics.objects.count()
        MonitoringService.collect_system_metrics()

        # 验证是否正确保存了所有类型的指标
        self.assertEqual(SystemMetrics.objects.count(), initial_count + 5)
        
        # 验证CPU指标是否正确保存
        latest_cpu = SystemMetrics.objects.filter(
            metric_type=SystemMetrics.MetricType.CPU_USAGE
        ).latest('timestamp')
        self.assertEqual(latest_cpu.value, 70.0)

    def test_visualization_data_generation(self):
        """测试可视化数据生成功能"""
        # 测试折线图数据生成
        line_data = MonitoringService.generate_visualization_data(self.visualization)
        self.assertIn('timestamps', line_data)
        self.assertIn('values', line_data)
        self.assertIn('metric_type', line_data)
        self.assertEqual(len(line_data['timestamps']), len(line_data['values']))

        # 测试仪表盘数据生成
        self.visualization.visualization_type = MonitoringVisualization.ChartType.GAUGE
        self.visualization.save()
        gauge_data = MonitoringService.generate_visualization_data(self.visualization)
        self.assertIn('value', gauge_data)
        self.assertIn('metric_type', gauge_data)
        self.assertIn('timestamp', gauge_data)

    def test_alert_rule_check(self):
        """测试告警规则检查功能"""
        # 创建一个正常值的指标（不触发告警）
        SystemMetrics.objects.create(
            metric_type=SystemMetrics.MetricType.CPU_USAGE,
            value=85.0
        )
        normal_alerts = MonitoringService.check_alerts()
        self.assertEqual(len(normal_alerts), 0)

        # 创建一个超过阈值的指标（触发告警）
        SystemMetrics.objects.create(
            metric_type=SystemMetrics.MetricType.CPU_USAGE,
            value=95.0
        )
        alerts = MonitoringService.check_alerts()
        self.assertEqual(len(alerts), 1)
        
        alert = alerts[0]
        self.assertEqual(alert['rule_name'], self.alert_rule.name)
        self.assertEqual(alert['metric_type'], self.alert_rule.get_metric_type_display())
        self.assertEqual(alert['alert_level'], self.alert_rule.alert_level)
        self.assertEqual(alert['current_value'], 95.0)
        self.assertEqual(alert['threshold'], 90.0)