from rest_framework import serializers
from .models import MonitorRule, MonitorAlert, SystemMetric, ErrorLog

class MonitorRuleSerializer(serializers.ModelSerializer):
    """监控规则序列化器"""
    
    condition_display = serializers.CharField(source='get_condition_display', read_only=True)
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = MonitorRule
        fields = [
            'id', 'name', 'metric', 'condition', 'condition_display',
            'threshold', 'duration', 'description', 'is_active',
            'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def create(self, validated_data):
        """创建监控规则"""
        try:
            print("开始创建监控规则...")  # 调试信息
            print(f"验证后的数据: {validated_data}")  # 调试信息
            
            request = self.context.get('request')
            print(f"请求上下文: {self.context}")  # 调试信息
            
            if not request:
                print("缺少request上下文")  # 调试信息
                raise serializers.ValidationError('缺少request上下文')
            
            print(f"请求用户: {request.user}")  # 调试信息
            if not request.user:
                print("缺少用户信息")  # 调试信息
                raise serializers.ValidationError('缺少用户信息')
            
            if not request.user.is_authenticated:
                print("用户未认证")  # 调试信息
                raise serializers.ValidationError('用户未认证')
            
            validated_data['created_by'] = request.user
            print(f"添加创建者信息后的数据: {validated_data}")  # 调试信息
            
            try:
                print("开始调用父类的create方法...")  # 调试信息
                instance = super().create(validated_data)
                print(f"创建成功: {instance}")  # 调试信息
                return instance
            except Exception as e:
                print(f"创建实例失败: {str(e)}")  # 调试信息
                raise serializers.ValidationError(f"创建实例失败: {str(e)}")
            
        except serializers.ValidationError as e:
            print(f"验证错误: {str(e)}")  # 调试信息
            raise
        except Exception as e:
            import traceback
            error_msg = f"Error in MonitorRuleSerializer.create: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)  # 开发环境打印错误
            raise serializers.ValidationError(str(e))

class MonitorAlertSerializer(serializers.ModelSerializer):
    """监控告警序列化器"""
    
    rule = MonitorRuleSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    resolved_by_username = serializers.CharField(source='resolved_by.username', read_only=True, allow_null=True)

    class Meta:
        model = MonitorAlert
        fields = [
            'id', 'rule', 'metric_value', 'status', 'status_display',
            'message', 'resolved_at', 'resolved_by', 'resolved_by_username',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'status']
        
    def get_status(self, obj):
        """获取状态"""
        return obj.status if hasattr(obj, 'status') else MonitorAlert.Status.ACTIVE
        
    def to_representation(self, instance):
        """自定义序列化表示"""
        if isinstance(instance, (list, tuple)):
            return [self.to_representation(item) for item in instance]
            
        if hasattr(instance, '_meta'):
            data = super().to_representation(instance)
            if not data.get('status'):
                data['status'] = self.get_status(instance)
            return data
        elif hasattr(instance, 'status'):
            return {'status': instance.status}
        else:
            return {'status': MonitorAlert.Status.ACTIVE}
            
    def get_fields(self):
        """获取字段"""
        fields = super().get_fields()
        fields['status'] = serializers.CharField(read_only=True)
        return fields
        
    def create(self, validated_data):
        """创建告警"""
        instance = super().create(validated_data)
        instance.status = MonitorAlert.Status.ACTIVE
        instance.save()
        return instance

class SystemMetricSerializer(serializers.ModelSerializer):
    """系统指标序列化器"""

    class Meta:
        model = SystemMetric
        fields = [
            'id', 'metric_name', 'value', 'unit',
            'timestamp', 'metadata'
        ]
        read_only_fields = ['timestamp']

class ErrorLogSerializer(serializers.ModelSerializer):
    """错误日志序列化器"""
    
    level_display = serializers.CharField(source='get_level_display', read_only=True)

    class Meta:
        model = ErrorLog
        fields = [
            'id', 'timestamp', 'level', 'level_display', 
            'service', 'message', 'traceback', 'metadata'
        ]
        read_only_fields = ['timestamp'] 