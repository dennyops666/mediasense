import pytest
from django.core.management import call_command
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """设置测试数据库"""
    with django_db_blocker.unblock():
        # 加载初始数据
        call_command('loaddata', 'initial_data.json')

@pytest.fixture
def api_client():
    """返回API测试客户端"""
    return APIClient()

@pytest.fixture
def test_password():
    """返回测试用户密码"""
    return 'testpass123'

@pytest.fixture
def create_user(db, test_password):
    """创建并返回测试用户的工厂函数"""
    def make_user(**kwargs):
        kwargs['password'] = test_password
        if 'username' not in kwargs:
            kwargs['username'] = 'testuser'
        if 'email' not in kwargs:
            kwargs['email'] = 'test@example.com'
        return User.objects.create_user(**kwargs)
    return make_user

@pytest.fixture
def auto_login_user(db, client, create_user, test_password):
    """创建并登录用户"""
    def make_auto_login(user=None):
        if user is None:
            user = create_user()
        client.login(username=user.username, password=test_password)
        return client, user
    return make_auto_login

@pytest.fixture
def api_client_with_credentials(db, create_user, api_client):
    """创建带认证的API客户端"""
    user = create_user()
    api_client.force_authenticate(user=user)
    yield api_client
    api_client.force_authenticate(user=None) 