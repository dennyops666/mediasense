import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from asgiref.sync import sync_to_async
import asyncio
from django.db import transaction

from tests.async_client import AsyncAPIClient
from tests.factories import UserFactory

User = get_user_model()

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class BaseTestCase(APITestCase):
    """基础测试类"""

    async def asyncSetUp(self):
        """异步设置"""
        # 开始事务
        await sync_to_async(transaction.atomic).__call__()
        
        self.client = AsyncAPIClient()
        self.user = await UserFactory.acreate()
        await self.client.force_authenticate(user=self.user)

    async def asyncTearDown(self):
        """异步清理"""
        await self.client.force_authenticate(user=None)
        await self.client.logout()
        self.client = None
        self.user = None
        
        # 回滚事务以清理测试数据
        await sync_to_async(transaction.rollback).__call__()

    def setUp(self):
        """设置"""
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.asyncSetUp())

    def tearDown(self):
        """清理"""
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.asyncTearDown()) 