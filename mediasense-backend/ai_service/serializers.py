from rest_framework import serializers

from .models import (
    AnalysisCache,
    AnalysisNotification,
    AnalysisResult,
    AnalysisRule,
    AnalysisSchedule,
    AnalysisVisualization,
    BatchAnalysisResult,
    BatchAnalysisTask,
    NotificationSubscription,
    ScheduleExecution,
    Notification,
)


class AnalysisRuleSerializer(serializers.ModelSerializer):
    """分析规则序列化器"""

    created_by = serializers.ReadOnlyField(source="created_by.username")
    rule_type_display = serializers.CharField(source="get_rule_type_display", read_only=True)

    class Meta:
        model = AnalysisRule
        fields = [
            "id",
            "name",
            "rule_type",
            "rule_type_display",
            "system_prompt",
            "user_prompt_template",
            "parameters",
            "is_active",
            "created_at",
            "updated_at",
            "description",
            "created_by",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "created_by"]

    def validate_parameters(self, value):
        """验证分析参数"""
        required_params = {"temperature", "max_tokens"}
        if not all(param in value for param in required_params):
            raise serializers.ValidationError(f"必须提供以下参数：{', '.join(required_params)}")

        if not 0 <= float(value["temperature"]) <= 2:
            raise serializers.ValidationError("temperature必须在0到2之间")

        if not 1 <= int(value["max_tokens"]) <= 4000:
            raise serializers.ValidationError("max_tokens必须在1到4000之间")

        return value

    def validate_user_prompt_template(self, value):
        """验证用户提示词模板"""
        required_placeholders = {"{title}", "{content}"}
        for placeholder in required_placeholders:
            if placeholder not in value:
                raise serializers.ValidationError(f"提示词模板必须包含{placeholder}占位符")
        return value


class AnalysisResultSerializer(serializers.ModelSerializer):
    """分析结果序列化器"""
    result = serializers.JSONField()
    
    class Meta:
        model = AnalysisResult
        fields = ['id', 'news', 'analysis_type', 'result', 'is_valid', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # 将result字段的内容展开到顶层
        if instance.result:
            data.update(instance.result)
        return data


class AnalysisCacheSerializer(serializers.ModelSerializer):
    """分析缓存序列化器"""

    class Meta:
        model = AnalysisCache
        fields = ["id", "cache_key", "result", "expires_at", "created_at"]
        read_only_fields = ["id", "created_at"]


class BatchAnalysisTaskSerializer(serializers.ModelSerializer):
    """批量分析任务序列化器"""

    duration = serializers.FloatField(read_only=True)
    success_rate = serializers.FloatField(read_only=True)
    news_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    analysis_types = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)

    class Meta:
        model = BatchAnalysisTask
        fields = [
            "id",
            "name",
            "rule",
            "news_ids",
            "analysis_types",
            "status",
            "total_count",
            "processed",
            "success",
            "failed",
            "error_message",
            "created_at",
            "started_at",
            "completed_at",
            "duration",
            "success_rate",
            "created_by",
            "config",
        ]
        read_only_fields = [
            "id",
            "status",
            "total_count",
            "processed",
            "success",
            "failed",
            "error_message",
            "created_at",
            "started_at",
            "completed_at",
            "duration",
            "success_rate",
            "created_by",
        ]

    def create(self, validated_data):
        news_ids = validated_data.pop('news_ids', [])
        analysis_types = validated_data.pop('analysis_types', ['sentiment'])
        validated_data['config'] = {
            'news_ids': news_ids,
            'analysis_types': analysis_types
        }
        validated_data['status'] = 'pending'
        validated_data['total_count'] = len(news_ids)
        return super().create(validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.config:
            data['news_ids'] = instance.config.get('news_ids', [])
            data['analysis_types'] = instance.config.get('analysis_types', [])
        return data


class BatchAnalysisResultSerializer(serializers.ModelSerializer):
    """批量分析结果序列化器"""

    class Meta:
        model = BatchAnalysisResult
        fields = ["id", "task", "news_id", "results", "is_success", "created_at"]
        read_only_fields = ["task", "news_id", "results", "is_success", "created_at"]


class AnalysisScheduleSerializer(serializers.ModelSerializer):
    """分析任务调度序列化器"""

    created_by = serializers.ReadOnlyField(source="created_by.username")
    schedule_type_display = serializers.CharField(source="get_schedule_type_display", read_only=True)
    rules = AnalysisRuleSerializer(many=True, read_only=True)
    rule = serializers.PrimaryKeyRelatedField(
        queryset=AnalysisRule.objects.filter(is_active=True), write_only=True, required=True
    )
    is_active = serializers.IntegerField(default=1)

    class Meta:
        model = AnalysisSchedule
        fields = [
            "id",
            "name",
            "schedule_type",
            "schedule_type_display",
            "interval_minutes",
            "cron_expression",
            "analysis_types",
            "categories",
            "rules",
            "rule",
            "time_window",
            "is_active",
            "created_by",
            "created_at",
            "updated_at",
            "last_run",
            "next_run",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at", "last_run", "next_run"]

    def validate(self, data):
        """验证调度配置"""
        # 设置默认值
        if "schedule_type" not in data:
            data["schedule_type"] = "cron"
        
        schedule_type = data["schedule_type"]
        
        # 根据调度类型设置默认值
        if schedule_type == "interval":
            if "interval_minutes" not in data or not data["interval_minutes"]:
                data["interval_minutes"] = 60  # 默认每小时执行一次
        elif schedule_type == "cron":
            if "cron_expression" not in data or not data["cron_expression"]:
                data["cron_expression"] = "0 0 * * *"  # 默认每天午夜执行

        # 设置其他默认值
        if "analysis_types" not in data:
            data["analysis_types"] = ["sentiment"]
        if "categories" not in data:
            data["categories"] = []
        if "time_window" not in data:
            data["time_window"] = 24  # 默认24小时
        if "is_active" not in data:
            data["is_active"] = 1  # 默认启用

        # 验证必填字段
        if "name" not in data:
            raise serializers.ValidationError("必须提供调度名称")
        if "rule" not in data:
            raise serializers.ValidationError("必须提供分析规则")

        return data

    def create(self, validated_data):
        """创建调度"""
        rule = validated_data.pop('rule', None)
        instance = super().create(validated_data)
        if rule:
            instance.rules.add(rule)
        return instance


class ScheduleExecutionSerializer(serializers.ModelSerializer):
    """调度执行记录序列化器"""

    schedule_name = serializers.CharField(source="schedule.name", read_only=True)
    duration = serializers.FloatField(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = ScheduleExecution
        fields = [
            "id",
            "schedule",
            "schedule_name",
            "status",
            "status_display",
            "started_at",
            "completed_at",
            "total_articles",
            "processed_articles",
            "success_articles",
            "error_message",
            "duration",
        ]
        read_only_fields = [
            "id",
            "schedule",
            "schedule_name",
            "status",
            "status_display",
            "started_at",
            "completed_at",
            "total_articles",
            "processed_articles",
            "success_articles",
            "error_message",
            "duration",
        ]


class NotificationSubscriptionSerializer(serializers.ModelSerializer):
    """通知订阅配置序列化器"""

    class Meta:
        model = NotificationSubscription
        fields = [
            "id",
            "user",
            "email_enabled",
            "websocket_enabled",
            "notify_on_complete",
            "notify_on_error",
            "notify_on_batch",
            "notify_on_schedule",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at"]

    def validate(self, data):
        """验证订阅配置"""
        # 确保至少启用一种通知方式
        if not data.get('email_enabled', False) and not data.get('websocket_enabled', False):
            raise serializers.ValidationError("至少需要启用一种通知方式")

        # 确保至少订阅一种通知类型
        notify_types = [
            data.get('notify_on_complete', False),
            data.get('notify_on_error', False),
            data.get('notify_on_batch', False),
            data.get('notify_on_schedule', False)
        ]
        if not any(notify_types):
            raise serializers.ValidationError("至少需要订阅一种通知类型")

        # 设置默认值
        data.setdefault('email_enabled', True)
        data.setdefault('websocket_enabled', True)
        data.setdefault('notify_on_complete', True)
        data.setdefault('notify_on_error', True)
        data.setdefault('notify_on_batch', False)
        data.setdefault('notify_on_schedule', False)

        return data

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user
        return super().create(validated_data)


class AnalysisNotificationSerializer(serializers.ModelSerializer):
    """分析通知序列化器"""

    notification_type_display = serializers.CharField(source="get_notification_type_display", read_only=True)

    class Meta:
        model = AnalysisNotification
        fields = [
            "id",
            "notification_type",
            "notification_type_display",
            "title",
            "content",
            "data",
            "is_read",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "notification_type",
            "notification_type_display",
            "title",
            "content",
            "data",
            "created_at",
        ]


class AnalysisVisualizationSerializer(serializers.ModelSerializer):
    """分析可视化序列化器"""

    created_by = serializers.ReadOnlyField(source="created_by.username")
    chart_type_display = serializers.CharField(source="get_chart_type_display", read_only=True)
    data_type_display = serializers.CharField(source="get_data_type_display", read_only=True)

    class Meta:
        model = AnalysisVisualization
        fields = [
            "id",
            "name",
            "description",
            "chart_type",
            "chart_type_display",
            "data_type",
            "data_type_display",
            "time_range",
            "categories",
            "aggregation_field",
            "aggregation_method",
            "group_by",
            "filters",
            "is_active",
            "created_by",
            "created_at",
            "updated_at",
            "last_generated",
            "cached_data",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at", "last_generated", "cached_data"]

    def validate_time_range(self, value):
        """验证时间范围"""
        if value < 1:
            raise serializers.ValidationError("时间范围必须大于0")
        return value

    def validate_aggregation_field(self, value):
        """验证聚合字段"""
        valid_fields = {"result", "is_valid", "created_at"}
        if value not in valid_fields:
            raise serializers.ValidationError(f'聚合字段必须是以下之一: {", ".join(valid_fields)}')
        return value

    def validate_group_by(self, value):
        """验证分组字段"""
        valid_fields = {"news__category", "analysis_type", "created_at__date"}
        if value not in valid_fields:
            raise serializers.ValidationError(f'分组字段必须是以下之一: {", ".join(valid_fields)}')
        return value


class NotificationSerializer(serializers.ModelSerializer):
    """通知序列化器"""

    notification_type_display = serializers.CharField(source="get_notification_type_display", read_only=True)
    user = serializers.ReadOnlyField(source="user.username")

    class Meta:
        model = Notification
        fields = [
            "id",
            "user",
            "notification_type",
            "notification_type_display",
            "title",
            "content",
            "is_read",
            "created_at",
            "updated_at",
            "related_object_id",
            "related_object_type",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "user"]
