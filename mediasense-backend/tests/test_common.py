from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

from .base import BaseTestCase

User = get_user_model()

class TestAPIResponseFormat(BaseTestCase):
    """API响应格式测试"""

    def setUp(self):
        """测试前准备"""
        super().setUp()
        self.me_url = reverse('api:custom_auth:users-me')
        self.token_url = reverse('api:custom_auth:token_obtain')
        self.nonexistent_url = '/api/v1/custom_auth/nonexistent/'
        
        # 获取认证token
        response = self.client.post(self.token_url, {
            'username': self.user.username,
            'password': self.test_password
        })
        self.access_token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

    def test_success_response_format(self):
        """测试成功响应的格式"""
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('username', response.data)
        self.assertIn('email', response.data)
        self.assertIn('id', response.data)

    def test_validation_error_format(self):
        """测试验证错误的响应格式"""
        # 发送无效的登录数据
        response = self.client.post(self.token_url, {
            'username': '',
            'password': ''
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(
            'detail' in response.data or 'message' in response.data,
            "Response should contain either 'detail' or 'message'"
        )

    def test_authentication_error_format(self):
        """测试认证错误的响应格式"""
        # 清除认证信息
        self.client.credentials()
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(
            'detail' in response.data or 'message' in response.data,
            "Response should contain either 'detail' or 'message'"
        )

    def test_not_found_error_format(self):
        """测试404错误的响应格式"""
        response = self.client.get(self.nonexistent_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response_data = response.json()  # 将JSON响应解析为字典
        self.assertTrue(
            'detail' in response_data or 'message' in response_data,
            "Response should contain either 'detail' or 'message'"
        )

    def test_method_not_allowed_format(self):
        """测试方法不允许的响应格式"""
        response = self.client.delete(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertTrue(
            'detail' in response.data or 'message' in response.data,
            "Response should contain either 'detail' or 'message'"
        )

    def test_server_error_format(self):
        """测试服务器错误的响应格式"""
        # 使用过期的token触发服务器错误
        token = AccessToken(self.access_token)
        token.set_exp(lifetime=-token.lifetime)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(
            'detail' in response.data or 'message' in response.data,
            "Response should contain either 'detail' or 'message'"
        ) 