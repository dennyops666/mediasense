from django.test import TestCase, Client
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

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
        self.client = APIClient()
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