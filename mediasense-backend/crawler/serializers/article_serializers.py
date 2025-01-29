from rest_framework import serializers
from ..models import NewsArticle
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
import re


class NewsArticleCreateSerializer(serializers.ModelSerializer):
    """新闻文章创建序列化器"""

    class Meta:
        model = NewsArticle
        fields = ['title', 'source_url', 'author', 'source', 'content', 'description', 'pub_date', 'crawler']

    def validate_source_url(self, value):
        """验证源URL"""
        # 检查URL格式
        validator = URLValidator()
        try:
            validator(value)
        except ValidationError:
            raise serializers.ValidationError("无效的URL格式")

        # 检查URL是否已存在
        if NewsArticle.objects.filter(source_url=value).exists():
            raise serializers.ValidationError("该文章URL已存在")

        return value

    def validate(self, data):
        """验证所有字段"""
        # 验证标题
        if not data.get('title'):
            raise serializers.ValidationError({"title": "标题不能为空"})

        # 验证内容
        if not data.get('content'):
            raise serializers.ValidationError({"content": "内容不能为空"})

        # 验证发布时间
        if not data.get('pub_date'):
            raise serializers.ValidationError({"pub_date": "发布时间不能为空"})

        return data 