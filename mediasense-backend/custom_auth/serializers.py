from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """用户序列化器"""

    class Meta:
        model = User
        fields = ("id", "username", "email", "phone", "user_type", "status", "avatar", "date_joined", "last_login")
        read_only_fields = ("id", "date_joined", "last_login")


class UserCreateSerializer(serializers.ModelSerializer):
    """用户创建序列化器"""

    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password], style={"input_type": "password"}
    )
    password2 = serializers.CharField(write_only=True, required=True, style={"input_type": "password"})
    phone = serializers.CharField(
        required=True, validators=[RegexValidator(regex=r"^1[3-9]\d{9}$", message="请输入有效的手机号码")]
    )

    class Meta:
        model = User
        fields = ("username", "password", "password2", "email", "phone")

    def validate_username(self, value):
        """验证用户名"""
        try:
            if len(value) < 3:
                raise serializers.ValidationError("用户名长度不能小于3个字符")
            if User.objects.filter(username=value).exists():
                raise serializers.ValidationError("该用户名已被使用")
            return value
        except serializers.ValidationError:
            raise
        except Exception as e:
            raise serializers.ValidationError("用户名验证失败")

    def validate_phone(self, value):
        """验证手机号"""
        try:
            if User.objects.filter(phone=value).exists():
                raise serializers.ValidationError("该手机号已被注册")
            return value
        except serializers.ValidationError:
            raise
        except Exception as e:
            raise serializers.ValidationError("手机号验证失败")

    def validate_email(self, value):
        """验证邮箱"""
        try:
            if User.objects.filter(email=value).exists():
                raise serializers.ValidationError("该邮箱已被注册")
            return value
        except serializers.ValidationError:
            raise
        except Exception as e:
            raise serializers.ValidationError("邮箱验证失败")

    def validate(self, attrs):
        """验证密码"""
        try:
            if attrs["password"] != attrs["password2"]:
                raise serializers.ValidationError({"password2": "两次输入的密码不匹配"})
            return attrs
        except KeyError:
            raise serializers.ValidationError({"password": "密码字段不能为空"})
        except serializers.ValidationError:
            raise
        except Exception as e:
            raise serializers.ValidationError({"non_field_errors": "密码验证失败"})

    def create(self, validated_data):
        """创建用户"""
        try:
            validated_data.pop("password2")
            password = validated_data.pop("password")
            user = User.objects.create_user(**validated_data, is_active=True, status=User.UserStatus.ACTIVE)
            user.set_password(password)
            user.save()
            return user
        except Exception as e:
            raise serializers.ValidationError({"non_field_errors": "用户创建失败，请稍后重试"})


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """自定义Token序列化器"""

    MAX_LOGIN_ATTEMPTS = 5  # 最大登录尝试次数
    LOCKOUT_TIME = 15 * 60  # 锁定时间（秒）

    def validate(self, attrs):
        # 获取用户名，用于检查登录失败次数
        username = attrs.get(self.username_field)

        try:
            # 检查用户是否存在
            try:
                user = User.objects.get(**{self.username_field: username})
            except User.DoesNotExist:
                # 用户不存在，增加失败计数并抛出错误
                self._increment_failed_attempts(username)
                # 检查是否达到最大失败次数
                if self._is_account_locked(username):
                    minutes = self.LOCKOUT_TIME // 60
                    raise serializers.ValidationError({"non_field_errors": [f"登录失败次数过多，请{minutes}分钟后重试"]})
                raise serializers.ValidationError({"non_field_errors": ["用户名或密码错误"]})

            # 检查用户状态
            if not user.is_active:
                raise serializers.ValidationError({"non_field_errors": ["账户已被禁用，请联系管理员"]})
            if user.status == User.UserStatus.BANNED:
                raise serializers.ValidationError({"non_field_errors": ["账户已被封禁，请联系管理员"]})
            if user.status == User.UserStatus.INACTIVE:
                raise serializers.ValidationError({"non_field_errors": ["账户未激活，请先激活账户"]})

            # 检查账户是否被锁定
            if self._is_account_locked(username):
                minutes = self.LOCKOUT_TIME // 60
                raise serializers.ValidationError({"non_field_errors": [f"登录失败次数过多，请{minutes}分钟后重试"]})

            # 验证密码
            try:
                data = super().validate(attrs)
            except Exception as e:
                # 密码验证失败，增加失败计数
                self._increment_failed_attempts(username)
                # 检查是否达到最大失败次数
                if self._is_account_locked(username):
                    minutes = self.LOCKOUT_TIME // 60
                    raise serializers.ValidationError({"non_field_errors": [f"登录失败次数过多，请{minutes}分钟后重试"]})
                raise serializers.ValidationError({"non_field_errors": ["用户名或密码错误"]})

            # 验证成功，清除失败计数
            self._clear_failed_attempts(username)
            # 更新用户最后登录信息
            self._update_last_login(self.user)

            # 添加额外的用户信息到响应中
            return {
                "access": data["access"],
                "refresh": data["refresh"],
                "user": UserSerializer(self.user).data
            }

        except serializers.ValidationError:
            raise
        except Exception as e:
            # 记录异常信息
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Login error: {str(e)}", exc_info=True)
            raise serializers.ValidationError({"non_field_errors": ["服务器内部错误，请稍后重试"]})

    def _get_failed_attempts_key(self, username):
        """获取登录失败次数的缓存键"""
        return f"login_failed_{username}"

    def _get_failed_attempts(self, username):
        """获取登录失败次数"""
        return cache.get(self._get_failed_attempts_key(username), 0)

    def _increment_failed_attempts(self, username):
        """增加登录失败次数"""
        key = self._get_failed_attempts_key(username)
        attempts = self._get_failed_attempts(username)
        cache.set(key, attempts + 1, timeout=self.LOCKOUT_TIME)

    def _clear_failed_attempts(self, username):
        """清除登录失败次数"""
        cache.delete(self._get_failed_attempts_key(username))

    def _is_account_locked(self, username):
        """检查账户是否被锁定"""
        attempts = self._get_failed_attempts(username)
        return attempts >= self.MAX_LOGIN_ATTEMPTS

    def _update_last_login(self, user):
        """更新用户最后登录信息"""
        user.last_login = timezone.now()
        if hasattr(self.context.get("request", None), "META"):
            user.last_login_ip = self.context["request"].META.get("REMOTE_ADDR")
        user.save(update_fields=["last_login", "last_login_ip"])


class ChangePasswordSerializer(serializers.Serializer):
    """修改密码序列化器"""

    old_password = serializers.CharField(required=True)
    new_password1 = serializers.CharField(required=True)
    new_password2 = serializers.CharField(required=True)

    def validate_new_password1(self, value):
        """验证新密码"""
        try:
            validate_password(value)
            return value
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)

    def validate(self, attrs):
        """验证密码"""
        try:
            if attrs["new_password1"] != attrs["new_password2"]:
                raise serializers.ValidationError({"new_password2": ["两次输入的新密码不匹配"]})
            return attrs
        except KeyError:
            raise serializers.ValidationError({"non_field_errors": ["密码字段不能为空"]})
        except serializers.ValidationError:
            raise
        except Exception as e:
            raise serializers.ValidationError({"non_field_errors": ["密码验证失败"]})
