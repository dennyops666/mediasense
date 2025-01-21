from rest_framework import serializers

from .models import CrawlerConfig, CrawlerTask


class CrawlerConfigSerializer(serializers.ModelSerializer):
    """
    爬虫配置序列化器
    """
    total_tasks = serializers.SerializerMethodField()
    total_items = serializers.SerializerMethodField()
    success_rate = serializers.SerializerMethodField()

    class Meta:
        model = CrawlerConfig
        fields = [
            'id', 'name', 'description', 'source_url', 'crawler_type',
            'config_data', 'headers', 'interval', 'status', 'last_run_time',
            'created_at', 'updated_at', 'total_tasks', 'total_items', 'success_rate'
        ]
        read_only_fields = ['last_run_time', 'created_at', 'updated_at']

    def validate_interval(self, value):
        """验证抓取间隔"""
        if value < 5:  # 最小5分钟
            raise serializers.ValidationError("抓取间隔不能小于5分钟")
        return value

    def get_total_tasks(self, obj):
        """获取总任务数"""
        return obj.crawlertask_set.count()

    def get_total_items(self, obj):
        """获取总抓取数量"""
        return sum(
            task.result.get('items_count', 0)
            for task in obj.crawlertask_set.filter(status=2)  # 已完成状态
            if task.result
        )

    def get_success_rate(self, obj):
        """获取成功率"""
        total = obj.crawlertask_set.count()
        if not total:
            return 0
        success = obj.crawlertask_set.filter(status=2).count()  # 已完成状态
        return round(success / total * 100, 2)


class CrawlerTaskSerializer(serializers.ModelSerializer):
    """
    爬虫任务序列化器
    """
    config_name = serializers.CharField(source='config.name', read_only=True)
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = CrawlerTask
        fields = [
            'id', 'config', 'config_name', 'status', 'start_time', 'end_time',
            'result', 'error_message', 'created_at', 'updated_at', 'items_count'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_items_count(self, obj):
        """获取抓取数量"""
        return obj.result.get('items_count', 0) if obj.result else 0


class CrawlerTaskDetailSerializer(CrawlerTaskSerializer):
    """爬虫任务详情序列化器"""

    config = CrawlerConfigSerializer(read_only=True)

    class Meta(CrawlerTaskSerializer.Meta):
        fields = CrawlerTaskSerializer.Meta.fields + ['result']
        read_only_fields = fields
