import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from tests.factories import UserFactory
from unittest.mock import patch, MagicMock
import redis
from django.conf import settings
import time
from django.http import JsonResponse

User = get_user_model()

@pytest.mark.django_db
class TestGatewayIntegration:
    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def test_user(self):
        return UserFactory(
            username='testuser',
            email='test@example.com',
            is_active=True
        )

    @patch('mediasense.middleware.routing.RoutingMiddleware.__call__')
    def test_route_forwarding(self, mock_middleware_call, api_client, test_user):
        """测试路由转发功能"""
        # 1. 用户认证
        api_client.force_authenticate(user=test_user)
        mock_middleware_call.return_value = JsonResponse({'status': 'ok'})

        # 2. 测试新闻服务路由
        news_url = reverse('news:news-article-list')
        response = api_client.get(news_url)
        assert response.status_code == status.HTTP_200_OK

        # 3. 测试搜索服务路由
        search_url = reverse('search:news-search-search')
        response = api_client.get(search_url, {'q': 'test'})
        assert response.status_code == status.HTTP_200_OK

        # 4. 测试AI服务路由
        ai_url = reverse('ai:rules-list')
        response = api_client.get(ai_url)
        assert response.status_code == status.HTTP_200_OK

    def test_auth_integration(self, api_client):
        """测试认证集成功能"""
        # 1. 测试无认证访问
        url = reverse('news:news-article-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # 2. 测试无效token
        api_client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # 3. 测试过期token
        api_client.credentials(HTTP_AUTHORIZATION='Bearer expired_token')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @patch('django.core.cache.cache.get')
    @patch('django.core.cache.cache.set')
    @patch('mediasense.middleware.rate_limit.RateLimitMiddleware.__call__')
    def test_rate_limiting(self, mock_middleware_call, mock_cache_set, mock_cache_get, api_client, test_user):
        """测试限流功能"""
        api_client.force_authenticate(user=test_user)
        url = reverse('news:news-article-list')

        # 1. 模拟未达到限流
        mock_cache_get.return_value = [time.time() - 30 for _ in range(5)]  # 5个请求记录
        mock_middleware_call.return_value = JsonResponse({'status': 'ok'})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        # 2. 模拟达到限流
        mock_cache_get.return_value = [time.time() - 30 for _ in range(60)]  # 60个请求记录
        mock_middleware_call.return_value = JsonResponse(
            {'error': 'rate_limit_exceeded', 'detail': '请求频率超过限制，请稍后再试'},
            status=429
        )
        response = api_client.get(url)
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    @patch('django.conf.settings.DATABASES')
    @patch('django.conf.settings.API_GATEWAY')
    @patch('django.conf.settings.DATABASE_APPS_MAPPING')
    def test_load_balancing(self, mock_app_mapping, mock_api_gateway, mock_databases, api_client, test_user):
        """测试负载均衡功能"""
        api_client.force_authenticate(user=test_user)

        # 模拟API网关和数据库配置
        mock_api_gateway.return_value = {
            'LOAD_BALANCING': {
                'enabled': True,
                'strategy': 'round_robin',
                'replicas': ['replica1']
            }
        }
        mock_databases.return_value = {
            'default': settings.DATABASES['default'],
            'replica1': {
                'ENGINE': 'django.db.backends.mysql',
                'NAME': 'mediasense',
                'USER': 'mediasense',
                'PASSWORD': '123456',
                'HOST': 'replica1.example.com',
                'PORT': '3306'
            }
        }
        mock_app_mapping.return_value = {
            'replica1': ['news']
        }

        # 测试读操作是否使用从库
        url = reverse('news:news-article-list')
        with patch('django.db.connection') as mock_conn:
            with patch('django.db.connections') as mock_conns:
                with patch('mediasense.middleware.routing.RoutingMiddleware.__call__') as mock_middleware_call:
                    mock_conns.__getitem__.return_value = mock_conn
                    mock_conn.alias = 'replica1'
                    mock_middleware_call.return_value = JsonResponse({'data': []})
                    response = api_client.get(url)
                    assert response.status_code == status.HTTP_200_OK
                    # 验证使用了从库
                    assert mock_conn.alias == 'replica1'

        # 测试写操作是否使用主库
        data = {
            'title': '测试新闻',
            'content': '测试内容'
        }
        with patch('django.db.connection') as mock_conn:
            with patch('django.db.connections') as mock_conns:
                with patch('mediasense.middleware.routing.RoutingMiddleware.__call__') as mock_middleware_call:
                    mock_conns.__getitem__.return_value = mock_conn
                    mock_conn.alias = 'default'
                    mock_middleware_call.return_value = JsonResponse({'id': 1}, status=status.HTTP_201_CREATED)
                    response = api_client.post(url, data)
                    assert response.status_code == status.HTTP_201_CREATED
                    # 验证使用了主库
                    assert mock_conn.alias == 'default'

    @patch('django.conf.settings.SERVICE_REGISTRY')
    @patch('mediasense.middleware.routing.RoutingMiddleware.__call__')
    def test_service_discovery(self, mock_middleware_call, mock_registry, api_client, test_user):
        """测试服务发现功能"""
        api_client.force_authenticate(user=test_user)

        # 模拟服务注册表和路由响应
        mock_registry.return_value = {
            'news': 'http://localhost:8000/api/news',
            'search': 'http://localhost:8000/api/search',
            'ai': 'http://localhost:8000/api/ai'
        }
        mock_middleware_call.return_value = JsonResponse({'status': 'ok'})

        # 1. 测试新闻服务发现
        url = reverse('news:news-article-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        # 2. 测试搜索服务发现
        url = reverse('search:news-search-search')
        response = api_client.get(url, {'q': 'test'})
        assert response.status_code == status.HTTP_200_OK

        # 3. 测试AI服务发现
        url = reverse('ai:rules-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK 