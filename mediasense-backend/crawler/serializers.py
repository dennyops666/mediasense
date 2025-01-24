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
        fields = (
            'id', 'name', 'description', 'source_url', 'crawler_type',
            'config_data', 'headers', 'interval', 'max_retries', 'retry_delay',
            'status', 'is_active', 'created_at', 'updated_at', 'total_tasks',
            'total_items', 'success_rate'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

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


class CrawlerTaskDetailSerializer(CrawlerTaskSerializer):
    """爬虫任务详情序列化器"""

    config = CrawlerConfigSerializer(read_only=True)


class CrawlerTaskBulkSerializer(serializers.ListSerializer):
    """爬虫任务批量操作序列化器"""

    child = CrawlerTaskSerializer()

    def create(self, validated_data):
        tasks = [CrawlerTask(**item) for item in validated_data]
        return CrawlerTask.objects.bulk_create(tasks)

    def update(self, instances, validated_data):
        instance_hash = {index: instance for index, instance in enumerate(instances)}

        result = [
            self.child.update(instance_hash[index], attrs)
            for index, attrs in enumerate(validated_data)
        ]

        writable_fields = [
            field for field in self.child.Meta.fields
            if field not in self.child.Meta.read_only_fields
        ]

        CrawlerTask.objects.bulk_update(result, writable_fields)

        return result
