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

    class Meta:
        model = AnalysisResult
        fields = ["id", "news", "analysis_type", "result", "created_at", "updated_at", "is_valid", "error_message"]
        read_only_fields = ["id", "created_at", "updated_at"]


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

    class Meta:
        model = BatchAnalysisTask
        fields = [
            "id",
            "created_by",
            "news_ids",
            "analysis_types",
            "status",
            "total_articles",
            "processed_articles",
            "success_articles",
            "error_message",
            "created_at",
            "started_at",
            "completed_at",
            "duration",
            "success_rate",
        ]
        read_only_fields = [
            "created_by",
            "status",
            "total_articles",
            "processed_articles",
            "success_articles",
            "error_message",
            "created_at",
            "started_at",
            "completed_at",
            "duration",
            "success_rate",
        ]


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
    rule_ids = serializers.PrimaryKeyRelatedField(
        queryset=AnalysisRule.objects.filter(is_active=True), many=True, write_only=True, required=False, source="rules"
    )

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
            "rule_ids",
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
        schedule_type = data.get("schedule_type")
        interval_minutes = data.get("interval_minutes")
        cron_expression = data.get("cron_expression")

        if schedule_type == AnalysisSchedule.ScheduleType.INTERVAL:
            if not interval_minutes:
                raise serializers.ValidationError({"interval_minutes": "间隔执行必须设置执行间隔"})
            if interval_minutes < 1:
                raise serializers.ValidationError({"interval_minutes": "执行间隔必须大于0"})
        else:  # CRON
            if not cron_expression:
                raise serializers.ValidationError({"cron_expression": "定时执行必须设置Cron表达式"})
            try:
                from croniter import croniter

                if not croniter.is_valid(cron_expression):
                    raise ValueError("Invalid cron expression")
            except Exception as e:
                raise serializers.ValidationError({"cron_expression": f"Cron表达式格式错误: {str(e)}"})

        return data


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
            "email_enabled",
            "websocket_enabled",
            "notify_on_complete",
            "notify_on_error",
            "notify_on_batch",
            "notify_on_schedule",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


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
