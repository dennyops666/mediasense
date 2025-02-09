from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, viewsets
import logging
import openai
import os
import json
import aiohttp
import asyncio
from django.conf import settings
from django.core.cache import cache

# 配置OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_API_BASE = os.getenv('OPENAI_API_BASE', 'https://api.openai-proxy.com/v1')

logger = logging.getLogger(__name__)

async def call_openai_api(messages, max_tokens=100):
    """调用OpenAI API的异步函数"""
    try:
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": settings.OPENAI_MODEL,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": max_tokens
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{OPENAI_API_BASE}/chat/completions",
                headers=headers,
                json=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['choices'][0]['message']['content'].strip()
                else:
                    error_text = await response.text()
                    logger.error(f"OpenAI API error: {error_text}")
                    raise Exception(f"OpenAI API error: {response.status}")
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {str(e)}", exc_info=True)
        raise

class AIServiceViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """获取可用的 AI 服务列表"""
        try:
            services = [
                {
                    "id": "text_analysis",
                    "name": "文本分析",
                    "description": "对文本进行情感分析、关键词提取等",
                    "status": "active",
                    "api_endpoint": "/api/ai/services/text-analysis/",
                    "supported_features": ["sentiment", "keywords", "summary"]
                },
                {
                    "id": "news_classification",
                    "name": "新闻分类",
                    "description": "对新闻文章进行主题分类",
                    "status": "active",
                    "api_endpoint": "/api/ai/services/classification/",
                    "supported_features": ["category", "tags"]
                },
                {
                    "id": "content_generation",
                    "name": "内容生成",
                    "description": "生成新闻摘要、标题等",
                    "status": "active",
                    "api_endpoint": "/api/ai/services/generation/",
                    "supported_features": ["summary", "title", "keywords"]
                }
            ]
            logger.info("Successfully retrieved AI services list")
            return Response({"services": services})
        except Exception as e:
            logger.error(f"Error retrieving AI services list: {str(e)}")
            return Response(
                {"error": "Failed to retrieve AI services"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class TextAnalysisViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.ai_service = AIService()

    async def create(self, request):
        """文本分析服务"""
        try:
            text = request.data.get('text')
            features = request.data.get('features', [])
            
            self.logger.info(f"收到文本分析请求: features={features}")
            self.logger.debug(f"文本内容: {text[:100]}...")
            
            if not text:
                self.logger.warning("请求中缺少文本内容")
                return Response(
                    {"error": "Text is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # 验证API密钥是否配置
            if not OPENAI_API_KEY:
                self.logger.error("OpenAI API key未配置")
                return Response(
                    {"error": "OpenAI API is not properly configured"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
                
            result = {
                "text": text,
                "analysis": {}
            }
            
            # 使用缓存来提高性能
            cache_key = f"text_analysis:{hash(text)}:{','.join(sorted(features))}"
            cached_result = cache.get(cache_key)
            if cached_result:
                self.logger.info("返回缓存的分析结果")
                return Response(cached_result)
            
            # 根据请求的特性进行分析
            if "sentiment" in features:
                try:
                    self.logger.info("开始情感分析")
                    sentiment_result = await self.ai_service.analyze_sentiment(text)
                    result["analysis"]["sentiment"] = sentiment_result
                    self.logger.info(f"情感分析完成: {sentiment_result}")
                except Exception as e:
                    self.logger.error(f"情感分析失败: {str(e)}", exc_info=True)
                    result["analysis"]["sentiment"] = {
                        "sentiment": "neutral",
                        "confidence": 0.0,
                        "explanation": f"分析失败: {str(e)}"
                    }
            
            if "keywords" in features:
                try:
                    self.logger.info("开始关键词提取")
                    keywords_result = await self.ai_service.extract_keywords(text)
                    result["analysis"]["keywords"] = keywords_result
                    self.logger.info(f"关键词提取完成: {keywords_result}")
                except Exception as e:
                    self.logger.error(f"关键词提取失败: {str(e)}", exc_info=True)
                    result["analysis"]["keywords"] = {
                        "terms": [],
                        "weights": []
                    }
                
            if "summary" in features:
                try:
                    self.logger.info("开始生成摘要")
                    summary_result = await self.ai_service.generate_summary(text)
                    result["analysis"]["summary"] = summary_result
                    self.logger.info(f"摘要生成完成: {summary_result}")
                except Exception as e:
                    self.logger.error(f"摘要生成失败: {str(e)}", exc_info=True)
                    result["analysis"]["summary"] = {
                        "text": text[:100] + "...",
                        "length": "short",
                        "key_points": []
                    }
            
            # 缓存结果
            try:
                cache.set(cache_key, result, timeout=3600)  # 缓存1小时
                self.logger.info("分析结果已缓存")
            except Exception as e:
                self.logger.error(f"缓存结果失败: {str(e)}", exc_info=True)
            
            return Response(result)
            
        except Exception as e:
            self.logger.error(f"文本分析服务出错: {str(e)}", exc_info=True)
            return Response(
                {"error": "Text analysis failed", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class NewsClassificationViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    def create(self, request):
        """新闻分类服务"""
        try:
            content = request.data.get('content')
            title = request.data.get('title', '')
                
            if not content:
                return Response(
                    {"error": "Content is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # 验证API密钥是否配置
            if not OPENAI_API_KEY:
                logger.error("OpenAI API key is not configured")
                return Response(
                    {"error": "OpenAI API is not properly configured"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            # 使用缓存来提高性能
            cache_key = f"news_classification:{hash(content + title)}"
            cached_result = cache.get(cache_key)
            if cached_result:
                logger.info("Returning cached classification result")
                return Response(cached_result)
            
            # 创建事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                logger.info("Starting news classification")
                classification_prompt = (
                    "请对以下新闻文章进行分类，并以JSON格式返回结果。格式要求：\n"
                    "{\n"
                    '  "category": "分类名称",\n'
                    '  "tags": ["标签1", "标签2", ...],\n'
                    '  "confidence": 0.0-1.0,\n'
                    '  "subcategories": ["子分类1", "子分类2", ...],\n'
                    '  "explanation": "分类理由"\n'
                    "}\n\n"
                    f"标题：{title}\n"
                    f"内容：{content}"
                )
                
                classification_result = loop.run_until_complete(
                    call_openai_api([{"role": "user", "content": classification_prompt}], max_tokens=200)
                )
                
                try:
                    result = json.loads(classification_result)
                    # 验证和规范化结果
                    result = {
                        "category": result.get("category", "未分类"),
                        "tags": result.get("tags", [])[:5],  # 最多保留5个标签
                        "confidence": float(result.get("confidence", 0.0)),
                        "subcategories": result.get("subcategories", [])[:3],  # 最多保留3个子分类
                        "explanation": result.get("explanation", "无分类说明")
                    }
                    logger.info(f"Classification completed: {result}")
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    logger.error(f"Error parsing classification result: {str(e)}")
                    result = {
                        "category": "未分类",
                        "tags": [],
                        "confidence": 0.0,
                        "subcategories": [],
                        "explanation": "分类过程出错"
                    }
                
                # 缓存结果（1小时）
                cache.set(cache_key, result, timeout=3600)
                logger.info("Classification results cached")
                
                return Response(result)
                
            except Exception as e:
                logger.error(f"Error in classification: {str(e)}", exc_info=True)
                return Response(
                    {
                        "category": "未分类",
                        "tags": [],
                        "confidence": 0.0,
                        "subcategories": [],
                        "explanation": f"分类失败：{str(e)}"
                    }
                )
                
        except Exception as e:
            logger.error(f"Error in news classification: {str(e)}", exc_info=True)
            return Response(
                {"error": "News classification failed", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ContentGenerationViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    def create(self, request):
        """内容生成服务"""
        try:
            content = request.data.get('content')
            features = request.data.get('features', [])
            
            if not content:
                return Response(
                    {"error": "Content is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # 验证API密钥是否配置
            if not OPENAI_API_KEY:
                logger.error("OpenAI API key is not configured")
                return Response(
                    {"error": "OpenAI API is not properly configured"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            # 使用缓存来提高性能
            cache_key = f"content_generation:{hash(content)}:{','.join(sorted(features))}"
            cached_result = cache.get(cache_key)
            if cached_result:
                logger.info("Returning cached generation result")
                return Response(cached_result)
            
            # 创建事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = {
                "content": content,
                "generated": {}
            }
            
            try:
                # 根据请求的特性生成内容
                if "summary" in features:
                    logger.info("Starting summary generation")
                    summary_prompt = (
                        "请生成以下内容的摘要，并以JSON格式返回结果。格式要求：\n"
                        "{\n"
                        '  "summary": "摘要内容",\n'
                        '  "word_count": 整数,\n'
                        '  "key_points": ["要点1", "要点2", ...],\n'
                        '  "style": "formal/casual/technical"\n'
                        "}\n\n"
                        f"原文内容：{content}"
                    )
                    
                    summary_result = loop.run_until_complete(
                        call_openai_api([{"role": "user", "content": summary_prompt}], max_tokens=300)
                    )
                    
                    try:
                        summary_data = json.loads(summary_result)
                        result["generated"]["summary"] = {
                            "text": summary_data["summary"],
                            "word_count": int(summary_data["word_count"]),
                            "key_points": summary_data["key_points"],
                            "style": summary_data["style"]
                        }
                    except (json.JSONDecodeError, KeyError, ValueError) as e:
                        logger.error(f"Error parsing summary result: {str(e)}")
                        result["generated"]["summary"] = {
                            "text": content[:100] + "...",
                            "word_count": len(content.split()),
                            "key_points": [],
                            "style": "formal"
                        }
                    
                if "title" in features:
                    logger.info("Starting title generation")
                    title_prompt = (
                        "请为以下内容生成标题，并以JSON格式返回结果。格式要求：\n"
                        "{\n"
                        '  "title": "主标题",\n'
                        '  "subtitle": "副标题",\n'
                        '  "seo_title": "SEO优化标题",\n'
                        '  "variations": ["变体1", "变体2", ...]\n'
                        "}\n\n"
                        f"文章内容：{content}"
                    )
                    
                    title_result = loop.run_until_complete(
                        call_openai_api([{"role": "user", "content": title_prompt}], max_tokens=200)
                    )
                    
                    try:
                        title_data = json.loads(title_result)
                        result["generated"]["title"] = {
                            "main": title_data["title"],
                            "subtitle": title_data["subtitle"],
                            "seo": title_data["seo_title"],
                            "variations": title_data["variations"][:3]  # 最多保留3个变体
                        }
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.error(f"Error parsing title result: {str(e)}")
                        result["generated"]["title"] = {
                            "main": "未生成标题",
                            "subtitle": "",
                            "seo": "",
                            "variations": []
                        }
                    
                if "keywords" in features:
                    logger.info("Starting keywords generation")
                    keywords_prompt = (
                        "请为以下内容生成关键词，并以JSON格式返回结果。格式要求：\n"
                        "{\n"
                        '  "keywords": ["关键词1", "关键词2", ...],\n'
                        '  "weights": [0.9, 0.8, ...],\n'
                        '  "categories": ["分类1", "分类2", ...],\n'
                        '  "seo_tags": ["标签1", "标签2", ...]\n'
                        "}\n\n"
                        f"文章内容：{content}"
                    )
                    
                    keywords_result = loop.run_until_complete(
                        call_openai_api([{"role": "user", "content": keywords_prompt}], max_tokens=200)
                    )
                    
                    try:
                        keywords_data = json.loads(keywords_result)
                        result["generated"]["keywords"] = {
                            "terms": keywords_data["keywords"][:5],  # 最多保留5个关键词
                            "weights": keywords_data["weights"][:5],  # 对应的权重
                            "categories": keywords_data["categories"][:3],  # 最多保留3个分类
                            "seo_tags": keywords_data["seo_tags"][:5]  # 最多保留5个SEO标签
                        }
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.error(f"Error parsing keywords result: {str(e)}")
                        result["generated"]["keywords"] = {
                            "terms": [],
                            "weights": [],
                            "categories": [],
                            "seo_tags": []
                        }
                
                # 缓存结果（1小时）
                cache.set(cache_key, result, timeout=3600)
                logger.info("Generation results cached")
                
                return Response(result)
                
            except Exception as e:
                logger.error(f"Error in content generation: {str(e)}", exc_info=True)
                return Response(
                    {
                        "content": content,
                        "generated": {
                            "error": f"生成失败：{str(e)}",
                            "summary": {"text": content[:100] + "..."} if "summary" in features else None,
                            "title": {"main": "生成失败"} if "title" in features else None,
                            "keywords": {"terms": []} if "keywords" in features else None
                        }
                    }
                )
                
        except Exception as e:
            logger.error(f"Error in content generation: {str(e)}", exc_info=True)
            return Response(
                {"error": "Content generation failed", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )