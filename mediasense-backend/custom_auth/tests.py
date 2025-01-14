from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User


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


class AuthAPITests(APITestCase):
    """认证API测试"""

    def setUp(self):
        self.register_url = reverse("custom_auth:register")
        self.login_url = reverse("custom_auth:token_obtain")
        self.user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "password2": "testpass123",
            "phone": "13800138000",
        }

    def test_user_registration(self):
        """测试用户注册"""
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username=self.user_data["username"]).exists())

    def test_user_registration_with_invalid_data(self):
        """测试无效数据注册"""
        # 测试密码不匹配
        invalid_data = self.user_data.copy()
        invalid_data["password2"] = "wrongpass"
        response = self.client.post(self.register_url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # 测试重复用户名
        User.objects.create_user(
            username=self.user_data["username"], email="other@example.com", password="pass123", phone="13700137000"
        )
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_login(self):
        """测试用户登录"""
        # 创建用户
        user = User.objects.create_user(
            username=self.user_data["username"],
            email=self.user_data["email"],
            password=self.user_data["password"],
            phone=self.user_data["phone"],
        )

        # 测试登录
        login_data = {"username": self.user_data["username"], "password": self.user_data["password"]}
        response = self.client.post(self.login_url, login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_user_login_with_invalid_credentials(self):
        """测试无效凭据登录"""
        login_data = {"username": "nonexistent", "password": "wrongpass"}
        response = self.client.post(self.login_url, login_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TokenTests(APITestCase):
    """Token相关测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123", phone="13800138000"
        )
        self.login_url = reverse("custom_auth:token_obtain")
        self.refresh_url = reverse("custom_auth:token_refresh")
        self.logout_url = reverse("custom_auth:logout")

    def test_token_refresh(self):
        """测试刷新token"""
        # 先登录获取token
        response = self.client.post(self.login_url, {"username": "testuser", "password": "testpass123"})
        refresh_token = response.data["refresh"]

        # 测试刷新token
        response = self.client.post(self.refresh_url, {"refresh": refresh_token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_token_refresh_with_invalid_token(self):
        """测试使用无效token刷新"""
        response = self.client.post(self.refresh_url, {"refresh": "invalid_token"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_logout(self):
        """测试用户登出"""
        # 先登录
        response = self.client.post(self.login_url, {"username": "testuser", "password": "testpass123"})
        token = response.data["access"]

        # 测试登出
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
