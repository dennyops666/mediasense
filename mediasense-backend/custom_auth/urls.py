from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from .views import CustomTokenObtainPairView, UserViewSet

# API路由
router = DefaultRouter()
router.register(r"users", UserViewSet)

app_name = "custom_auth"

urlpatterns = [
    # 认证相关
    path("token/", CustomTokenObtainPairView.as_view(), name="token_obtain"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    # 获取当前用户信息
    path("me/", UserViewSet.as_view({"get": "me"}), name="users-me"),
    # 用户管理相关（需要认证）
    path("", include(router.urls)),
]
