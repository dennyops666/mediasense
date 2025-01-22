import pytest
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from monitoring.async_client import AsyncAPIClient
from tests.factories import UserFactory
import uuid
from custom_auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework_simplejwt.tokens import RefreshToken

class AsyncAPITestCase(APITestCase):
    """异步API测试类"""

    def setUp(self):
        """同步设置"""
        super().setUp()
        import asyncio
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.asyncSetUp())

    async def asyncSetUp(self):
        """异步设置"""
        from rest_framework.test import APIClient
        self.client = APIClient()
        self.test_password = 'Test@123456'
        
        # 创建测试用户
        self.user = await User.objects.acreate_user(
            username=f'testuser_{uuid.uuid4().hex[:8]}',
            email=f'test_{uuid.uuid4().hex[:8]}@example.com',
            password=self.test_password,
            phone=f'1{uuid.uuid4().hex[:10]}'
        )
        
        # 创建管理员用户
        self.admin_user = await User.objects.acreate_superuser(
            username=f'admin_{uuid.uuid4().hex[:8]}',
            email=f'admin_{uuid.uuid4().hex[:8]}@example.com',
            password=self.test_password,
            phone=f'1{uuid.uuid4().hex[:10]}'
        )
        
        # 生成测试token
        self.user_token = self._get_token(self.user)
        self.admin_token = self._get_token(self.admin_user)
        self.access_token = self.user_token['access']
        self.refresh_token = self.user_token['refresh']
        
        # 设置默认认证头
        await self.authenticate()
        
        # 设置默认属性
        self.url = None
        self.data = None

    def _get_token(self, user):
        """获取用户token"""
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    async def authenticate(self, user='user'):
        """异步设置认证头"""
        token = self.admin_token if user == 'admin' else self.user_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token["access"]}')

    async def clear_credentials(self):
        """异步清除认证头"""
        self.client.credentials()

    def tearDown(self):
        """同步清理"""
        import asyncio
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.asyncTearDown())
        super().tearDown()

    async def asyncTearDown(self):
        """异步清理"""
        await self.clear_credentials()
        await User.objects.all().adelete()

class BaseTestCase(APITestCase):
    """基础测试类"""
    
    def setUp(self):
        """设置测试环境"""
        super().setUp()
        self.client = APIClient()
        self.test_password = 'Test@123456'
        
        # 创建测试用户
        self.user = User.objects.create_user(
            username=f'testuser_{uuid.uuid4().hex[:8]}',
            email=f'test_{uuid.uuid4().hex[:8]}@example.com',
            password=self.test_password,
            phone=f'1{uuid.uuid4().hex[:10]}'
        )
        
        # 创建管理员用户
        self.admin_user = User.objects.create_superuser(
            username=f'admin_{uuid.uuid4().hex[:8]}',
            email=f'admin_{uuid.uuid4().hex[:8]}@example.com',
            password=self.test_password,
            phone=f'1{uuid.uuid4().hex[:10]}'
        )
        
        # 生成测试token
        self.user_token = self._get_token(self.user)
        self.admin_token = self._get_token(self.admin_user)
        self.access_token = self.user_token['access']
        self.refresh_token = self.user_token['refresh']
        
        # 设置默认认证头
        self.authenticate()
        
        # 设置默认属性
        self.url = None
        self.data = None

    def _get_token(self, user):
        """获取用户token"""
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    def authenticate(self, user='user'):
        """设置认证头"""
        token = self.admin_token if user == 'admin' else self.user_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token["access"]}')

    def clear_credentials(self):
        """清除认证头"""
        self.client.credentials()

    def tearDown(self):
        """清理测试环境"""
        self.clear_credentials()
        User.objects.all().delete()
        super().tearDown()

class BaseAPITestCase(AsyncAPITestCase):
    """基础API测试类"""
    
    async def asyncSetUp(self):
        """异步设置"""
        await super().asyncSetUp()
        self.url = None
        self.data = None
        # 设置默认认证头
        await self.authenticate()

    async def authenticate(self, user='user'):
        """异步设置认证头"""
        token = self.admin_token if user == 'admin' else self.user_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token["access"]}')

    async def asyncTearDown(self):
        """异步清理"""
        await self.clear_credentials()
        await super().asyncTearDown() 