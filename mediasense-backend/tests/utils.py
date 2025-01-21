from django.test import TestCase, Client
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
import pytest
import asyncio
import json
import os

from .test_ai import AsyncAPIClient

User = get_user_model()

class BaseTestCase(TestCase):
    """基础测试类"""
    
    def setUp(self):
        self.client = Client()
        # 创建测试用户
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.admin_user = User.objects.create_superuser(
            username='test_admin',
            email='admin@example.com',
            password='admin123'
        )

    def tearDown(self):
        User.objects.all().delete()

class BaseAPITestCase(APITestCase):
    """基础API测试类"""
    
    def setUp(self):
        self.client = AsyncAPIClient()  # 使用异步客户端
        self.test_password = 'testpass123'  # 设置测试密码
        # 创建测试用户
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password=self.test_password
        )
        self.admin_user = User.objects.create_superuser(
            username='test_admin',
            email='admin@example.com',
            password='admin123'
        )
        # 生成测试token
        self.user_token = self._get_token(self.user)
        self.admin_token = self._get_token(self.admin_user)

    def _get_token(self, user):
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    def authenticate(self, user='user'):
        """设置认证头"""
        token = self.admin_token if user == 'admin' else self.user_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token["access"]}')

    def tearDown(self):
        self.client.credentials()  # 清除认证
        User.objects.all().delete() 

class AsyncAPIClient(APIClient, AsyncClient):
    """支持异步操作的 API 客户端"""

    async def get(self, path, data=None, follow=False, **extra):
        """异步 GET 请求"""
        response = await super().get(path, data=data, follow=follow, **extra)
        if asyncio.iscoroutine(response):
            response = await response
        return response

    async def post(self, path, data=None, format='json', content_type=None, follow=False, **extra):
        """异步 POST 请求"""
        if format == 'json' and data is not None:
            data = json.dumps(data)
            content_type = content_type or 'application/json'
        response = await super().post(path, data=data, content_type=content_type, follow=follow, **extra)
        if asyncio.iscoroutine(response):
            response = await response
        return response

    async def put(self, path, data=None, format='json', content_type=None, follow=False, **extra):
        """异步 PUT 请求"""
        if format == 'json' and data is not None:
            data = json.dumps(data)
            content_type = content_type or 'application/json'
        response = await super().put(path, data=data, content_type=content_type, follow=follow, **extra)
        if asyncio.iscoroutine(response):
            response = await response
        return response

    async def patch(self, path, data=None, format='json', content_type=None, follow=False, **extra):
        """异步 PATCH 请求"""
        if format == 'json' and data is not None:
            data = json.dumps(data)
            content_type = content_type or 'application/json'
        response = await super().patch(path, data=data, content_type=content_type, follow=follow, **extra)
        if asyncio.iscoroutine(response):
            response = await response
        return response

    async def delete(self, path, data=None, follow=False, **extra):
        """异步 DELETE 请求"""
        response = await super().delete(path, data=data, follow=follow, **extra)
        if asyncio.iscoroutine(response):
            response = await response
        return response

    async def force_authenticate(self, user=None, token=None):
        """异步强制认证"""
        os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
        try:
            super().force_authenticate(user=user, token=token)
        finally:
            del os.environ['DJANGO_ALLOW_ASYNC_UNSAFE']

    async def force_login(self, user):
        """异步强制登录"""
        os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
        try:
            super().force_login(user)
        finally:
            del os.environ['DJANGO_ALLOW_ASYNC_UNSAFE']

    async def logout(self):
        """异步登出"""
        os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
        try:
            super().logout()
        finally:
            del os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] 