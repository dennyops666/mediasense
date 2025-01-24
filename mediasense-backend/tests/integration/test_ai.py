import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch, Mock, MagicMock
from tests.factories import UserFactory, NewsArticleFactory, AnalysisRuleFactory
from news.models import NewsArticle
from ai_service.models import AnalysisRule, AnalysisResult
from django.utils import timezone
import json

pytestmark = pytest.mark.django_db

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def admin_user():
    return UserFactory(is_staff=True, is_superuser=True)

@pytest.fixture
def authenticated_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client

@pytest.fixture
def mock_openai():
    with patch('ai_service.services.openai') as mock:
        mock.ChatCompletion.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="测试分析结果"))]
        )
        yield mock

class TestAIServiceIntegration:
    """TC-INT-AI-001: AI服务集成测试"""

    def test_text_analysis(self, authenticated_client, mock_openai):
        """测试文本分析功能"""
        # 创建测试文章
        article = NewsArticleFactory(
            title="测试文章",
            content="这是一篇测试文章的内容，用于测试AI文本分析功能。",
            status=NewsArticle.Status.PUBLISHED,
            created_by=authenticated_client.handler._force_user
        )

        # 测试情感分析
        url = reverse('api:ai:analyze-article')
        response = authenticated_client.post(url, {
            'article_id': article.id,
            'analysis_types': ['sentiment']
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert 'sentiment' in response.data['data']
        assert response.data['message'] == '分析完成'

        # 验证分析结果保存
        result = AnalysisResult.objects.get(news=article)
        assert result.analysis_type == 'sentiment'
        assert result.result is not None

    def test_service_integration(self, authenticated_client, mock_openai):
        """测试服务集成"""
        # 创建测试文章和分析规则
        article = NewsArticleFactory(
            title="集成测试文章",
            content="这是一篇用于测试服务集成的文章。",
            status=NewsArticle.Status.PUBLISHED,
            created_by=authenticated_client.handler._force_user
        )
        
        rule = AnalysisRuleFactory(
            name="测试规则",
            rule_type="sentiment",
            system_prompt="你是一个文本分析助手",
            user_prompt_template="分析以下文本的情感倾向：{content}",
            is_active=True
        )

        # 测试规则分析
        url = reverse('api:ai:analyze-with-rules', args=[article.id])
        response = authenticated_client.post(url, {
            'rule_id': rule.id
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == '规则分析完成'
        assert str(rule.id) in response.data['data']

        # 验证与监控服务的集成
        result = AnalysisResult.objects.get(news=article)
        assert result.created_at is not None
        assert result.execution_time is not None

    def test_error_handling(self, authenticated_client, mock_openai):
        """测试错误处理机制"""
        # 创建测试文章
        article = NewsArticleFactory(
            title="错误处理测试",
            content="这是一篇用于测试错误处理的文章。",
            status=NewsArticle.Status.PUBLISHED,
            created_by=authenticated_client.handler._force_user
        )

        # 测试超时处理
        mock_openai.ChatCompletion.create.side_effect = TimeoutError("请求超时")
        
        url = reverse('api:ai:analyze-article')
        response = authenticated_client.post(url, {
            'article_id': article.id,
            'analysis_types': ['sentiment']
        })
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'error' in response.data

        # 测试重试机制
        rule = AnalysisRuleFactory(
            name="重试测试规则",
            rule_type="sentiment",
            is_active=True
        )

        mock_openai.ChatCompletion.create.side_effect = [
            TimeoutError("第一次超时"),
            MagicMock(choices=[MagicMock(message=MagicMock(content="重试成功"))])
        ]

        url = reverse('api:ai:analyze-with-rules', args=[article.id])
        response = authenticated_client.post(url, {
            'rule_id': rule.id
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == '规则分析完成'

        # 测试降级策略
        mock_openai.ChatCompletion.create.side_effect = Exception("服务不可用")
        
        response = authenticated_client.post(url, {
            'rule_id': rule.id
        })
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'error' in response.data 