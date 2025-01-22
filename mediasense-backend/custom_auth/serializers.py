from django.contrib.auth import get_user_model
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
        fields = ("id", "username", "email", "user_type", "date_joined", "last_login")
        read_only_fields = ("id", "date_joined", "last_login")


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """自定义令牌获取序列化器"""

    def validate(self, attrs):
        """验证用户凭据"""
        # 先调用父类的验证方法获取token
        data = super().validate(attrs)

        # 获取用户
        user = self.user

        # 检查用户是否被封禁
        if not user.is_active:
            raise AuthenticationFailed("账号已被封禁")

        # 更新最后登录时间
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        # 返回用户信息和令牌
        data['user'] = UserSerializer(user).data
        return data
