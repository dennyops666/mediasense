from rest_framework import serializers

from ..models import CrawlerConfig


class CrawlerConfigSerializer(serializers.ModelSerializer):
    """爬虫配置序列化器"""

    class Meta:
        model = CrawlerConfig
        fields = (
            'id', 'name', 'description', 'source_url', 'crawler_type',
            'config_data', 'headers', 'interval', 'max_retries', 'retry_delay',
            'status', 'is_active', 'last_run_time', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'is_active', 'last_run_time', 'created_at', 'updated_at')

    def validate_interval(self, value):
        """验证抓取间隔"""
        if value < 5:  # 最小5分钟
            raise serializers.ValidationError("抓取间隔不能小于5分钟")
        return value


class CrawlerConfigBulkSerializer(serializers.ModelSerializer):
    """爬虫配置批量操作序列化器"""

    class Meta:
        model = CrawlerConfig
        fields = (
            'id', 'name', 'description', 'source_url', 'crawler_type',
            'config_data', 'headers', 'interval', 'max_retries', 'retry_delay',
            'status', 'is_active'
        )
        read_only_fields = ('id',)

    def validate_interval(self, value):
        """验证抓取间隔"""
        if value < 5:  # 最小5分钟
            raise serializers.ValidationError("抓取间隔不能小于5分钟")
        return value 