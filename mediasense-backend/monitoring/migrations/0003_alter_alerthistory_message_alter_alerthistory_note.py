# Generated by Django 5.1.5 on 2025-02-02 09:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("monitoring", "0002_fix_alert_history_note_field"),
    ]

    operations = [
        migrations.AlterField(
            model_name="alerthistory",
            name="message",
            field=models.TextField(blank=True, default="", verbose_name="告警消息"),
        ),
        migrations.AlterField(
            model_name="alerthistory",
            name="note",
            field=models.TextField(blank=True, default="", verbose_name="备注"),
        ),
    ]
