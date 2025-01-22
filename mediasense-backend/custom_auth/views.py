from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError, AuthenticationFailed
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import APIException

from .permissions import ActionBasedPermission
from .serializers import CustomTokenObtainPairSerializer, UserSerializer

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


class UserViewSet(viewsets.GenericViewSet):
    """用户视图集"""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """获取查询集"""
        if self.action == "me":
            return User.objects.filter(id=self.request.user.id)
        return super().get_queryset()

    @action(detail=False, methods=["get"], authentication_classes=[JWTAuthentication], permission_classes=[IsAuthenticated])
    def me(self, request):
        """获取当前用户信息"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
