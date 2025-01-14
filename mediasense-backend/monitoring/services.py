from datetime import timedelta

import psutil
import requests
from django.conf import settings
from django.db.models import Avg, Count, Max, Min, Sum
from django.utils import timezone

from .models import MonitoringVisualization, SystemMetrics


class MonitoringVisualizationService:
    """监控可视化服务类"""

    @staticmethod
    def generate_chart_data(visualization):
        """生成图表数据"""
        # 计算时间范围
        end_time = timezone.now()
        start_time = end_time - timedelta(minutes=visualization.time_range)

        # 获取基础查询集
        queryset = SystemMetrics.objects.filter(
            metric_type=visualization.metric_type, timestamp__gte=start_time, timestamp__lte=end_time
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
            period_data = queryset.filter(timestamp__gte=current_time, timestamp__lt=next_time).aggregate(
                value=agg_func("value")
            )

            # 添加数据点
            data.append({"timestamp": current_time.isoformat(), "value": period_data["value"] or 0})

            current_time = next_time

        # 格式化图表数据
        if visualization.chart_type == MonitoringVisualization.ChartType.LINE:
            chart_data = {
                "xAxis": [item["timestamp"] for item in data],
                "series": [{"name": visualization.get_metric_type_display(), "data": [item["value"] for item in data]}],
                "warning": visualization.warning_threshold,
                "critical": visualization.critical_threshold,
            }

        elif visualization.chart_type == MonitoringVisualization.ChartType.BAR:
            chart_data = {
                "xAxis": [item["timestamp"] for item in data],
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
        visualization.save()

        return chart_data

    @staticmethod
    def get_chart_data(visualization):
        """获取图表数据，如果缓存有效则返回缓存数据"""
        # 检查缓存是否有效
        if (
            visualization.cached_data
            and visualization.last_generated
            and visualization.last_generated >= timezone.now() - timedelta(seconds=visualization.refresh_interval)
        ):
            return visualization.cached_data

        # 生成新数据
        return MonitoringVisualizationService.generate_chart_data(visualization)

    @staticmethod
    def get_available_fields():
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
