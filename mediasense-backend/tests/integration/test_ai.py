import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch, Mock, MagicMock, AsyncMock
from tests.factories import UserFactory, NewsArticleFactory, AnalysisRuleFactory
from news.models import NewsArticle
from ai_service.models import AnalysisRule, AnalysisResult
from django.utils import timezone
import json
from django.db import transaction
from django.test import TransactionTestCase
from asgiref.sync import sync_to_async
import logging

pytestmark = [
    pytest.mark.django_db(transaction=True),
    pytest.mark.asyncio
]

logger = logging.getLogger(__name__)

class TestAIServiceIntegration(TransactionTestCase):
    """TC-INT-AI-001: AI服务集成测试"""

    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        super().setUpClass()
        cls.mock_openai_patcher = patch('ai_service.services.AsyncOpenAI')
        cls.mock_openai = cls.mock_openai_patcher.start()
        cls.mock_client = MagicMock()
        cls.mock_client.chat.completions.create = AsyncMock(return_value=MagicMock(
            choices=[MagicMock(message=MagicMock(content=json.dumps({
                "sentiment": "positive",
                "confidence": 0.8,
                "explanation": "测试分析结果"
            })))]
        ))
        cls.mock_openai.return_value = cls.mock_client

    @classmethod
    def tearDownClass(cls):
        """清理测试类"""
        super().tearDownClass()
        cls.mock_openai_patcher.stop()

    def setUp(self):
        """设置测试环境"""
        super().setUp()
        self.user = UserFactory(is_staff=True, is_superuser=True)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    async def test_text_analysis(self):
        """测试文本分析功能"""
        try:
            # 创建测试文章
            article = await NewsArticleFactory.acreate(
                title="测试文章",
                content="这是一篇测试文章的内容，用于测试AI文本分析功能。",
                status=NewsArticle.Status.PUBLISHED,
                created_by=self.user
            )

            # 测试情感分析
            url = reverse('api:ai_service:ai-analyze-article', args=[article.id])
            response = await sync_to_async(self.client.post)(
                url, 
                data=json.dumps({
                    'analysis_types': ['sentiment']
                }),
                content_type='application/json'
            )
            
            print(f"\n测试情感分析响应: {response.status_code}")
            print(f"响应内容: {response.data}")
            
            assert response.status_code == status.HTTP_200_OK, f"请求失败，状态码: {response.status_code}"
            assert 'data' in response.data, "响应中缺少data字段"
            assert 'sentiment' in response.data['data'], "响应中缺少sentiment字段"
            assert response.data['message'] == '分析完成', "响应消息不正确"
            assert 'result_ids' in response.data, "响应中缺少result_ids字段"
            assert len(response.data['result_ids']) > 0, "没有生成分析结果ID"

            # 验证分析结果保存
            result = await sync_to_async(AnalysisResult.objects.get)(news=article)
            assert result is not None, "分析结果未保存到数据库"
            assert result.analysis_type == 'sentiment', "分析类型不正确"
            assert result.result is not None, "分析结果为空"
            assert isinstance(result.result, dict), "分析结果格式不正确"
            assert 'sentiment' in result.result, "分析结果中缺少sentiment字段"
            assert 'confidence' in result.result, "分析结果中缺少confidence字段"
            assert 'explanation' in result.result, "分析结果中缺少explanation字段"

        except Exception as e:
            logger.error(f"测试失败: {str(e)}")
            raise

    async def test_service_integration(self):
        """测试服务集成"""
        try:
            # 创建测试文章和分析规则
            article = await NewsArticleFactory.acreate(
                title="集成测试文章",
                content="这是一篇用于测试服务集成的文章。",
                status=NewsArticle.Status.PUBLISHED,
                created_by=self.user
            )
            
            rule = await AnalysisRuleFactory.acreate(
                name="测试规则",
                rule_type="sentiment",
                system_prompt="你是一个文本分析助手",
                user_prompt_template="分析以下文本的情感倾向：{content}",
                is_active=True,
                created_by=self.user
            )

            # 测试规则分析
            url = reverse('api:ai_service:ai-analyze-with-rules', args=[article.id])
            response = await sync_to_async(self.client.post)(
                url,
                data=json.dumps({'rule_id': rule.id}),
                content_type='application/json'
            )

            print(f"\n测试规则分析响应: {response.status_code}")
            print(f"响应内容: {response.data}")

            assert response.status_code == status.HTTP_200_OK, f"请求失败，状态码: {response.status_code}"
            assert 'data' in response.data, "响应中缺少data字段"
            assert str(rule.id) in response.data['data'], "响应中缺少规则分析结果"
            assert response.data['message'] == '规则分析完成', "响应消息不正确"
            assert 'result_id' in response.data, "响应中缺少result_id字段"

            # 验证分析结果保存
            result = await sync_to_async(AnalysisResult.objects.get)(
                news=article,
                analysis_type=f"rule_{rule.id}"
            )
            assert result is not None, "分析结果未保存到数据库"
            assert result.result is not None, "分析结果为空"
            assert isinstance(result.result, dict), "分析结果格式不正确"

        except Exception as e:
            logger.error(f"测试失败: {str(e)}")
            raise