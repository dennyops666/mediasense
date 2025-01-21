# Generated by Django 5.1.4 on 2025-01-21 12:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crawler", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name='NewsArticle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=500, verbose_name='标题')),
                ('description', models.TextField(blank=True, verbose_name='描述')),
                ('content', models.TextField(blank=True, verbose_name='内容')),
                ('url', models.URLField(max_length=255, unique=True, verbose_name='链接')),
                ('source', models.CharField(max_length=100, verbose_name='来源')),
                ('author', models.CharField(blank=True, max_length=100, verbose_name='作者')),
                ('pub_time', models.DateTimeField(verbose_name='发布时间')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
            ],
            options={
                'verbose_name': '新闻文章',
                'verbose_name_plural': '新闻文章',
                'ordering': ['-pub_time'],
                'indexes': [
                    models.Index(fields=['-pub_time'], name='news_article_pub_time_idx'),
                    models.Index(fields=['source', '-pub_time'], name='news_article_source_idx'),
                ],
            },
        ),
    ]
