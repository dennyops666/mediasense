from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from .views import CustomTokenObtainPairView, UserViewSet

app_name = "custom_auth"

# API路由
router = DefaultRouter(trailing_slash=False)
router.include_format_suffixes = False
router.register(r"users", UserViewSet, basename="users")

urlpatterns = [
    # JWT认证相关
    path("token/", CustomTokenObtainPairView.as_view(), name="token_obtain"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    
    # 用户相关
    path("me/", UserViewSet.as_view({"get": "me"}), name="users-me"),
    path("profile/", UserViewSet.as_view({"get": "profile", "put": "update_profile"}), name="users-profile"),
    path("password/change/", UserViewSet.as_view({"post": "change_password"}), name="users-change-password"),
    path("password/reset/", UserViewSet.as_view({"post": "reset_password"}), name="users-reset-password"),
    
    # 用户管理相关（需要管理员权限）
    path("", include(router.urls)),
]
