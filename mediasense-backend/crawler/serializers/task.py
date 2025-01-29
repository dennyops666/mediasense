from rest_framework import serializers

from ..models import CrawlerTask


class CrawlerTaskSerializer(serializers.ModelSerializer):
    """
    爬虫任务序列化器
    """
    config_name = serializers.CharField(source='config.name', read_only=True)
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = CrawlerTask
        fields = (
            'id', 'config', 'task_id', 'status', 'result',
            'error_message', 'start_time', 'end_time', 'is_test',
            'created_at', 'updated_at', 'config_name', 'items_count'
        )
        read_only_fields = (
            'id', 'task_id', 'status', 'result', 'error_message',
            'start_time', 'end_time', 'created_at', 'updated_at'
        )

    def get_items_count(self, obj):
        """获取抓取数量"""
        return obj.result.get('items_count', 0) if obj.result else 0 