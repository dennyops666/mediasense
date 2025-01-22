# Generated by Django 5.1.4 on 2025-01-22 10:18

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AlertNotificationConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, verbose_name="通知名称")),
                (
                    "notification_type",
                    models.CharField(
                        choices=[
                            ("email", "邮件通知"),
                            ("sms", "短信通知"),
                            ("webhook", "Webhook通知"),
                            ("dingtalk", "钉钉通知"),
                            ("wechat", "微信通知"),
                        ],
                        max_length=20,
                        verbose_name="通知类型",
                    ),
                ),
                ("config", models.JSONField(help_text="通知相关的配置信息", verbose_name="通知配置")),
                ("alert_levels", models.JSONField(help_text="接收哪些级别的告警", verbose_name="告警级别")),
                ("is_active", models.BooleanField(default=True, verbose_name="是否启用")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
                ("last_notified", models.DateTimeField(blank=True, null=True, verbose_name="上次通知时间")),
                ("notification_count", models.IntegerField(default=0, verbose_name="通知次数")),
                (
                    "user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="alert_notifications",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="用户",
                    ),
                ),
            ],
            options={
                "verbose_name": "告警通知配置",
                "verbose_name_plural": "告警通知配置",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="AlertRule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, verbose_name="规则名称")),
                ("description", models.TextField(blank=True, verbose_name="规则描述")),
                (
                    "metric_type",
                    models.CharField(
                        choices=[
                            ("cpu", "CPU使用率"),
                            ("memory", "内存使用率"),
                            ("disk", "磁盘使用率"),
                            ("network", "网络流量"),
                            ("api_latency", "API响应时间"),
                            ("error_rate", "错误率"),
                            ("request_count", "请求数"),
                            ("task_count", "任务数"),
                        ],
                        max_length=20,
                        verbose_name="监控指标",
                    ),
                ),
                (
                    "operator",
                    models.CharField(
                        choices=[
                            ("gt", "大于"),
                            ("lt", "小于"),
                            ("gte", "大于等于"),
                            ("lte", "小于等于"),
                            ("eq", "等于"),
                            ("neq", "不等于"),
                        ],
                        max_length=10,
                        verbose_name="比较运算符",
                    ),
                ),
                ("threshold", models.FloatField(verbose_name="阈值")),
                (
                    "duration",
                    models.IntegerField(
                        default=5, help_text="指标超过阈值持续n分钟后触发告警", verbose_name="持续时间(分钟)"
                    ),
                ),
                (
                    "alert_level",
                    models.CharField(
                        choices=[("info", "信息"), ("warning", "警告"), ("critical", "严重")],
                        default="warning",
                        max_length=20,
                        verbose_name="告警级别",
                    ),
                ),
                ("is_enabled", models.BooleanField(default=True, verbose_name="是否启用")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="alert_rules",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="创建者",
                    ),
                ),
            ],
            options={
                "verbose_name": "告警规则",
                "verbose_name_plural": "告警规则",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="AlertHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "status",
                    models.CharField(
                        choices=[("active", "活动"), ("resolved", "已解决"), ("acknowledged", "已确认")],
                        default="active",
                        max_length=20,
                        verbose_name="状态",
                    ),
                ),
                ("message", models.TextField(blank=True, verbose_name="告警消息")),
                ("metric_value", models.FloatField(verbose_name="指标值")),
                ("triggered_at", models.DateTimeField(auto_now_add=True, verbose_name="触发时间")),
                ("resolved_at", models.DateTimeField(blank=True, null=True, verbose_name="解决时间")),
                ("acknowledged_at", models.DateTimeField(blank=True, null=True, verbose_name="确认时间")),
                ("note", models.TextField(blank=True, verbose_name="备注")),
                (
                    "acknowledged_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="acknowledged_alerts",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="确认者",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_alerts",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="创建者",
                    ),
                ),
                (
                    "rule",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="alert_history",
                        to="monitoring.alertrule",
                        verbose_name="告警规则",
                    ),
                ),
            ],
            options={
                "verbose_name": "告警历史",
                "verbose_name_plural": "告警历史",
                "ordering": ["-triggered_at"],
            },
        ),
        migrations.CreateModel(
            name="Dashboard",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, verbose_name="仪表盘名称")),
                ("description", models.TextField(blank=True, verbose_name="仪表盘描述")),
                (
                    "layout_type",
                    models.CharField(
                        choices=[("grid", "网格布局"), ("flex", "弹性布局"), ("free", "自由布局")],
                        default="grid",
                        max_length=20,
                        verbose_name="布局类型",
                    ),
                ),
                ("layout", models.JSONField(default=dict, verbose_name="布局配置")),
                ("is_default", models.BooleanField(default=False, verbose_name="是否默认")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="dashboards",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="创建者",
                    ),
                ),
            ],
            options={
                "verbose_name": "仪表盘",
                "verbose_name_plural": "仪表盘",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="ErrorLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("message", models.TextField(verbose_name="错误信息")),
                ("stack_trace", models.TextField(blank=True, null=True, verbose_name="堆栈跟踪")),
                (
                    "severity",
                    models.CharField(
                        choices=[("INFO", "信息"), ("WARNING", "警告"), ("ERROR", "错误"), ("CRITICAL", "严重")],
                        default="ERROR",
                        max_length=10,
                        verbose_name="严重程度",
                    ),
                ),
                ("source", models.CharField(max_length=100, verbose_name="错误来源")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
            ],
            options={
                "verbose_name": "错误日志",
                "verbose_name_plural": "错误日志",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["-created_at"], name="error_log_created_at_idx"),
                    models.Index(fields=["severity", "-created_at"], name="error_log_severity_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="MonitoringVisualization",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, verbose_name="图表名称")),
                ("description", models.TextField(blank=True, verbose_name="图表描述")),
                (
                    "chart_type",
                    models.CharField(
                        choices=[("line", "折线图"), ("bar", "柱状图"), ("gauge", "仪表盘"), ("pie", "饼图")],
                        default="line",
                        max_length=20,
                        verbose_name="图表类型",
                    ),
                ),
                (
                    "metric_type",
                    models.CharField(
                        choices=[
                            ("cpu", "CPU使用率"),
                            ("memory", "内存使用率"),
                            ("disk", "磁盘使用率"),
                            ("network", "网络流量"),
                            ("api_latency", "API响应时间"),
                            ("error_rate", "错误率"),
                            ("request_count", "请求数"),
                            ("task_count", "任务数"),
                        ],
                        max_length=20,
                        verbose_name="指标类型",
                    ),
                ),
                (
                    "time_range",
                    models.IntegerField(default=60, help_text="统计最近n分钟的数据", verbose_name="时间范围(分钟)"),
                ),
                (
                    "interval",
                    models.IntegerField(default=60, help_text="数据聚合的时间间隔", verbose_name="统计间隔(秒)"),
                ),
                (
                    "aggregation_method",
                    models.CharField(
                        choices=[
                            ("avg", "平均值"),
                            ("max", "最大值"),
                            ("min", "最小值"),
                            ("sum", "求和"),
                            ("count", "计数"),
                        ],
                        default="avg",
                        max_length=20,
                        verbose_name="聚合方法",
                    ),
                ),
                (
                    "warning_threshold",
                    models.FloatField(blank=True, help_text="超过此值显示警告", null=True, verbose_name="警告阈值"),
                ),
                (
                    "critical_threshold",
                    models.FloatField(blank=True, help_text="超过此值显示严重警告", null=True, verbose_name="严重阈值"),
                ),
                ("is_active", models.IntegerField(default=1, verbose_name="是否启用")),
                (
                    "refresh_interval",
                    models.IntegerField(default=30, help_text="数据自动刷新的间隔", verbose_name="刷新间隔(秒)"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
                ("last_generated", models.DateTimeField(blank=True, null=True, verbose_name="上次生成时间")),
                (
                    "cached_data",
                    models.JSONField(blank=True, help_text="缓存的图表数据", null=True, verbose_name="缓存数据"),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="monitoring_visualizations",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="创建者",
                    ),
                ),
            ],
            options={
                "verbose_name": "监控可视化",
                "verbose_name_plural": "监控可视化",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="DashboardWidget",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, verbose_name="小部件名称")),
                (
                    "widget_type",
                    models.CharField(
                        choices=[("chart", "图表"), ("metric", "指标"), ("text", "文本"), ("alert", "告警")],
                        default="chart",
                        max_length=20,
                        verbose_name="小部件类型",
                    ),
                ),
                ("config", models.JSONField(default=dict, verbose_name="配置信息")),
                ("position", models.JSONField(default=dict, verbose_name="位置信息")),
                ("is_visible", models.BooleanField(default=True, verbose_name="是否可见")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
                (
                    "dashboard",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="widgets",
                        to="monitoring.dashboard",
                        verbose_name="所属仪表盘",
                    ),
                ),
                (
                    "visualization",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="widgets",
                        to="monitoring.monitoringvisualization",
                        verbose_name="可视化配置",
                    ),
                ),
            ],
            options={
                "verbose_name": "仪表盘小部件",
                "verbose_name_plural": "仪表盘小部件",
                "ordering": ["dashboard", "created_at"],
            },
        ),
        migrations.CreateModel(
            name="SystemMetrics",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "metric_type",
                    models.CharField(
                        choices=[
                            ("cpu", "CPU使用率"),
                            ("memory", "内存使用率"),
                            ("disk", "磁盘使用率"),
                            ("network", "网络流量"),
                            ("api_latency", "API响应时间"),
                            ("error_rate", "错误率"),
                            ("request_count", "请求数"),
                            ("task_count", "任务数"),
                        ],
                        max_length=20,
                        verbose_name="指标类型",
                    ),
                ),
                ("value", models.FloatField(verbose_name="指标值")),
                ("timestamp", models.DateTimeField(auto_now_add=True, verbose_name="时间戳")),
                ("metadata", models.JSONField(blank=True, default=dict, verbose_name="元数据")),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="system_metrics",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="创建者",
                    ),
                ),
            ],
            options={
                "verbose_name": "系统指标",
                "verbose_name_plural": "系统指标",
                "ordering": ["-timestamp"],
            },
        ),
        migrations.AddIndex(
            model_name="alertrule",
            index=models.Index(fields=["metric_type", "is_enabled"], name="monitoring__metric__ca52c6_idx"),
        ),
        migrations.AddIndex(
            model_name="alertrule",
            index=models.Index(fields=["created_at"], name="monitoring__created_e57411_idx"),
        ),
        migrations.AddIndex(
            model_name="alerthistory",
            index=models.Index(fields=["rule", "status"], name="monitoring__rule_id_0ac316_idx"),
        ),
        migrations.AddIndex(
            model_name="alerthistory",
            index=models.Index(fields=["triggered_at"], name="monitoring__trigger_ba7964_idx"),
        ),
        migrations.AddIndex(
            model_name="dashboard",
            index=models.Index(fields=["created_by", "is_default"], name="monitoring__created_578ec7_idx"),
        ),
        migrations.AddIndex(
            model_name="dashboard",
            index=models.Index(fields=["created_at"], name="monitoring__created_81e130_idx"),
        ),
        migrations.AddIndex(
            model_name="monitoringvisualization",
            index=models.Index(fields=["metric_type", "is_active"], name="monitoring__metric__3cd24a_idx"),
        ),
        migrations.AddIndex(
            model_name="monitoringvisualization",
            index=models.Index(fields=["created_at"], name="monitoring__created_b135c4_idx"),
        ),
        migrations.AddIndex(
            model_name="dashboardwidget",
            index=models.Index(fields=["dashboard", "is_visible"], name="monitoring__dashboa_c4a3b4_idx"),
        ),
        migrations.AddIndex(
            model_name="dashboardwidget",
            index=models.Index(fields=["created_at"], name="monitoring__created_c1b3a0_idx"),
        ),
        migrations.AddIndex(
            model_name="systemmetrics",
            index=models.Index(fields=["metric_type", "timestamp"], name="monitoring__metric__641d8a_idx"),
        ),
        migrations.AddIndex(
            model_name="systemmetrics",
            index=models.Index(fields=["created_by"], name="monitoring__created_ad5770_idx"),
        ),
    ]
