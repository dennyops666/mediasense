# Generated by Django 4.2.9 on 2025-01-29 12:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("monitoring", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="alertrule",
            options={"verbose_name": "告警规则", "verbose_name_plural": "告警规则"},
        ),
        migrations.RemoveIndex(
            model_name="alertrule",
            name="monitoring__metric__ca52c6_idx",
        ),
        migrations.RemoveIndex(
            model_name="alertrule",
            name="monitoring__created_e57411_idx",
        ),
        migrations.RemoveIndex(
            model_name="monitoringvisualization",
            name="monitoring__metric__3cd24a_idx",
        ),
        migrations.RemoveIndex(
            model_name="monitoringvisualization",
            name="monitoring__created_b135c4_idx",
        ),
        migrations.RemoveIndex(
            model_name="systemmetrics",
            name="monitoring__created_ad5770_idx",
        ),
        migrations.RemoveField(
            model_name="alertrule",
            name="created_by",
        ),
        migrations.RemoveField(
            model_name="monitoringvisualization",
            name="created_by",
        ),
        migrations.RemoveField(
            model_name="monitoringvisualization",
            name="last_generated",
        ),
        migrations.RemoveField(
            model_name="systemmetrics",
            name="created_by",
        ),
        migrations.AlterField(
            model_name="alertrule",
            name="duration",
            field=models.IntegerField(default=60, verbose_name="持续时间(秒)"),
        ),
        migrations.AlterField(
            model_name="alertrule",
            name="operator",
            field=models.CharField(choices=[("gt", "大于"), ("lt", "小于")], max_length=10, verbose_name="比较运算符"),
        ),
        migrations.AlterField(
            model_name="monitoringvisualization",
            name="cached_data",
            field=models.JSONField(blank=True, null=True, verbose_name="缓存数据"),
        ),
        migrations.AlterField(
            model_name="monitoringvisualization",
            name="visualization_type",
            field=models.CharField(
                choices=[("line_chart", "折线图"), ("gauge", "仪表盘")], max_length=20, verbose_name="可视化类型"
            ),
        ),
        migrations.AlterField(
            model_name="systemmetrics",
            name="timestamp",
            field=models.DateTimeField(auto_now_add=True, verbose_name="记录时间"),
        ),
    ]
