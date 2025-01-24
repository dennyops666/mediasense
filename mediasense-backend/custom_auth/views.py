from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework import permissions, status, viewsets, generics
from rest_framework.decorators import action, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError, AuthenticationFailed
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.exceptions import APIException
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Role, Permission
from .serializers import (
    CustomTokenObtainPairSerializer, 
    UserSerializer, 
    UserProfileSerializer,
    ChangePasswordSerializer,
    ResetPasswordSerializer,
    RoleSerializer,
    PermissionSerializer,
    UserRegistrationSerializer
)

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    """自定义令牌获取视图"""
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        """处理登录请求"""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        except (AuthenticationFailed, TokenError, ValidationError) as e:
            return Response(
                {"message": str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except APIException as e:
            return Response(
                {"message": str(e)},
                status=e.status_code
            )
        except Exception as e:
            return Response(
                {"message": "服务器内部错误，请稍后重试"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserViewSet(viewsets.ModelViewSet):
    """用户视图集"""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def handle_exception(self, exc):
        """处理异常"""
        if isinstance(exc, (InvalidToken, TokenError)):
            return Response(
                {"message": "认证失败"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        return super().handle_exception(exc)

    def get_permissions(self):
        """根据不同的操作设置权限"""
        if self.action in ['list', 'create', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """获取查询集"""
        if self.action == "me":
            return User.objects.filter(id=self.request.user.id)
        return super().get_queryset()

    @action(detail=False, methods=["get"])
    def me(self, request):
        """获取当前用户信息"""
        if not request.user.is_authenticated:
            return Response(
                {"message": "认证失败"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=["get", "put"])
    def profile(self, request):
        """获取或更新用户档案"""
        if request.method == "GET":
            serializer = UserProfileSerializer(request.user)
            return Response(serializer.data)
        else:
            serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def change_password(self, request):
        """修改密码"""
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "密码修改成功"})

    @action(detail=False, methods=["post"])
    def reset_password(self, request):
        """重置密码"""
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "密码重置邮件已发送"})

class UserRegistrationView(generics.CreateAPIView):
    """用户注册视图"""
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserRegistrationSerializer

class SessionInfoView(APIView):
    """会话信息视图"""
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response({
            'is_authenticated': True,
            'user_id': request.user.id,
            'username': request.user.username,
            'email': request.user.email
        })

class LogoutView(APIView):
    """注销视图"""
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh_token")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class CheckPermissionView(APIView):
    """权限检查视图"""
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        permission_name = request.data.get('permission')
        if not permission_name:
            return Response(
                {'error': 'Permission name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user_permissions = set()
        for role in request.user.roles.all():
            user_permissions.update(role.get_all_permissions())

        has_permission = any(
            p.name == permission_name for p in user_permissions
        )
        return Response({'has_permission': has_permission})

class RoleListView(generics.ListCreateAPIView):
    """角色列表视图"""
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = (IsAuthenticated,)

class RoleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """角色详情视图"""
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = (IsAuthenticated,)

class PermissionListView(generics.ListAPIView):
    """权限列表视图"""
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = (IsAuthenticated,)
