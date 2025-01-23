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
        self.protected_url = '/v1/auth/me/'

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
        self.assertEqual(response.status_code, 401)

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