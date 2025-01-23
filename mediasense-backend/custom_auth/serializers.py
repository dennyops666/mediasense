from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.exceptions import AuthenticationFailed

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """用户序列化器"""

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'is_active', 'date_joined', 'last_login')
        read_only_fields = ('id', 'date_joined', 'last_login')


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """自定义令牌序列化器"""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # 添加自定义声明
        token['username'] = user.username
        token['email'] = user.email
        token['is_staff'] = user.is_staff
        return token


class UserProfileSerializer(serializers.ModelSerializer):
    """用户档案序列化器"""

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_active')
        read_only_fields = ('id', 'username', 'email', 'is_active')


class ChangePasswordSerializer(serializers.Serializer):
    """修改密码序列化器"""

    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("旧密码不正确")
        return value

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class ResetPasswordSerializer(serializers.Serializer):
    """重置密码序列化器"""

    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("该邮箱未注册")
        return value

    def save(self, **kwargs):
        email = self.validated_data['email']
        user = User.objects.get(email=email)
        # TODO: 发送重置密码邮件
        return user
