# Generated by Django 5.1.4 on 2025-01-23 20:39

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("news", "0002_alter_newsarticle_url"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="newsarticle",
            name="created_by",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="created_articles",
                to=settings.AUTH_USER_MODEL,
                verbose_name="创建者",
            ),
        ),
    ]
