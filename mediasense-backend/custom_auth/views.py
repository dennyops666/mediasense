from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import transaction
from datetime import timedelta
from rest_framework import permissions, status, viewsets, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser

from .permissions import ActionBasedPermission, IsAdmin, IsSelfOrAdmin, IsStaffOrAdmin, ReadOnly
from .serializers import ChangePasswordSerializer, CustomTokenObtainPairSerializer, UserCreateSerializer, UserSerializer

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    """用户登录视图"""

    permission_classes = [permissions.AllowAny]
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        """
        用户登录
        ---
        请求参数:
            - username: 用户名
            - password: 密码
        """
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            return Response(
                {
                    "message": "登录成功",
                    "data": {
                        "user": data["user"],
                        "token": {
                            "access": data["access"],
                            "refresh": data["refresh"]
                        }
                    }
                },
                status=status.HTTP_200_OK
            )

        except (TokenError, ValidationError) as e:
            return Response(
                {
                    "message": "登录失败",
                    "errors": e.message_dict if hasattr(e, "message_dict") else {"non_field_errors": [str(e)]}
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return Response(
                {
                    "message": "登录失败",
                    "errors": {"non_field_errors": ["服务器内部错误，请稍后重试"]}
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class UserViewSet(viewsets.ModelViewSet):
    """用户视图集"""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [ActionBasedPermission]
    action_permissions = {
        "list": [IsAdminUser],
        "create": [AllowAny],
        "retrieve": [IsAuthenticated],
        "update": [IsAuthenticated],
        "me": [IsAuthenticated],
        "change_password": [IsAuthenticated],
        "ban": [IsAdminUser],
        "activate": [IsAdminUser],
        "logout": [IsAuthenticated],
    }

    def create(self, request):
        """用户注册"""
        serializer = UserCreateSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "message": "注册成功",
                    "data": {
                        "user": UserSerializer(user).data,
                        "token": {
                            "access": str(refresh.access_token),
                            "refresh": str(refresh)
                        }
                    }
                },
                status=status.HTTP_201_CREATED
            )
        except ValidationError as e:
            return Response(
                {
                    "message": "注册失败",
                    "errors": e.detail
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {
                    "message": "注册失败",
                    "errors": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=["post"])
    def change_password(self, request):
        """修改密码"""
        if not request.user.is_authenticated:
            return Response(
                {
                    "message": "未认证",
                    "errors": {"detail": ["请先登录"]}
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        serializer = ChangePasswordSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            old_password = serializer.validated_data.get('old_password')
            new_password = serializer.validated_data.get('new_password1')
            
            if not request.user.check_password(old_password):
                return Response(
                    {
                        "message": "密码修改失败",
                        "errors": {"old_password": ["旧密码不正确"]}
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            request.user.set_password(new_password)
            request.user.save()
            
            # 使所有旧token失效
            for token in OutstandingToken.objects.filter(user=request.user):
                BlacklistedToken.objects.get_or_create(token=token)
            
            return Response(
                {
                    "message": "密码修改成功",
                    "data": None
                },
                status=status.HTTP_200_OK
            )
        except serializers.ValidationError as e:
            return Response(
                {
                    "message": "密码修改失败",
                    "errors": e.detail if hasattr(e, 'detail') else e.args[0]
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {
                    "message": "密码修改失败",
                    "errors": {"non_field_errors": ["服务器内部错误，请稍后重试"]}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["post"])
    def ban(self, request, pk=None):
        """封禁用户"""
        try:
            user = self.get_object()
            user.status = User.UserStatus.BANNED
            user.save()
            return Response({"message": "用户已被封禁"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {
                    "message": "封禁失败",
                    "errors": {"non_field_errors": ["服务器内部错误，请稍后重试"]}
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        """激活用户"""
        try:
            user = self.get_object()
            user.status = User.UserStatus.ACTIVE
            user.save()
            return Response({"message": "用户已被激活"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {
                    "message": "激活失败",
                    "errors": {"non_field_errors": ["服务器内部错误，请稍后重试"]}
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=["post"])
    def logout(self, request):
        """用户登出"""
        try:
            refresh_token = request.data.get("refresh_token")
            if not refresh_token:
                raise ValidationError({"refresh_token": ["刷新令牌不能为空"]})
            
            # 获取并加入黑名单
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            # 将当前的 access token 也加入黑名单
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                access_token = auth_header.split(' ')[1]
                # 解码 access token 获取其 jti
                access_token_obj = AccessToken(access_token)
                # 创建或获取 OutstandingToken 记录
                outstanding_token, _ = OutstandingToken.objects.get_or_create(
                    jti=access_token_obj.payload['jti'],
                    defaults={
                        'user': request.user,
                        'token': access_token,
                        'created_at': access_token_obj.current_time,
                        'expires_at': access_token_obj.current_time + timedelta(minutes=60)
                    }
                )
                # 将 token 加入黑名单
                BlacklistedToken.objects.get_or_create(token=outstanding_token)
            
            # 清除用户登录状态缓存
            cache.delete(f"user_login_{request.user.id}")
            return Response({"message": "登出成功"}, status=status.HTTP_200_OK)
        except (TokenError, ValidationError) as e:
            return Response(
                {
                    "message": "登出失败",
                    "errors": {"non_field_errors": [str(e)]}
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {
                    "message": "登出失败",
                    "errors": {"non_field_errors": ["服务器内部错误，请稍后重试"]}
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    def me(self, request):
        """获取当前用户信息"""
        serializer = self.get_serializer(request.user)
        return Response(
            {
                "message": "获取成功",
                "data": {
                    "user": serializer.data
                }
            },
            status=status.HTTP_200_OK
        )
