import pytest
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from monitoring.async_client import AsyncAPIClient
from tests.factories import UserFactory
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone

class BaseTestCase(TestCase):
    """基础测试类"""

    def setUp(self):
        """测试前准备"""
        super().setUp()
        self.client = APIClient()
        self.user = UserFactory(
            username='testuser',
            email='test@example.com',
            is_active=True,
            user_type='admin',
            is_staff=True,
            is_superuser=True
        )
        self.test_password = 'testpass123'
        self.user.set_password(self.test_password)
        self.user.save()

        # 常用URL
        self.token_url = '/v1/auth/token/'
        self.token_refresh_url = '/v1/auth/token/refresh/'
        self.token_verify_url = '/v1/auth/token/verify/'
        self.me_url = '/v1/auth/me/'

    def tearDown(self):
        """测试后清理"""
        self.client.credentials()

class BaseAPITestCase(APITestCase):
    """基础API测试类"""

    def setUp(self):
        """测试前准备"""
        super().setUp()
        self.client = APIClient()
        self.async_client = AsyncAPIClient()
        
        # 创建测试用户
        self.user = UserFactory(
            username='testuser',
            email='test@example.com',
            is_active=True,
            user_type='admin',
            is_staff=True,
            is_superuser=True
        )
        
        # 生成token
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        
        # 设置认证头
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        self.async_client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

    def _get_token(self, user):
        """获取用户token"""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def authenticate(self, user='user'):
        """设置用户认证"""
        if isinstance(user, str):
            user = UserFactory(user_type=user)
        token = self._get_token(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        return user, token

    def tearDown(self):
        """测试后清理"""
        self.client.credentials()
        self.async_client.credentials()

    def get_url(self, path):
        """获取完整的 URL 路径"""
        if not path.startswith('/'):
            path = f'/{path}'
        return path 