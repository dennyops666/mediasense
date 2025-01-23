import json
from unittest.mock import AsyncMock, patch, MagicMock
from django.test import TransactionTestCase
from django.core.cache import cache
from rest_framework.test import APIRequestFactory
from asgiref.sync import sync_to_async
from news.models import NewsArticle
from ai_service.views import AIServiceViewSet
from ai_service.services import AIService, RateLimitExceeded
from ai_service.models import AnalysisRule, AnalysisResult
from openai import OpenAI, AsyncOpenAI, APIStatusError
import asyncio
import openai
import uuid
import pytest
from django.conf import settings
from django.utils import timezone

class TestAITextAnalysis(TransactionTestCase):
    """AI文本分析服务测试"""

    async def asyncSetUp(self):
        """测试初始化"""
        # 清理缓存
        await sync_to_async(cache.clear)()
        
        # 创建测试新闻
        self.news = await sync_to_async(NewsArticle.objects.create)(
            title="Test News",
            content="This is a test news article with positive sentiment.",
            url=f"http://example.com/test-news-{uuid.uuid4()}"
        )
        
        # 创建空内容的新闻
        self.empty_news = await sync_to_async(NewsArticle.objects.create)(
            title="Empty News",
            content="",
            url=f"http://example.com/empty-news-{uuid.uuid4()}"
        )

        # 创建超长文本的新闻
        long_content = "Long test content. " * 1000
        self.long_news = await sync_to_async(NewsArticle.objects.create)(
            title="Long News",
            content=long_content,
            url=f"http://example.com/long-news-{uuid.uuid4()}"
        )

        # 设置mock响应
        self.mock_response = AsyncMock()
        self.mock_response.choices = [AsyncMock()]
        self.mock_response.choices[0].message = AsyncMock()
        self.mock_response.choices[0].message.content = json.dumps({
            "sentiment": "positive",
            "confidence": 0.85,
            "explanation": "The text contains positive language."
        })
        
        # 创建mock客户端
        self.mock_client = AsyncMock()
        self.mock_client.chat.completions.create = AsyncMock(return_value=self.mock_response)
        
        # 存储所有创建的mock对象以便清理
        self._mock_objects = []
        self._mock_objects.extend([
            self.mock_response,
            self.mock_response.choices[0],
            self.mock_response.choices[0].message,
            self.mock_client,
            self.mock_client.chat.completions.create
        ])

        # 创建AI服务实例
        self.ai_service = AIService()
        self.ai_service.openai_client = self.mock_client
        
        # 创建测试规则
        self.rule = await sync_to_async(AnalysisRule.objects.create)(
            name="Test Rule",
            description="Test rule for sentiment analysis",
            rule_type="sentiment",
            system_prompt="You are a sentiment analysis expert.",
            user_prompt_template="Analyze the sentiment of: {content}",
            parameters={"temperature": 0.5, "max_tokens": 100},
            is_active=True
        )

    def setUp(self):
        """同步初始化"""
        asyncio.run(self.asyncSetUp())

    async def asyncTearDown(self):
        """测试清理"""
        # 清理测试数据
        await sync_to_async(cache.clear)()
        if hasattr(self, 'news'):
            await sync_to_async(self.news.delete)()
        if hasattr(self, 'empty_news'):
            await sync_to_async(self.empty_news.delete)()
        if hasattr(self, 'long_news'):
            await sync_to_async(self.long_news.delete)()
        if hasattr(self, 'rule'):
            await sync_to_async(self.rule.delete)()
        
        # 清理分析结果
        await sync_to_async(AnalysisResult.objects.all().delete)()
        
        # 清理所有mock对象
        if hasattr(self, '_mock_objects'):
            for mock_obj in self._mock_objects:
                # 检查是否有未完成的调用
                if hasattr(mock_obj, '_mock_wraps') and mock_obj._mock_wraps is not None:
                    try:
                        await mock_obj._mock_wraps
                    except Exception:
                        pass
                # 检查是否有异步上下文管理器方法
                if hasattr(mock_obj, '__aexit__'):
                    try:
                        await mock_obj.__aexit__(None, None, None)
                    except Exception:
                        pass
                # 检查是否有异步关闭方法
                if hasattr(mock_obj, 'aclose'):
                    try:
                        await mock_obj.aclose()
                    except Exception:
                        pass
            self._mock_objects.clear()

    def tearDown(self):
        """同步清理"""
        asyncio.run(self.asyncTearDown())

    def _create_mock_response(self, content):
        """创建标准的mock响应对象"""
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock()]
        mock_response.choices[0].message = AsyncMock()
        mock_response.choices[0].message.content = json.dumps(content)
        
        # 添加异步上下文管理器方法
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        # 添加到待清理列表
        self._mock_objects.extend([
            mock_response,
            mock_response.choices[0],
            mock_response.choices[0].message
        ])
        
        return mock_response

    @pytest.mark.asyncio
    async def test_sentiment_analysis_normal(self):
        """测试正常文本的情感分析"""
        # 重置速率限制
        self.ai_service.reset_rate_limit()
        
        # 设置mock响应
        mock_response = self._create_mock_response({
            "sentiment": "positive",
            "confidence": 0.8,
            "explanation": "Test response"
        })
        
        self.mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        self._mock_objects.append(self.mock_client.chat.completions.create)
        
        # 执行分析
        result = await self.ai_service.analyze_sentiment(self.news.content)
        
        assert result["sentiment"] == "positive"
        assert result["confidence"] == 0.8
        assert "explanation" in result

    @pytest.mark.asyncio
    async def test_sentiment_analysis_empty_content(self):
        """测试空内容的情感分析"""
        with pytest.raises(ValueError, match="新闻内容为空"):
            await self.ai_service.analyze_sentiment("")

    @pytest.mark.asyncio
    async def test_sentiment_analysis_long_content(self):
        """测试超长文本的情感分析"""
        response = await self.ai_service.analyze_sentiment(self.long_news.content)
        assert response["sentiment"] in ["positive", "negative", "neutral"]
        assert 0 <= response["confidence"] <= 1

    @pytest.mark.asyncio
    async def test_sentiment_analysis_api_error(self):
        """测试API调用失败的情况"""
        # 重置速率限制
        self.ai_service.reset_rate_limit()
        
        # 设置mock抛出异常
        mock_response = AsyncMock()
        mock_response.status = 429
        mock_response.text = "Rate limit exceeded"
        mock_response.json.return_value = {"error": "rate_limit_exceeded"}
        
        self.mock_client.chat.completions.create.side_effect = openai.RateLimitError(
            message="Rate limit exceeded",
            response=mock_response,
            body={"error": "rate_limit_exceeded"}
        )
        
        with pytest.raises(RateLimitExceeded):
            await self.ai_service.analyze_sentiment(self.news.content)

    @pytest.mark.asyncio
    async def test_sentiment_analysis_cache(self):
        """测试情感分析缓存机制"""
        # 清除缓存
        await sync_to_async(cache.clear)()
        
        # 重置速率限制
        self.ai_service.reset_rate_limit()
        
        # 设置mock响应
        self.mock_response.choices[0].message.content = json.dumps({
            "sentiment": "positive",
            "confidence": 0.8,
            "explanation": "Test response"
        })
        self.mock_client.chat.completions.create.return_value = self.mock_response
        
        # 第一次请求
        result = await self.ai_service.analyze_sentiment(self.news.content)
        assert result["sentiment"] == "positive"
        assert result["confidence"] == 0.8
        
        # 修改mock响应
        self.mock_response.choices[0].message.content = json.dumps({
            "sentiment": "negative",
            "confidence": 0.75,
            "explanation": "Different response"
        })
        
        # 第二次请求应该返回缓存的结果
        cached_result = await self.ai_service.analyze_sentiment(self.news.content)
        assert cached_result["sentiment"] == result["sentiment"]
        assert cached_result["confidence"] == result["confidence"]
        
        # 验证API只被调用一次
        assert self.mock_client.chat.completions.create.call_count == 1

    @pytest.mark.asyncio
    async def test_keyword_extraction_normal(self):
        """测试正常文本的关键词提取"""
        self.mock_response.choices[0].message.content = json.dumps({
            "keywords": [
                {"word": "test", "score": 0.8},
                {"word": "news", "score": 0.6}
            ]
        })
        response = await self.ai_service.extract_keywords(self.news.content)
        assert "keywords" in response
        assert len(response["keywords"]) > 0
        assert all("word" in kw and "score" in kw for kw in response["keywords"])

    @pytest.mark.asyncio
    async def test_keyword_extraction_empty_content(self):
        """测试空内容的关键词提取"""
        with pytest.raises(ValueError, match="新闻内容不能为空"):
            await self.ai_service.extract_keywords("")

    @pytest.mark.asyncio
    async def test_summary_generation_normal(self):
        """测试正常文本的摘要生成"""
        self.mock_response.choices[0].message.content = json.dumps({
            "summary": "This is a test summary.",
            "confidence": 0.9
        })
        response = await self.ai_service.generate_summary(self.news.content)
        assert "summary" in response
        assert "confidence" in response
        assert 0 <= response["confidence"] <= 1

    @pytest.mark.asyncio
    async def test_summary_generation_empty_content(self):
        """测试空内容的摘要生成"""
        with pytest.raises(ValueError, match="新闻内容不能为空"):
            await self.ai_service.generate_summary("")

    @pytest.mark.asyncio
    async def test_batch_analysis(self):
        """测试批量分析功能"""
        news_articles = [self.news, self.long_news]
        results = await self.ai_service.batch_analyze(news_articles)
        
        assert len(results) == len(news_articles)
        for article_id, result in results.items():
            assert isinstance(result, dict)
            assert any(key in result for key in ["sentiment", "keywords", "summary"])

    @pytest.mark.asyncio
    async def test_rate_limit(self):
        """测试速率限制"""
        # 设置较低的速率限制
        self.ai_service.rate_limit_max_requests = 2
        
        # 连续发送请求直到触发限制
        with pytest.raises(RateLimitExceeded):
            for _ in range(3):
                await self.ai_service.analyze_sentiment(self.news.content)

    @pytest.mark.asyncio
    async def test_result_storage(self):
        """测试分析结果存储"""
        # 重置速率限制
        self.ai_service.reset_rate_limit()
        
        # 设置mock响应
        self.mock_response.choices[0].message.content = json.dumps({
            "sentiment": "positive",
            "confidence": 0.8,
            "explanation": "Test response"
        })
        
        # 执行分析
        result = await self.ai_service.analyze_sentiment(self.news.content)
        
        # 创建分析结果
        await sync_to_async(AnalysisResult.objects.create)(
            news=self.news,
            analysis_type="sentiment",
            result=json.dumps(result),
            is_valid=True
        )
        
        # 验证结果是否正确存储
        stored_result = await sync_to_async(AnalysisResult.objects.get)(
            news=self.news,
            analysis_type="sentiment"
        )
        assert stored_result is not None
        assert json.loads(stored_result.result)["sentiment"] == result["sentiment"]

    @pytest.mark.asyncio
    async def test_concurrent_analysis(self):
        """测试并发分析"""
        # 重置速率限制
        self.ai_service.reset_rate_limit()
        
        # 设置不同的mock响应
        sentiment_response = self._create_mock_response({
            "sentiment": "positive",
            "confidence": 0.85,
            "explanation": "Sentiment analysis"
        })
        
        keywords_response = self._create_mock_response({
            "keywords": [
                {"word": "test", "score": 0.8},
                {"word": "news", "score": 0.6}
            ]
        })
        
        summary_response = self._create_mock_response({
            "summary": "Test summary",
            "confidence": 0.9
        })
        
        # 创建响应序列
        self.mock_client.chat.completions.create.side_effect = [
            sentiment_response,
            keywords_response,
            summary_response
        ]
        
        # 创建多个分析任务
        tasks = [
            self.ai_service.analyze_sentiment(self.news.content),
            self.ai_service.extract_keywords(self.news.content),
            self.ai_service.generate_summary(self.news.content)
        ]
        
        # 并发执行任务
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 验证所有任务都成功完成
        assert len(results) == 3
        assert all(not isinstance(r, Exception) for r in results)
        
        # 验证结果类型
        assert "sentiment" in results[0]
        assert "keywords" in results[1]
        assert "summary" in results[2]

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """测试错误处理机制"""
        # 重置速率限制
        self.ai_service.reset_rate_limit()
        
        # 测试API错误
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text = "Internal Server Error"
        mock_response.json.return_value = {"error": "API Error"}
        
        self.mock_client.chat.completions.create.side_effect = openai.APIError(
            message="API Error",
            body={"error": "API Error"},
            request=AsyncMock()
        )
        with pytest.raises(ValueError, match="API错误"):
            await self.ai_service.analyze_sentiment(self.news.content)
        
        # 测试超时错误
        self.mock_client.chat.completions.create.side_effect = asyncio.TimeoutError()
        with pytest.raises(ValueError):
            await self.ai_service.analyze_sentiment(self.news.content)
        
        # 测试网络错误
        self.mock_client.chat.completions.create.side_effect = ConnectionError()
        with pytest.raises(ValueError):
            await self.ai_service.analyze_sentiment(self.news.content)

    @pytest.mark.asyncio
    async def test_cache_invalidation(self):
        """测试缓存失效机制"""
        # 重置速率限制
        self.ai_service.reset_rate_limit()
        
        # 设置mock响应
        self.mock_response.choices[0].message.content = json.dumps({
            "sentiment": "positive",
            "confidence": 0.8,
            "explanation": "Test response"
        })
        
        # 先执行分析并缓存结果
        result = await self.ai_service.analyze_sentiment(self.news.content)
        
        # 创建分析结果记录
        await sync_to_async(AnalysisResult.objects.create)(
            news=self.news,
            analysis_type="sentiment",
            result=json.dumps(result),
            is_valid=True
        )
        
        # 清除缓存
        await self.ai_service.invalidate_cache(self.news.id)
        
        # 验证分析结果已标记为无效
        invalid_result = await sync_to_async(AnalysisResult.objects.get)(
            news=self.news,
            analysis_type="sentiment"
        )
        assert not invalid_result.is_valid

    @pytest.mark.asyncio
    async def test_analysis_with_rules(self):
        """测试带规则的分析"""
        # 清理所有规则
        await sync_to_async(AnalysisRule.objects.all().delete)()
        
        # 创建测试新闻
        news = await sync_to_async(NewsArticle.objects.create)(
            title="Test News",
            content="This is a test news article with positive sentiment.",
            url=f"http://example.com/test-news-{uuid.uuid4()}"
        )

        # 创建分析规则
        rule = await sync_to_async(AnalysisRule.objects.create)(
            name="Test Rule",
            description="Test Description",
            rule_type="SENTIMENT",
            parameters={
                "keywords": ["positive", "negative"],
                "threshold": 0.5
            },
            system_prompt="You are a sentiment analysis expert.",
            user_prompt_template="Analyze the sentiment of: {content}",
            is_active=True
        )

        # 创建测试数据
        data = {
            "text": "This is a positive test message",
            "rule_id": rule.id
        }

        # 创建请求
        request = self._create_request(method='POST', data=data, path=f'/api/ai/{news.id}/analyze/')
        
        # 发送请求
        response = await self._get_response(request)
        
        # 验证响应
        self.assertEqual(response.status_code, 200)
        result = response.data
        print(f"\nResponse data: {result}")
        print(f"Rule ID: {rule.id}")
        self.assertEqual(result['message'], '规则分析完成')
        self.assertIn('data', result)
        
        # 验证规则分析结果
        rule_result = result['data'][rule.id]
        self.assertTrue(rule_result['success'])
        self.assertIn('data', rule_result)
        self.assertIn('content', rule_result['data'])
        self.assertIn('rule_id', rule_result['data'])
        self.assertEqual(rule_result['data']['rule_id'], rule.id)
        self.assertEqual(rule_result['data']['rule_name'], rule.name)
        
        # 验证分析结果是否被保存
        analysis_result = await sync_to_async(AnalysisResult.objects.filter(
            news=news,
            analysis_type=rule.rule_type
        ).first)()
        self.assertIsNotNone(analysis_result)
        
        # 验证分析结果的内容
        result_data = json.loads(analysis_result.result)
        self.assertEqual(result_data['rule_id'], rule.id)
        self.assertEqual(result_data['rule_name'], rule.name)

        # 清理测试数据
        await sync_to_async(news.delete)()
        await sync_to_async(rule.delete)()

    def _create_request(self, method='GET', data=None, path=None):
        """创建测试请求"""
        if data is None:
            data = {}
        if path is None:
            path = f'/api/ai/sentiment/{self.news.id}/'
            
        factory = APIRequestFactory()
        if method.upper() == 'GET':
            request = factory.get(path)
        elif method.upper() == 'POST':
            request = factory.post(path, data, format='json')
        else:
            request = factory.generic(method.upper(), path, data, format='json')
            
        request.data = data
        return request

    async def _get_response(self, request):
        """获取响应"""
        view = AIServiceViewSet()
        
        # 从路径中提取news_id
        news_id = None
        if 'batch' not in request.path:
            path_parts = request.path.strip('/').split('/')
            for i, part in enumerate(path_parts):
                if part in ['sentiment', 'keywords', 'summary', 'result', 'analyze']:
                    if i - 1 >= 0:  # 检查前一个部分是否是news_id
                        try:
                            news_id = int(path_parts[i-1])
                        except (ValueError, IndexError):
                            pass
                    break
        
        # 根据请求路径确定要调用的方法
        if 'sentiment' in request.path:
            response = await view.analyze_sentiment(request, pk=news_id)
        elif 'keywords' in request.path:
            response = await view.extract_keywords(request, pk=news_id)
        elif 'summary' in request.path:
            response = await view.generate_summary(request, pk=news_id)
        elif 'batch' in request.path:
            response = await view.batch_analyze(request)
        elif 'result' in request.path:
            response = await view.analysis_result(request, pk=news_id)
        elif 'analyze' in request.path:
            response = await view.analyze_with_rules(request, pk=news_id)
        else:
            raise ValueError(f"Unknown request path: {request.path}")
            
        return response 