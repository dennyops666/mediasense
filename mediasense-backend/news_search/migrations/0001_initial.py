# Generated by Django 4.2.9 on 2025-01-27 10:33

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SearchSuggestion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("keyword", models.CharField(max_length=100, unique=True, verbose_name="关键词")),
                ("search_count", models.IntegerField(default=0, verbose_name="搜索次数")),
                ("is_hot", models.BooleanField(default=False, verbose_name="是否热门")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
            ],
            options={
                "verbose_name": "搜索建议",
                "verbose_name_plural": "搜索建议",
                "ordering": ["-search_count", "-updated_at"],
                "indexes": [
                    models.Index(fields=["-search_count"], name="news_search_search__e51234_idx"),
                    models.Index(fields=["keyword"], name="news_search_keyword_eb550f_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="SearchHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("keyword", models.CharField(max_length=100, verbose_name="关键词")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="搜索时间")),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="search_history",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="用户",
                    ),
                ),
            ],
            options={
                "verbose_name": "搜索历史",
                "verbose_name_plural": "搜索历史",
                "ordering": ["-created_at"],
                "indexes": [models.Index(fields=["user", "-created_at"], name="news_search_user_id_704c7f_idx")],
            },
        ),
    ]
