from rest_framework import serializers

from .models import CrawlerConfig, CrawlerTask


class CrawlerConfigSerializer(serializers.ModelSerializer):
    """爬虫配置序列化器"""

    class Meta:
        model = CrawlerConfig
        fields = [
            "id",
            "name",
            "crawler_type",
            "url",
            "request_headers",
            "fetch_interval",
            "enabled",
            "last_fetch_time",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["last_fetch_time", "created_at", "updated_at"]

    def validate_request_headers(self, value):
        """验证请求头格式"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("请求头必须是JSON对象格式")
        return value

    def validate(self, attrs):
        """验证配置数据"""
        # 验证抓取间隔
        if attrs.get("fetch_interval", 0) < 300:  # 最小5分钟
            raise serializers.ValidationError({"fetch_interval": "抓取间隔不能小于5分钟"})
        return attrs


class CrawlerTaskSerializer(serializers.ModelSerializer):
    """爬虫任务列表序列化器"""

    config_name = serializers.CharField(source="config.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = CrawlerTask
        fields = [
            "id",
            "config_id",
            "config_name",
            "status",
            "status_display",
            "is_test",
            "start_time",
            "end_time",
            "created_at",
        ]
        read_only_fields = fields


class CrawlerTaskDetailSerializer(CrawlerTaskSerializer):
    """爬虫任务详情序列化器"""

    config = CrawlerConfigSerializer(read_only=True)

    class Meta(CrawlerTaskSerializer.Meta):
        fields = CrawlerTaskSerializer.Meta.fields + ["config", "error_message", "result_count"]
        read_only_fields = fields
