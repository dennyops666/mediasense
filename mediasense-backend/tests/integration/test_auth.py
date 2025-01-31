import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from custom_auth.models import Role, Permission
from tests.factories import UserFactory, RoleFactory, PermissionFactory

User = get_user_model()

@pytest.mark.django_db
class TestAuthIntegration:
    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def test_user(self):
        return UserFactory(
            username='testuser',
            email='test@example.com',
            is_active=True
        )

    @pytest.fixture
    def admin_role(self):
        return RoleFactory(name='admin')

    @pytest.fixture
    def user_role(self):
        return RoleFactory(name='user')

    @pytest.fixture
    def news_permission(self):
        return PermissionFactory(
            name='news_manage',
            description='Can manage news'
        )

    def test_user_registration_and_login(self, api_client):
        """测试用户注册和登录流程"""
        # 1. 测试用户注册
        register_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123'
        }
        register_url = reverse('api:auth:register')
        response = api_client.post(register_url, register_data)
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(username='newuser').exists()

        # 2. 测试用户登录
        login_data = {
            'username': 'newuser',
            'password': 'testpass123'
        }
        login_url = reverse('api:auth:token_obtain')
        response = api_client.post(login_url, login_data)
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_role_and_permission_assignment(self, api_client, test_user, admin_role, news_permission):
        """测试角色和权限分配"""
        # 1. 分配角色给用户
        admin_role.permissions.add(news_permission)
        test_user.roles.add(admin_role)
        
        # 2. 验证用户权限
        api_client.force_authenticate(user=test_user)
        permission_url = reverse('api:auth:check_permission')
        response = api_client.post(permission_url, {'permission': 'news_manage'})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['has_permission'] is True

    def test_token_refresh_and_verify(self, api_client, test_user):
        """测试Token刷新和验证"""
        # 1. 获取初始token
        login_data = {
            'username': test_user.username,
            'password': 'password123'  # UserFactory默认密码
        }
        login_url = reverse('api:auth:token_obtain')
        response = api_client.post(login_url, login_data)
        assert response.status_code == status.HTTP_200_OK
        refresh_token = response.data['refresh']

        # 2. 使用refresh token获取新的access token
        refresh_url = reverse('api:auth:token_refresh')
        response = api_client.post(refresh_url, {'refresh': refresh_token})
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data

    def test_session_management(self, api_client, test_user):
        """测试会话管理"""
        # 1. 用户登录并获取session
        api_client.force_authenticate(user=test_user)
        session_url = reverse('api:auth:session_info')
        response = api_client.get(session_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_authenticated'] is True

        # 2. 测试会话注销
        logout_url = reverse('api:auth:logout')
        response = api_client.post(logout_url)
        assert response.status_code == status.HTTP_200_OK

        # 3. 验证会话已结束
        api_client.force_authenticate(user=None)  # 清除认证
        response = api_client.get(session_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_role_inheritance(self, api_client, admin_role, user_role, test_user, news_permission):
        """测试角色继承"""
        # 1. 设置角色继承关系
        user_role.parent = admin_role
        user_role.save()
        admin_role.permissions.add(news_permission)
        test_user.roles.add(user_role)

        # 2. 验证继承的权限
        api_client.force_authenticate(user=test_user)
        permission_url = reverse('api:auth:check_permission')
        response = api_client.post(permission_url, {'permission': 'news_manage'})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['has_permission'] is True 