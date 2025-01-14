import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
import time

from .utils import BaseAPITestCase

User = get_user_model()

class TestUserLogin(BaseAPITestCase):
    """用户登录测试"""

    def setUp(self):
        """测试初始化"""
        super().setUp()
        self.test_user = self.user  # 使用BaseAPITestCase中创建的用户
        self.test_password = 'testpass123'  # 使用BaseAPITestCase中的默认密码

    def test_login_success(self):
        """测试使用正确的用户名和密码登录"""
        url = reverse('custom_auth:token_obtain')
        data = {
            'username': self.test_user.username,
            'password': self.test_password
        }
        response = self.client.post(url, data)
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

    def test_login_wrong_password(self):
        """测试使用错误密码登录"""
        url = reverse('custom_auth:token_obtain')
        data = {
            'username': self.test_user.username,
            'password': 'wrongpass'
        }
        response = self.client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'message' in response.data
        assert response.data['message'] == '登录失败'
        assert 'errors' in response.data

    def test_login_nonexistent_user(self):
        """测试使用不存在的用户名登录"""
        url = reverse('custom_auth:token_obtain')
        data = {
            'username': 'nonexistentuser',
            'password': self.test_password
        }
        response = self.client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'message' in response.data
        assert response.data['message'] == '登录失败'
        assert 'errors' in response.data

    def test_login_banned_user(self):
        """测试被禁用的用户登录"""
        # 禁用测试用户
        self.test_user.is_active = False
        self.test_user.save()

        url = reverse('custom_auth:token_obtain')
        data = {
            'username': self.test_user.username,
            'password': self.test_password
        }
        response = self.client.post(url, data)
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
        # 设置认证头
        self.authenticate()

    def test_valid_token_access(self):
        """测试使用有效token访问"""
        response = self.client.get(reverse('custom_auth:users-me'))
        assert response.status_code == status.HTTP_200_OK
        assert 'message' in response.data
        assert response.data['message'] == '获取成功'
        assert 'data' in response.data
        assert 'user' in response.data['data']

    def test_expired_token_access(self):
        """测试使用过期token访问"""
        # 使用一个无效的token
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNTE2MjM5MDIyLCJpYXQiOjE1MTYyMzkwMjIsImp0aSI6ImY3YzJkYzFkYjg4YzQ3OWFiZWY5M2RmODUyMGU3OTI4IiwidXNlcl9pZCI6MX0.invalid_signature')
        response = self.client.get(reverse('custom_auth:users-me'))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_invalid_token_access(self):
        """测试使用无效token访问"""
        # 使用格式错误的token
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid.token.format')
        response = self.client.get(reverse('custom_auth:users-me'))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_blacklisted_token_access(self):
        """测试使用已注销token访问"""
        # 先获取一个有效的响应，确保token有效
        response = self.client.get(reverse('custom_auth:users-me'))
        assert response.status_code == status.HTTP_200_OK

        # 注销当前token
        url = reverse('custom_auth:logout')
        data = {
            'refresh_token': self.refresh_token
        }
        logout_response = self.client.post(url, data)
        assert logout_response.status_code == status.HTTP_200_OK
        
        # 等待token黑名单生效
        time.sleep(1)
        
        # 使用已注销的token访问
        response = self.client.get(reverse('custom_auth:users-me'))
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

    def test_valid_registration(self):
        """测试使用有效信息注册新用户"""
        url = reverse('custom_auth:register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'NewPass@123',
            'password2': 'NewPass@123',
            'phone': '13800138000'
        }
        response = self.client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert 'message' in response.data
        assert response.data['message'] == '注册成功'
        assert 'data' in response.data
        assert 'user' in response.data['data']
        assert 'token' in response.data['data']
        assert 'access' in response.data['data']['token']
        assert 'refresh' in response.data['data']['token']

    def test_duplicate_username_registration(self):
        """测试使用已存在的用户名注册"""
        url = reverse('custom_auth:register')
        data = {
            'username': self.test_user.username,
            'email': 'another@example.com',
            'password': 'NewPass@123',
            'password2': 'NewPass@123',
            'phone': '13800138000'
        }
        response = self.client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'message' in response.data
        assert response.data['message'] == '注册失败'
        assert 'errors' in response.data

    def test_invalid_email_registration(self):
        """测试使用无效的邮箱格式注册"""
        url = reverse('custom_auth:register')
        data = {
            'username': 'newuser',
            'email': 'invalid-email',
            'password': 'NewPass@123',
            'password2': 'NewPass@123',
            'phone': '13800138000'
        }
        response = self.client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'message' in response.data
        assert response.data['message'] == '注册失败'
        assert 'errors' in response.data

    def test_weak_password_registration(self):
        """测试使用不符合要求的密码注册"""
        url = reverse('custom_auth:register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': '123',
            'password2': '123',
            'phone': '13800138000'
        }
        response = self.client.post(url, data)
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
        self.authenticate()

    def test_change_password(self):
        """测试修改密码"""
        data = {
            'old_password': self.test_password,
            'new_password1': 'NewPass@123',  # 使用符合要求的强密码
            'new_password2': 'NewPass@123'
        }
        response = self.client.post(reverse('custom_auth:users-change-password'), data)
        assert response.status_code == status.HTTP_200_OK
        assert 'message' in response.data
        assert response.data['message'] == '密码修改成功'

    def test_change_password_wrong_old_password(self):
        """测试使用错误的旧密码修改密码"""
        data = {
            'old_password': 'wrongpassword',
            'new_password1': 'NewPass@123',
            'new_password2': 'NewPass@123'
        }
        response = self.client.post(reverse('custom_auth:users-change-password'), data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'message' in response.data
        assert response.data['message'] == '密码修改失败'

    def test_change_password_mismatch(self):
        """测试新密码不匹配的情况"""
        data = {
            'old_password': self.test_password,
            'new_password1': 'NewPass@123',
            'new_password2': 'DifferentPass@123'
        }
        response = self.client.post(reverse('custom_auth:users-change-password'), data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'message' in response.data
        assert response.data['message'] == '密码修改失败'

    def test_change_password_weak_password(self):
        """测试使用弱密码修改密码"""
        data = {
            'old_password': self.test_password,
            'new_password1': '123',
            'new_password2': '123'
        }
        response = self.client.post(reverse('custom_auth:users-change-password'), data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'message' in response.data
        assert response.data['message'] == '密码修改失败'

    def test_change_password_unauthorized(self):
        """测试未认证用户修改密码"""
        # 清除认证头
        self.client.credentials()
        
        data = {
            'old_password': self.test_password,
            'new_password1': 'NewPass@123',
            'new_password2': 'NewPass@123'
        }
        response = self.client.post(reverse('custom_auth:users-change-password'), data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

class TestConcurrentAuth(BaseAPITestCase):
    """并发认证测试"""

    def setUp(self):
        """测试初始化"""
        super().setUp()
        self.test_user = self.user
        self.test_password = 'testpass123'
        self.login_url = reverse('custom_auth:token_obtain')

    def test_concurrent_login_attempts(self):
        """测试并发登录尝试"""
        # 使用错误密码尝试登录5次
        for _ in range(5):
            response = self.client.post(self.login_url, {
                'username': self.test_user.username,
                'password': 'wrong_password'
            })
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data['message'], '登录失败')
            self.assertIn('non_field_errors', response.data['errors'])

        # 第6次尝试登录，即使使用正确密码也应该被锁定
        response = self.client.post(self.login_url, {
            'username': self.test_user.username,
            'password': self.test_password
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], '登录失败')
        self.assertIn('non_field_errors', response.data['errors'])

    def test_concurrent_password_changes(self):
        """测试并发修改密码"""
        # 创建两个客户端模拟并发
        client1 = APIClient()
        client2 = APIClient()
        
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
        response1 = client1.post(reverse('custom_auth:users-change-password'), data1)
        assert response1.status_code == status.HTTP_200_OK
        
        # 等待密码修改和token黑名单生效
        time.sleep(1)
        
        # 客户端2使用旧密码尝试修改密码
        data2 = {
            'old_password': self.test_password,
            'new_password1': 'AnotherPass@123',
            'new_password2': 'AnotherPass@123'
        }
        response2 = client2.post(reverse('custom_auth:users-change-password'), data2)
        assert response2.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'detail' in response2.data
        assert 'Token is blacklisted' in str(response2.data['detail'])

    def test_token_reuse_after_password_change(self):
        """测试修改密码后旧token是否失效"""
        # 设置认证头
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_token["access"]}')
        
        # 先获取一个有效的响应，确保token有效
        response = self.client.get(reverse('custom_auth:users-me'))
        assert response.status_code == status.HTTP_200_OK
        
        # 修改密码
        change_data = {
            'old_password': self.test_password,
            'new_password1': 'NewPass@123',
            'new_password2': 'NewPass@123'
        }
        response = self.client.post(reverse('custom_auth:users-change-password'), change_data)
        assert response.status_code == status.HTTP_200_OK
        
        # 等待密码修改和token黑名单生效
        time.sleep(1)
        
        # 使用旧token访问
        response = self.client.get(reverse('custom_auth:users-me'))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'detail' in response.data
        assert 'Token is blacklisted' in str(response.data['detail']) 