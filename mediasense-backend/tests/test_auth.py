import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from datetime import timedelta
import uuid

from .base import BaseTestCase
from custom_auth.models import User

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def test_user():
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )

@pytest.mark.django_db
class TestAuthAPI:
    """认证模块API测试"""

    def test_login_success(self, api_client, test_user):
        """测试用户登录成功"""
        url = reverse('api:auth:token_obtain')
        data = {
            'username': test_user.username,
            'password': 'testpass123'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_login_invalid_credentials(self, api_client):
        """测试无效凭证登录"""
        url = reverse('api:auth:token_obtain')
        data = {
            'username': 'wronguser',
            'password': 'wrongpass'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_token_refresh(self, api_client, test_user):
        """测试刷新令牌"""
        login_url = reverse('api:auth:token_obtain')
        refresh_url = reverse('api:auth:token_refresh')
        
        # 获取初始 token
        login_response = api_client.post(login_url, {
            'username': test_user.username,
            'password': 'testpass123'
        })
        refresh_token = login_response.data['refresh']
        
        # 刷新 token
        response = api_client.post(refresh_url, {'refresh': refresh_token})
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data

    def test_token_verify(self, api_client, test_user):
        """测试验证令牌"""
        login_url = reverse('api:auth:token_obtain')
        verify_url = reverse('api:auth:token_verify')
        
        # 获取 token
        login_response = api_client.post(login_url, {
            'username': test_user.username,
            'password': 'testpass123'
        })
        access_token = login_response.data['access']
        
        # 验证 token
        response = api_client.post(verify_url, {'token': access_token})
        assert response.status_code == status.HTTP_200_OK

    def test_invalid_token_verify(self, api_client):
        """测试验证无效令牌"""
        verify_url = reverse('api:auth:token_verify')
        response = api_client.post(verify_url, {'token': 'invalid_token'})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_protected_api_with_token(self, api_client, test_user):
        """测试使用令牌访问受保护的API"""
        login_url = reverse('api:auth:token_obtain')
        protected_url = reverse('api:auth:users-me')
        
        # 获取 token
        login_response = api_client.post(login_url, {
            'username': test_user.username,
            'password': 'testpass123'
        })
        access_token = login_response.data['access']
        
        # 使用 token 访问受保护的 API
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = api_client.get(protected_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == test_user.username

    def test_protected_api_without_token(self, api_client, test_user):
        """测试不使用令牌访问受保护的API"""
        protected_url = reverse('api:auth:users-me')
        response = api_client.get(protected_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

class TestUserLogin(BaseTestCase):
    """用户登录测试"""

    def setUp(self):
        super().setUp()
        self.url = reverse('api:custom_auth:token_obtain')
        self.data = {
            'username': self.user.username,
            'password': self.test_password
        }

    def test_login_success(self):
        """测试使用正确的用户名和密码登录"""
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_wrong_password(self):
        """测试使用错误密码登录"""
        data = {
            'username': self.user.username,
            'password': 'wrongpass'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_nonexistent_user(self):
        """测试使用不存在的用户名登录"""
        data = {
            'username': 'nonexistent',
            'password': 'testpass123'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_banned_user(self):
        """测试被禁用的用户登录"""
        self.user.is_active = False
        self.user.save()
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class TestJWTAuthentication(BaseTestCase):
    """JWT认证测试"""

    def setUp(self):
        """测试前准备"""
        super().setUp()
        self.token_url = reverse('api:custom_auth:token_obtain')
        self.token_refresh_url = reverse('api:custom_auth:token_refresh')
        self.token_verify_url = reverse('api:custom_auth:token_verify')
        self.me_url = reverse('api:custom_auth:users-me')
        self.protected_url = self.me_url  # 使用me_url作为受保护的端点

    def clear_credentials(self):
        """清除认证信息"""
        self.client.credentials()

    def test_token_obtain_pair(self):
        """测试获取token对"""
        response = self.client.post(self.token_url, {
            'username': self.user.username,
            'password': self.test_password
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_token_refresh(self):
        """测试刷新token"""
        # 获取初始token
        response = self.client.post(self.token_url, {
            'username': self.user.username,
            'password': self.test_password
        })
        refresh_token = response.data['refresh']
        old_access_token = response.data['access']

        # 使用refresh token获取新的access token
        response = self.client.post(self.token_refresh_url, {
            'refresh': refresh_token
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertNotEqual(response.data['access'], old_access_token)

    def test_token_verify(self):
        """测试验证token"""
        # 获取token
        response = self.client.post(self.token_url, {
            'username': self.user.username,
            'password': self.test_password
        })
        access_token = response.data['access']

        # 验证token
        response = self.client.post(self.token_verify_url, {
            'token': access_token
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_protected_endpoint_access(self):
        """测试使用token访问受保护的端点"""
        # 获取token
        response = self.client.post(self.token_url, {
            'username': self.user.username,
            'password': self.test_password
        })
        access_token = response.data['access']

        # 使用token访问me端点
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.user.username)

    def test_protected_endpoint_no_token(self):
        """测试无token访问受保护接口"""
        self.clear_credentials()
        response = self.client.get(self.protected_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_protected_endpoint_expired_token(self):
        """测试使用过期token访问受保护的端点"""
        # 获取token
        response = self.client.post(self.token_url, {
            'username': self.user.username,
            'password': self.test_password
        })
        access_token = response.data['access']

        # 修改token的过期时间
        token = AccessToken(access_token)
        token.set_exp(lifetime=-timedelta(days=1))
        expired_token = str(token)

        # 使用过期token访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {expired_token}')
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED) 