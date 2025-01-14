from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import CustomTokenObtainPairView, UserViewSet

# API路由
router = DefaultRouter()
router.register(r"users", UserViewSet)

app_name = "custom_auth"

urlpatterns = [
    # 认证相关
    path("token/", CustomTokenObtainPairView.as_view(), name="token_obtain"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # 用户注册
    path("register/", UserViewSet.as_view({"post": "create"}), name="register"),
    # 用户登出
    path("logout/", UserViewSet.as_view({"post": "logout"}), name="logout"),
    # 获取当前用户信息
    path("me/", UserViewSet.as_view({"get": "me"}), name="users-me"),
    # 修改密码
    path("change-password/", UserViewSet.as_view({"post": "change_password"}), name="users-change-password"),
    # 用户管理相关（需要认证）
    path("", include(router.urls)),
]
