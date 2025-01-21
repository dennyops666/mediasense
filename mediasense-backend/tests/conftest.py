import pytest
from django.core.management import call_command
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
import uuid
import asyncio
from asgiref.sync import sync_to_async

User = get_user_model()

@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """设置测试数据库"""
    pass

@pytest.fixture
def api_client():
    """返回API测试客户端"""
    return APIClient()

@pytest.fixture
def test_password():
    """返回测试用户密码"""
    return 'testpass123'

@pytest.fixture
async def create_user(db, test_password):
    """创建并返回测试用户的工厂函数"""
    async def make_user(**kwargs):
        kwargs['password'] = test_password
        if 'username' not in kwargs:
            kwargs['username'] = str(uuid.uuid4())
        if 'email' not in kwargs:
            kwargs['email'] = f"{kwargs['username']}@example.com"
        return await sync_to_async(User.objects.create_user)(**kwargs)
    return make_user

@pytest.fixture
async def auto_login_user(db, client, create_user, test_password):
    """创建并登录用户"""
    async def make_auto_login(user=None):
        if user is None:
            user = await create_user()
        await sync_to_async(client.login)(username=user.username, password=test_password)
        return client, user
    return make_auto_login

@pytest.fixture
async def api_client_with_credentials(db, create_user, api_client):
    """创建带认证的API客户端"""
    user = await create_user()
    api_client.force_authenticate(user=user)
    return api_client, user 