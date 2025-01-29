from rest_framework import serializers
from django.utils import timezone

from news.models import NewsArticle


class NewsArticleCreateSerializer(serializers.ModelSerializer):
    """新闻文章创建序列化器"""

    class Meta:
        model = NewsArticle
        fields = [
            'title',
            'source_url',
            'author',
            'source',
            'content',
            'summary',
            'publish_time',
            'crawler',
            'status',
            'tags'
        ]

    def validate_source_url(self, value):
        """验证URL唯一性"""
        if not value:
            raise serializers.ValidationError('URL不能为空')
        
        if not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError('无效的URL格式')
            
        qs = NewsArticle.objects.filter(source_url=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('该URL已存在')
        return value

    def validate(self, attrs):
        """验证文章数据"""
        # 验证必要字段
        if not attrs.get('title'):
            raise serializers.ValidationError({'title': '标题不能为空'})
            
        if not attrs.get('source_url'):
            raise serializers.ValidationError({'source_url': 'URL不能为空'})
            
        # 如果没有发布时间，使用当前时间
        if not attrs.get('publish_time'):
            attrs['publish_time'] = timezone.now()
            
        # 设置默认值
        attrs.setdefault('summary', '')
        attrs.setdefault('status', NewsArticle.Status.DRAFT)
        attrs.setdefault('tags', [])
            
        return attrs 