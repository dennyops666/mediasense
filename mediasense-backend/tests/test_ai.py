import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from ai_service.models import AnalysisResult
from news.models import News
from .factories import NewsFactory, UserFactory, AnalysisResultFactory
import json
from unittest.mock import patch

pytestmark = pytest.mark.django_db

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def authenticated_client(api_client):
    user = UserFactory(is_staff=True)
    api_client.force_authenticate(user=user)
    return api_client

class TestAITextAnalysis:
    """TC-AI-001: 文本分析服务测试"""

    @pytest.fixture
    def test_news(self):
        return NewsFactory(
            title="Test News for AI Analysis",
            content="This is a test content for AI analysis. The content is positive and informative."
        )

    def test_sentiment_analysis(self, authenticated_client, test_news):
        """测试情感分析处理"""
        url = reverse('ai-analyze-sentiment', kwargs={'pk': test_news.id})
        
        with patch('ai_service.services.openai.ChatCompletion.create') as mock_openai:
            # 模拟OpenAI API响应
            mock_openai.return_value = {
                'choices': [{
                    'message': {
                        'content': json.dumps({
                            'sentiment': 'positive',
                            'confidence': 0.85,
                            'explanation': 'The content shows a positive tone'
                        })
                    }
                }]
            }
            
            response = authenticated_client.post(url)
            
        assert response.status_code == status.HTTP_200_OK
        assert response.data['sentiment'] == 'positive'
        assert response.data['confidence'] > 0.8
        
        # 验证分析结果已保存
        analysis = AnalysisResult.objects.get(news_id=test_news.id)
        assert analysis.sentiment == 'positive'

    def test_keyword_extraction(self, authenticated_client, test_news):
        """测试关键词提取"""
        url = reverse('ai-extract-keywords', kwargs={'pk': test_news.id})
        
        with patch('ai_service.services.openai.ChatCompletion.create') as mock_openai:
            mock_openai.return_value = {
                'choices': [{
                    'message': {
                        'content': json.dumps({
                            'keywords': ['test', 'AI', 'analysis', 'content'],
                            'confidence': 0.9
                        })
                    }
                }]
            }
            
            response = authenticated_client.post(url)
            
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['keywords']) > 0
        assert 'AI' in response.data['keywords']
        
        # 验证关键词已保存
        analysis = AnalysisResult.objects.get(news_id=test_news.id)
        assert 'AI' in analysis.keywords

    def test_text_summary_generation(self, authenticated_client, test_news):
        """测试文本摘要生成"""
        url = reverse('ai-generate-summary', kwargs={'pk': test_news.id})
        
        with patch('ai_service.services.openai.ChatCompletion.create') as mock_openai:
            mock_openai.return_value = {
                'choices': [{
                    'message': {
                        'content': json.dumps({
                            'summary': 'A test content for AI analysis with positive tone.',
                            'confidence': 0.88
                        })
                    }
                }]
            }
            
            response = authenticated_client.post(url)
            
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['summary']) > 0
        
        # 验证摘要已保存
        analysis = AnalysisResult.objects.get(news_id=test_news.id)
        assert analysis.summary is not None

    def test_batch_analysis(self, authenticated_client):
        """测试批量分析任务"""
        # 创建多条新闻
        news_list = [NewsFactory() for _ in range(3)]
        url = reverse('ai-batch-analyze')
        
        with patch('ai_service.services.openai.ChatCompletion.create') as mock_openai:
            mock_openai.return_value = {
                'choices': [{
                    'message': {
                        'content': json.dumps({
                            'sentiment': 'neutral',
                            'keywords': ['test'],
                            'summary': 'Test summary',
                            'confidence': 0.85
                        })
                    }
                }]
            }
            
            response = authenticated_client.post(url, {
                'news_ids': [news.id for news in news_list]
            })
            
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert 'task_id' in response.data
        
        # 检查任务状态
        task_url = reverse('ai-task-status', kwargs={'task_id': response.data['task_id']})
        status_response = authenticated_client.get(task_url)
        assert status_response.status_code == status.HTTP_200_OK

    def test_analysis_result_storage(self, authenticated_client, test_news):
        """测试分析结果存储"""
        # 创建分析结果
        analysis = AnalysisResultFactory(
            news=test_news,
            sentiment='positive',
            keywords=['test', 'AI'],
            summary='Test summary',
            confidence=0.9
        )
        
        # 获取分析结果
        url = reverse('ai-analysis-result', kwargs={'pk': test_news.id})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['sentiment'] == 'positive'
        assert 'AI' in response.data['keywords']
        assert response.data['confidence'] == 0.9
        
        # 测试结果更新
        update_url = reverse('ai-update-analysis', kwargs={'pk': test_news.id})
        with patch('ai_service.services.openai.ChatCompletion.create') as mock_openai:
            mock_openai.return_value = {
                'choices': [{
                    'message': {
                        'content': json.dumps({
                            'sentiment': 'negative',
                            'confidence': 0.95
                        })
                    }
                }]
            }
            
            response = authenticated_client.put(update_url)
            
        assert response.status_code == status.HTTP_200_OK
        analysis.refresh_from_db()
        assert analysis.sentiment == 'negative'
        assert analysis.confidence == 0.95 