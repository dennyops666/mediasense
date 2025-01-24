from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from .views import CustomTokenObtainPairView, UserViewSet, UserRegistrationView, SessionInfoView, LogoutView, CheckPermissionView, RoleListView, RoleDetailView, PermissionListView

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

    # 用户注册和登录
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token-verify'),
    
    # 会话管理
    path('session-info/', SessionInfoView.as_view(), name='session-info'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # 权限管理
    path('check-permission/', CheckPermissionView.as_view(), name='check-permission'),
    path('roles/', RoleListView.as_view(), name='role-list'),
    path('roles/<int:pk>/', RoleDetailView.as_view(), name='role-detail'),
    path('permissions/', PermissionListView.as_view(), name='permission-list'),
]
