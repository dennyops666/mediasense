from datetime import timedelta
import asyncio

import psutil
import requests
from django.conf import settings
from django.db.models import Avg, Count, Max, Min, Sum
from django.utils import timezone

from .models import MonitoringVisualization, SystemMetrics, AlertRule


class MonitoringService:
    """监控服务类"""

    @staticmethod
    def collect_system_metrics():
        """收集系统指标"""
        metrics = []
        
        # CPU使用率
        cpu_usage = psutil.cpu_percent(interval=1)
        metrics.append(SystemMetrics(
            metric_type=SystemMetrics.MetricType.CPU_USAGE,
            value=cpu_usage
        ))

        # 内存使用率
        memory = psutil.virtual_memory()
        metrics.append(SystemMetrics(
            metric_type=SystemMetrics.MetricType.MEMORY_USAGE,
            value=memory.percent
        ))

        # 磁盘使用率
        disk = psutil.disk_usage('/')
        metrics.append(SystemMetrics(
            metric_type=SystemMetrics.MetricType.DISK_USAGE,
            value=disk.percent
        ))

        # 网络流量
        net_io = psutil.net_io_counters()
        metrics.append(SystemMetrics(
            metric_type=SystemMetrics.MetricType.NETWORK_IN,
            value=net_io.bytes_recv
        ))
        metrics.append(SystemMetrics(
            metric_type=SystemMetrics.MetricType.NETWORK_OUT,
            value=net_io.bytes_sent
        ))

        # 批量创建
        SystemMetrics.objects.bulk_create(metrics)

    @staticmethod
    def generate_visualization_data(visualization):
        """生成可视化数据"""
        end_time = timezone.now()
        time_range = visualization.config.get('time_range', 30)  # 默认30分钟
        start_time = end_time - timedelta(minutes=time_range)

        # 获取指定时间范围内的指标数据
        metrics = SystemMetrics.objects.filter(
            metric_type=visualization.metric_type,
            created_at__gte=start_time,
            created_at__lte=end_time
        ).order_by('created_at')

        if visualization.visualization_type == MonitoringVisualization.ChartType.LINE_CHART:
            # 生成折线图数据
            data = {
                'timestamps': [m.created_at.isoformat() for m in metrics],
                'values': [m.value for m in metrics],
                'metric_type': visualization.get_metric_type_display()
            }
        else:  # GAUGE
            # 获取最新值用于仪表盘显示
            latest_metric = metrics.last()
            data = {
                'value': latest_metric.value if latest_metric else 0,
                'metric_type': visualization.get_metric_type_display(),
                'created_at': latest_metric.created_at.isoformat() if latest_metric else end_time.isoformat()
            }

        # 更新缓存
        visualization.cached_data = data
        visualization.save()

        return data

    @staticmethod
    def check_alerts():
        """检查告警规则"""
        alerts = []
        rules = AlertRule.objects.filter(is_enabled=True)
        
        for rule in rules:
            # 获取最新的指标值
            latest_metric = SystemMetrics.objects.filter(
                metric_type=rule.metric_type
            ).order_by('-created_at').first()

            if not latest_metric:
                continue

            # 检查是否触发告警
            should_alert = False
            if rule.operator == AlertRule.Operator.GT and latest_metric.value > rule.threshold:
                should_alert = True
            elif rule.operator == AlertRule.Operator.LT and latest_metric.value < rule.threshold:
                should_alert = True

            if should_alert:
                alerts.append({
                    'rule_name': rule.name,
                    'metric_type': rule.get_metric_type_display(),
                    'current_value': latest_metric.value,
                    'threshold': rule.threshold,
                    'alert_level': rule.alert_level,
                    'created_at': latest_metric.created_at.isoformat()
                })

        return alerts

class MonitoringVisualizationService:
    """监控可视化服务类"""

    @staticmethod
    async def generate_chart_data(visualization):
        """生成图表数据"""
        # 计算时间范围
        end_time = timezone.now()
        start_time = end_time - timedelta(minutes=visualization.time_range)

        # 获取基础查询集
        queryset = SystemMetrics.objects.filter(
            metric_type=visualization.metric_type, created_at__gte=start_time, created_at__lte=end_time
        )

        # 准备聚合函数
        aggregation_funcs = {"avg": Avg, "max": Max, "min": Min, "sum": Sum, "count": Count}

        # 获取聚合函数
        agg_func = aggregation_funcs[visualization.aggregation_method]

        # 按时间间隔分组
        interval_seconds = visualization.interval

        # 构建时间序列数据
        data = []
        current_time = start_time
        while current_time <= end_time:
            next_time = current_time + timedelta(seconds=interval_seconds)

            # 查询当前时间段的数据
            period_data = await queryset.filter(created_at__gte=current_time, created_at__lt=next_time).aaggregate(
                value=agg_func("value")
            )

            # 添加数据点
            data.append({"created_at": current_time.isoformat(), "value": period_data["value"] or 0})

            current_time = next_time

        # 格式化图表数据
        if visualization.chart_type == MonitoringVisualization.ChartType.LINE:
            chart_data = {
                "xAxis": [item["created_at"] for item in data],
                "series": [{"name": visualization.get_metric_type_display(), "data": [item["value"] for item in data]}],
                "warning": visualization.warning_threshold,
                "critical": visualization.critical_threshold,
            }

        elif visualization.chart_type == MonitoringVisualization.ChartType.BAR:
            chart_data = {
                "xAxis": [item["created_at"] for item in data],
                "series": [{"name": visualization.get_metric_type_display(), "data": [item["value"] for item in data]}],
                "warning": visualization.warning_threshold,
                "critical": visualization.critical_threshold,
            }

        elif visualization.chart_type == MonitoringVisualization.ChartType.GAUGE:
            # 获取最新值
            latest_value = data[-1]["value"] if data else 0
            chart_data = {
                "value": latest_value,
                "warning": visualization.warning_threshold,
                "critical": visualization.critical_threshold,
            }

        elif visualization.chart_type == MonitoringVisualization.ChartType.PIE:
            # 计算各个区间的数据分布
            values = [item["value"] for item in data if item["value"] is not None]
            if not values:
                chart_data = {"series": []}
            else:
                min_value = min(values)
                max_value = max(values)
                interval = (max_value - min_value) / 5 if max_value > min_value else 1

                ranges = [(min_value + i * interval, min_value + (i + 1) * interval) for i in range(5)]

                distribution = []
                for start, end in ranges:
                    count = len([v for v in values if start <= v < end])
                    distribution.append({"name": f"{start:.2f} - {end:.2f}", "value": count})

                chart_data = {"series": [{"name": visualization.get_metric_type_display(), "data": distribution}]}

        # 更新缓存
        visualization.cached_data = chart_data
        visualization.last_generated = timezone.now()
        await visualization.asave()

        return chart_data

    @staticmethod
    async def get_chart_data(visualization):
        """获取图表数据，如果缓存有效则返回缓存数据"""
        # 检查缓存是否有效
        if (
            visualization.cached_data
            and visualization.last_generated
            and visualization.last_generated >= timezone.now() - timedelta(seconds=visualization.refresh_interval)
        ):
            return visualization.cached_data

        # 生成新数据
        return await MonitoringVisualizationService.generate_chart_data(visualization)

    @staticmethod
    async def get_available_fields():
        """获取可用的字段列表"""
        return {
            "metric_types": [
                {"value": choice[0], "label": choice[1]} for choice in MonitoringVisualization.MetricType.choices
            ],
            "chart_types": [
                {"value": choice[0], "label": choice[1]} for choice in MonitoringVisualization.ChartType.choices
            ],
            "aggregation_methods": [
                {"value": "avg", "label": "平均值"},
                {"value": "max", "label": "最大值"},
                {"value": "min", "label": "最小值"},
                {"value": "sum", "label": "求和"},
                {"value": "count", "label": "计数"},
            ],
        }
