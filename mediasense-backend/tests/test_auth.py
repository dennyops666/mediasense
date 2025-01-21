import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
import time
import asyncio

from .utils import BaseAPITestCase
from .test_ai import AsyncAPIClient
from django.test import TestCase
from custom_auth.models import User
from tests.base import BaseTestCase

User = get_user_model()

class TestUserLogin(BaseAPITestCase):
    """用户登录测试"""

    def setUp(self):
        """测试初始化"""
        super().setUp()
        self.test_user = self.user  # 使用BaseAPITestCase中创建的用户
        self.test_password = 'testpass123'  # 使用BaseAPITestCase中的默认密码
        self.client = AsyncAPIClient()  # 使用异步客户端

    @pytest.mark.asyncio
    async def test_login_success(self):
        """测试使用正确的用户名和密码登录"""
        url = reverse('custom_auth:token_obtain')
        data = {
            'username': self.test_user.username,
            'password': self.test_password
        }
        response = await self.client.post(url, data)
        print("Response data:", response.data)  # 打印响应内容
        assert response.status_code == status.HTTP_200_OK
        assert 'message' in response.data
        assert response.data['message'] == '登录成功'
        assert 'data' in response.data
        assert 'user' in response.data['data']
        assert 'token' in response.data['data']
        assert 'access' in response.data['data']['token']
        assert 'refresh' in response.data['data']['token']
        assert response.data['data']['user']['username'] == self.test_user.username

    @pytest.mark.asyncio
    async def test_login_wrong_password(self):
        """测试使用错误密码登录"""
        url = reverse('custom_auth:token_obtain')
        data = {
            'username': self.test_user.username,
            'password': 'wrongpass'
        }
        response = await self.client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'message' in response.data
        assert response.data['message'] == '登录失败'
        assert 'errors' in response.data

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self):
        """测试使用不存在的用户名登录"""
        url = reverse('custom_auth:token_obtain')
        data = {
            'username': 'nonexistentuser',
            'password': self.test_password
        }
        response = await self.client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'message' in response.data
        assert response.data['message'] == '登录失败'
        assert 'errors' in response.data

    @pytest.mark.asyncio
    async def test_login_banned_user(self):
        """测试被禁用的用户登录"""
        # 禁用测试用户
        self.test_user.is_active = False
        self.test_user.save()

        url = reverse('custom_auth:token_obtain')
        data = {
            'username': self.test_user.username,
            'password': self.test_password
        }
        response = await self.client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'message' in response.data
        assert response.data['message'] == '登录失败'
        assert 'errors' in response.data

class TestJWTTokenVerification(BaseAPITestCase):
    """JWT Token验证测试"""

    def setUp(self):
        """测试初始化"""
        super().setUp()
        self.test_user = self.user  # 使用BaseAPITestCase中创建的用户
        self.test_password = 'testpass123'  # 使用BaseAPITestCase中的默认密码
        self.access_token = self.user_token['access']
        self.refresh_token = self.user_token['refresh']
        self.client = AsyncAPIClient()  # 使用异步客户端
        # 设置认证头
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

    @pytest.mark.asyncio
    async def test_valid_token_access(self):
        """测试使用有效token访问"""
        response = await self.client.get(reverse('custom_auth:users-me'))
        assert response.status_code == status.HTTP_200_OK
        assert 'message' in response.data
        assert response.data['message'] == '获取成功'
        assert 'data' in response.data
        assert 'user' in response.data['data']

    @pytest.mark.asyncio
    async def test_expired_token_access(self):
        """测试使用过期token访问"""
        # 使用一个无效的token
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNTE2MjM5MDIyLCJpYXQiOjE1MTYyMzkwMjIsImp0aSI6ImY3YzJkYzFkYjg4YzQ3OWFiZWY5M2RmODUyMGU3OTI4IiwidXNlcl9pZCI6MX0.invalid_signature')
        response = await self.client.get(reverse('custom_auth:users-me'))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_invalid_token_access(self):
        """测试使用无效token访问"""
        # 使用格式错误的token
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid.token.format')
        response = await self.client.get(reverse('custom_auth:users-me'))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_blacklisted_token_access(self):
        """测试使用已注销token访问"""
        # 先获取一个有效的响应，确保token有效
        response = await self.client.get(reverse('custom_auth:users-me'))
        assert response.status_code == status.HTTP_200_OK

        # 注销当前token
        url = reverse('custom_auth:logout')
        data = {
            'refresh_token': self.refresh_token
        }
        logout_response = await self.client.post(url, data)
        assert logout_response.status_code == status.HTTP_200_OK
        
        # 等待token黑名单生效
        await asyncio.sleep(1)
        
        # 使用已注销的token访问
        response = await self.client.get(reverse('custom_auth:users-me'))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'detail' in response.data
        assert 'Token is blacklisted' in str(response.data['detail'])

class TestUserRegistration(BaseAPITestCase):
    """用户注册测试"""

    def setUp(self):
        """测试初始化"""
        super().setUp()
        self.test_user = self.user  # 使用BaseAPITestCase中创建的用户
        self.test_password = 'testpass123'  # 使用BaseAPITestCase中的默认密码
        self.client = AsyncAPIClient()  # 使用异步客户端

    @pytest.mark.asyncio
    async def test_valid_registration(self):
        """测试使用有效信息注册新用户"""
        url = reverse('custom_auth:register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'NewPass@123',
            'password2': 'NewPass@123',
            'phone': '13800138000'
        }
        response = await self.client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert 'message' in response.data
        assert response.data['message'] == '注册成功'
        assert 'data' in response.data
        assert 'user' in response.data['data']
        assert 'token' in response.data['data']
        assert 'access' in response.data['data']['token']
        assert 'refresh' in response.data['data']['token']

    @pytest.mark.asyncio
    async def test_duplicate_username_registration(self):
        """测试使用已存在的用户名注册"""
        url = reverse('custom_auth:register')
        data = {
            'username': self.test_user.username,
            'email': 'another@example.com',
            'password': 'NewPass@123',
            'password2': 'NewPass@123',
            'phone': '13800138000'
        }
        response = await self.client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'message' in response.data
        assert response.data['message'] == '注册失败'
        assert 'errors' in response.data

    @pytest.mark.asyncio
    async def test_invalid_email_registration(self):
        """测试使用无效的邮箱格式注册"""
        url = reverse('custom_auth:register')
        data = {
            'username': 'newuser',
            'email': 'invalid-email',
            'password': 'NewPass@123',
            'password2': 'NewPass@123',
            'phone': '13800138000'
        }
        response = await self.client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'message' in response.data
        assert response.data['message'] == '注册失败'
        assert 'errors' in response.data

    @pytest.mark.asyncio
    async def test_weak_password_registration(self):
        """测试使用不符合要求的密码注册"""
        url = reverse('custom_auth:register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': '123',
            'password2': '123',
            'phone': '13800138000'
        }
        response = await self.client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'message' in response.data
        assert response.data['message'] == '注册失败'
        assert 'errors' in response.data

class TestPasswordReset(BaseAPITestCase):
    """密码重置测试"""

    def setUp(self):
        """测试初始化"""
        super().setUp()
        self.test_user = self.user  # 使用BaseAPITestCase中创建的用户
        self.test_password = 'testpass123'  # 使用BaseAPITestCase中的默认密码
        self.client = AsyncAPIClient()  # 使用异步客户端
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_token["access"]}')

    @pytest.mark.asyncio
    async def test_change_password(self):
        """测试修改密码"""
        data = {
            'old_password': self.test_password,
            'new_password1': 'NewPass@123',  # 使用符合要求的强密码
            'new_password2': 'NewPass@123'
        }
        response = await self.client.post(reverse('custom_auth:users-change-password'), data)
        assert response.status_code == status.HTTP_200_OK
        assert 'message' in response.data
        assert response.data['message'] == '密码修改成功'

    @pytest.mark.asyncio
    async def test_change_password_wrong_old_password(self):
        """测试使用错误的旧密码修改密码"""
        data = {
            'old_password': 'wrongpassword',
            'new_password1': 'NewPass@123',
            'new_password2': 'NewPass@123'
        }
        response = await self.client.post(reverse('custom_auth:users-change-password'), data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'message' in response.data
        assert response.data['message'] == '密码修改失败'

    @pytest.mark.asyncio
    async def test_change_password_mismatch(self):
        """测试新密码不匹配的情况"""
        data = {
            'old_password': self.test_password,
            'new_password1': 'NewPass@123',
            'new_password2': 'DifferentPass@123'
        }
        response = await self.client.post(reverse('custom_auth:users-change-password'), data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'message' in response.data
        assert response.data['message'] == '密码修改失败'

    @pytest.mark.asyncio
    async def test_change_password_weak_password(self):
        """测试使用弱密码修改密码"""
        data = {
            'old_password': self.test_password,
            'new_password1': '123',
            'new_password2': '123'
        }
        response = await self.client.post(reverse('custom_auth:users-change-password'), data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'message' in response.data
        assert response.data['message'] == '密码修改失败'

    @pytest.mark.asyncio
    async def test_change_password_unauthorized(self):
        """测试未认证用户修改密码"""
        # 清除认证头
        self.client.credentials()
        
        data = {
            'old_password': self.test_password,
            'new_password1': 'NewPass@123',
            'new_password2': 'NewPass@123'
        }
        response = await self.client.post(reverse('custom_auth:users-change-password'), data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

class TestConcurrentAuth(BaseAPITestCase):
    """并发认证测试"""

    def setUp(self):
        """测试初始化"""
        super().setUp()
        self.test_user = self.user
        self.test_password = 'testpass123'
        self.login_url = reverse('custom_auth:token_obtain')
        self.client = AsyncAPIClient()  # 使用异步客户端

    @pytest.mark.asyncio
    async def test_concurrent_login_attempts(self):
        """测试并发登录尝试"""
        # 使用错误密码尝试登录5次
        for _ in range(5):
            response = await self.client.post(self.login_url, {
                'username': self.test_user.username,
                'password': 'wrong_password'
            })
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert response.data['message'] == '登录失败'
            assert 'non_field_errors' in response.data['errors']

        # 第6次尝试登录，即使使用正确密码也应该被锁定
        response = await self.client.post(self.login_url, {
            'username': self.test_user.username,
            'password': self.test_password
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['message'] == '登录失败'
        assert 'non_field_errors' in response.data['errors']

    @pytest.mark.asyncio
    async def test_concurrent_password_changes(self):
        """测试并发修改密码"""
        # 创建两个客户端模拟并发
        client1 = AsyncAPIClient()
        client2 = AsyncAPIClient()
        
        # 设置认证头
        token = self.user_token['access']
        client1.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        client2.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # 客户端1修改密码
        data1 = {
            'old_password': self.test_password,
            'new_password1': 'NewPass@123',
            'new_password2': 'NewPass@123'
        }
        response1 = await client1.post(reverse('custom_auth:users-change-password'), data1)
        assert response1.status_code == status.HTTP_200_OK
        
        # 等待密码修改和token黑名单生效
        await asyncio.sleep(1)
        
        # 客户端2使用旧密码尝试修改密码
        data2 = {
            'old_password': self.test_password,
            'new_password1': 'AnotherPass@123',
            'new_password2': 'AnotherPass@123'
        }
        response2 = await client2.post(reverse('custom_auth:users-change-password'), data2)
        assert response2.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'detail' in response2.data
        assert 'Token is blacklisted' in str(response2.data['detail'])

    @pytest.mark.asyncio
    async def test_token_reuse_after_password_change(self):
        """测试修改密码后旧token是否失效"""
        # 设置认证头
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_token["access"]}')
        
        # 先获取一个有效的响应，确保token有效
        response = await self.client.get(reverse('custom_auth:users-me'))
        assert response.status_code == status.HTTP_200_OK
        
        # 修改密码
        change_data = {
            'old_password': self.test_password,
            'new_password1': 'NewPass@123',
            'new_password2': 'NewPass@123'
        }
        response = await self.client.post(reverse('custom_auth:users-change-password'), change_data)
        assert response.status_code == status.HTTP_200_OK
        
        # 等待密码修改和token黑名单生效
        await asyncio.sleep(1)
        
        # 使用旧token访问
        response = await self.client.get(reverse('custom_auth:users-me'))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'detail' in response.data
        assert 'Token is blacklisted' in str(response.data['detail'])

class UserModelTests(TestCase):
    """用户模型测试"""

    def setUp(self):
        self.user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "phone": "13800138000",
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_create_user(self):
        """测试创建普通用户"""
        self.assertEqual(self.user.username, self.user_data["username"])
        self.assertEqual(self.user.email, self.user_data["email"])
        self.assertEqual(self.user.phone, self.user_data["phone"])
        self.assertTrue(self.user.check_password(self.user_data["password"]))
        self.assertEqual(self.user.user_type, "user")
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)

    def test_create_superuser(self):
        """测试创建超级用户"""
        admin = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="admin123", phone="13900139000"
        )
        self.assertEqual(admin.user_type, "admin")
        self.assertTrue(admin.is_active)
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)


class AuthAPITests(BaseTestCase):
    """认证API测试"""

    async def asyncSetUp(self):
        await super().asyncSetUp()
        self.register_url = reverse("custom_auth:register")
        self.login_url = reverse("custom_auth:token_obtain")
        self.user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "password2": "testpass123",
            "phone": "13800138000",
        }

    @pytest.mark.django_db
    @pytest.mark.asyncio
    async def test_user_registration(self):
        """测试用户注册"""
        response = await self.client.post(self.register_url, self.user_data)
        assert response.status_code == status.HTTP_201_CREATED
        assert await User.objects.filter(username=self.user_data["username"]).aexists()

    @pytest.mark.django_db
    @pytest.mark.asyncio
    async def test_user_registration_with_invalid_data(self):
        """测试无效数据注册"""
        # 测试密码不匹配
        invalid_data = self.user_data.copy()
        invalid_data["password2"] = "wrongpass"
        response = await self.client.post(self.register_url, invalid_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # 测试重复用户名
        await User.objects.acreate_user(
            username=self.user_data["username"], email="other@example.com", password="pass123", phone="13700137000"
        )
        response = await self.client.post(self.register_url, self.user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    @pytest.mark.asyncio
    async def test_user_login(self):
        """测试用户登录"""
        # 创建用户
        await User.objects.acreate_user(
            username=self.user_data["username"],
            email=self.user_data["email"],
            password=self.user_data["password"],
            phone=self.user_data["phone"],
        )

        # 测试登录
        login_data = {"username": self.user_data["username"], "password": self.user_data["password"]}
        response = await self.client.post(self.login_url, login_data)
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    @pytest.mark.django_db
    @pytest.mark.asyncio
    async def test_user_login_with_invalid_credentials(self):
        """测试无效凭据登录"""
        login_data = {"username": "nonexistent", "password": "wrongpass"}
        response = await self.client.post(self.login_url, login_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TokenTests(BaseTestCase):
    """Token相关测试"""

    async def asyncSetUp(self):
        await super().asyncSetUp()
        self.user = await User.objects.acreate_user(
            username="testuser", email="test@example.com", password="testpass123", phone="13800138000"
        )
        self.login_url = reverse("custom_auth:token_obtain")
        self.refresh_url = reverse("custom_auth:token_refresh")
        self.logout_url = reverse("custom_auth:logout")

    @pytest.mark.django_db
    @pytest.mark.asyncio
    async def test_token_refresh(self):
        """测试刷新token"""
        # 先登录获取token
        response = await self.client.post(self.login_url, {"username": "testuser", "password": "testpass123"})
        refresh_token = response.data["refresh"]

        # 测试刷新token
        response = await self.client.post(self.refresh_url, {"refresh": refresh_token})
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

    @pytest.mark.django_db
    @pytest.mark.asyncio
    async def test_token_refresh_with_invalid_token(self):
        """测试使用无效token刷新"""
        response = await self.client.post(self.refresh_url, {"refresh": "invalid_token"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    @pytest.mark.asyncio
    async def test_user_logout(self):
        """测试用户登出"""
        # 先登录
        response = await self.client.post(self.login_url, {"username": "testuser", "password": "testpass123"})
        token = response.data["access"]

        # 测试登出
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = await self.client.post(self.logout_url)
        assert response.status_code == status.HTTP_200_OK 