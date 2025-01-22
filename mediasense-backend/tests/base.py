import pytest
from django.test import TestCase
from rest_framework.test import APITestCase
from monitoring.async_client import AsyncAPIClient
from tests.factories import UserFactory

class BaseTestCase(APITestCase):
    """基础测试类"""

    client_class = AsyncAPIClient

    @pytest.mark.asyncio
    async def asyncSetUp(self):
        """异步设置"""
        self.user = await UserFactory.acreate()
        self.client.force_authenticate(user=self.user)

    async def setUp(self):
        """设置测试环境"""
        await self.asyncSetUp()

    async def tearDown(self):
        """清理测试环境"""
        await self.client.logout() 