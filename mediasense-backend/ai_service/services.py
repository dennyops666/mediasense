import asyncio
import csv
import hashlib
import io
import json
from datetime import timedelta, datetime
from io import BytesIO, StringIO
from typing import Any, Dict, List

import openai
import openpyxl
import pandas as pd
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from asgiref.sync import sync_to_async
from django.core.cache import cache
import redis
from openai import AsyncOpenAI

from news.models import NewsArticle, NewsCategory

from .models import AnalysisCache, AnalysisResult, AnalysisRule

class RateLimitExceeded(Exception):
    """速率限制异常"""
    pass

class AIService:
    """AI服务类，提供文本分析相关功能"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化 AI 服务"""
        if self._initialized:
            return
            
        self.openai_client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=settings.OPENAI_TIMEOUT
        )
        self.openai_model = "gpt-3.5-turbo"
        self.openai_temperature = 0.7
        self.openai_max_tokens = 500
        self.rate_limit = settings.OPENAI_RATE_LIMIT
        self.rate_limit_window = settings.OPENAI_RATE_LIMIT_WINDOW
        self.cache_ttl = settings.OPENAI_CACHE_TTL
        
        # 在测试环境中使用本地内存缓存
        if getattr(settings, 'TESTING', False):
            self.redis_client = None
        else:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB
            )
            
        self.rate_limit_key = "ai_service_rate_limit"
        self.rate_limit_max_requests = 5  # 每分钟最多5个请求
        self._request_count = 0
        self._last_request_time = None
        
        self._initialized = True

    def reset_rate_limit(self):
        """重置速率限制计数器"""
        self._request_count = 0
        self._last_request_time = None

    def _get_cache_key(self, content: str, analysis_type: str) -> str:
        """生成缓存键"""
        content_hash = hashlib.md5(content.encode()).hexdigest()
        return f"ai_service:{analysis_type}:{content_hash}"

    async def _check_rate_limit(self) -> bool:
        """检查速率限制"""
        if getattr(settings, 'TESTING', False):
            # 测试环境下不进行速率限制
            return True
            
        current_time = timezone.now()
        
        if self._last_request_time is None:
            self._last_request_time = current_time
            self._request_count = 1
            return True
            
        time_diff = (current_time - self._last_request_time).total_seconds()
        
        if time_diff > self.rate_limit_window:
            self._request_count = 1
            self._last_request_time = current_time
            return True
            
        if self._request_count >= self.rate_limit_max_requests:
            raise RateLimitExceeded("API调用次数超限")
            
        self._request_count += 1
        return True

    async def _get_cached_result(self, cache_key: str, analysis_type: str = None) -> Dict:
        """获取缓存的分析结果"""
        try:
            if analysis_type:
                cache_key = f"{cache_key}:{analysis_type}"
            cached_result = await sync_to_async(cache.get)(cache_key)
            if cached_result:
                return json.loads(cached_result) if isinstance(cached_result, str) else cached_result
        except Exception:
            pass
        return None

    async def _cache_result(self, cache_key: str, result: Dict, analysis_type: str = None) -> None:
        """缓存分析结果"""
        try:
            if analysis_type:
                cache_key = f"{cache_key}:{analysis_type}"
            result_str = json.dumps(result) if isinstance(result, dict) else result
            await sync_to_async(cache.set)(cache_key, result_str, self.cache_ttl)
        except Exception:
            pass

    async def analyze_sentiment(self, content):
        """分析文本情感"""
        if not content or not content.strip():
            raise ValueError("新闻内容为空")

        # 获取缓存
        cache_key = self._get_cache_key(content, "sentiment")
        cached_result = await self._get_cached_result(cache_key)
        if cached_result:
            return cached_result

        # 检查速率限制
        await self._check_rate_limit()

        try:
            response = await self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "你是一个情感分析专家。请分析以下文本的情感倾向，并给出分析结果。"},
                    {"role": "user", "content": f"请分析以下文本的情感倾向：\n\n{content}\n\n请以JSON格式返回分析结果，包含以下字段：\n- sentiment: 情感倾向（positive/negative/neutral）\n- confidence: 置信度（0-1之间的浮点数）\n- explanation: 分析说明"}
                ],
                temperature=self.openai_temperature,
                max_tokens=self.openai_max_tokens
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # 缓存结果
            await self._cache_result(cache_key, result)
            
            return result
            
        except openai.RateLimitError as e:
            raise RateLimitExceeded(str(e))
        except openai.APIError as e:
            raise ValueError(f"API错误: {str(e)}")
        except json.JSONDecodeError:
            raise ValueError("API返回格式错误")
        except Exception as e:
            raise ValueError(f"分析失败: {str(e)}")

    async def extract_keywords(self, content):
        """提取新闻关键词"""
        if not content or not isinstance(content, str) or not content.strip():
            raise ValueError("新闻内容不能为空")

        # 获取缓存
        cache_key = self._get_cache_key(content, "keywords")
        cached_result = await self._get_cached_result(cache_key)
        if cached_result:
            return cached_result

        try:
            # 检查速率限制
            await self._check_rate_limit()

            # 调用OpenAI API
            response = await self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "你是一个专业的新闻关键词提取助手。请提取5-10个重要关键词,并给出每个关键词的重要性得分(0-1)。"},
                    {"role": "user", "content": f"请从以下文本中提取关键词：\n\n{content}\n\n请以JSON格式返回结果，包含keywords数组，每个元素包含word和score字段。"}
                ],
                temperature=self.openai_temperature,
                max_tokens=self.openai_max_tokens
            )

            # 解析结果
            result = json.loads(response.choices[0].message.content)

            # 验证结果格式
            if not isinstance(result, dict) or 'keywords' not in result or not isinstance(result['keywords'], list):
                raise ValueError("API返回格式错误")

            # 验证关键词格式
            for keyword in result['keywords']:
                if not isinstance(keyword, dict) or 'word' not in keyword or 'score' not in keyword:
                    raise ValueError("关键词格式错误")

            # 缓存结果
            await self._cache_result(cache_key, result)

            return result

        except RateLimitExceeded:
            raise
        except openai.RateLimitError:
            raise RateLimitExceeded("API调用次数超限")
        except openai.APIError as e:
            raise ValueError(f"API错误: {str(e)}")
        except json.JSONDecodeError:
            raise ValueError("API返回格式错误")
        except ValueError as e:
            raise e
        except Exception as e:
            raise ValueError(f"内部错误: {str(e)}")

    async def generate_summary(self, content):
        """生成新闻摘要"""
        if not content or not isinstance(content, str) or not content.strip():
            raise ValueError("新闻内容不能为空")

        # 获取缓存
        cache_key = self._get_cache_key(content, "summary")
        cached_result = await self._get_cached_result(cache_key)
        if cached_result:
            return cached_result

        try:
            # 检查速率限制
            await self._check_rate_limit()

            # 调用OpenAI API
            response = await self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "你是一个专业的新闻摘要生成助手。请生成一个简短的新闻摘要,并给出置信度得分(0-1)。"},
                    {"role": "user", "content": f"请为以下文本生成摘要：\n\n{content}\n\n请以JSON格式返回结果，包含summary和confidence字段。"}
                ],
                temperature=self.openai_temperature,
                max_tokens=self.openai_max_tokens
            )

            # 解析结果
            result = json.loads(response.choices[0].message.content)

            # 验证结果格式
            if not isinstance(result, dict) or 'summary' not in result or 'confidence' not in result:
                raise ValueError("API返回格式错误")

            # 缓存结果
            await self._cache_result(cache_key, result)

            return result

        except RateLimitExceeded:
            raise
        except openai.RateLimitError:
            raise RateLimitExceeded("API调用次数超限")
        except openai.APIError as e:
            raise ValueError(f"API错误: {str(e)}")
        except json.JSONDecodeError:
            raise ValueError("API返回格式错误")
        except ValueError as e:
            raise e
        except Exception as e:
            raise ValueError(f"内部错误: {str(e)}")

    async def create_batch_analysis_task(self, news_ids, analysis_types):
        """创建批量分析任务"""
        if not news_ids:
            raise ValueError("新闻ID列表不能为空")
        if not analysis_types:
            raise ValueError("分析类型列表不能为空")

        try:
            # 创建任务
            task = await sync_to_async(BatchAnalysisTask.objects.create)(
                status='pending',
                total_count=len(news_ids),
                processed=0,
                success=0,
                failed=0
            )

            # 异步处理每篇新闻
            for news_id in news_ids:
                try:
                    news = await sync_to_async(NewsArticle.objects.get)(id=news_id)
                    if 'sentiment' in analysis_types:
                        await self.analyze_sentiment(news.content)
                    if 'keywords' in analysis_types:
                        await self.extract_keywords(news.content)
                    if 'summary' in analysis_types:
                        await self.generate_summary(news.content)
                    task.success += 1
                except Exception as e:
                    task.failed += 1
                    task.error_message = str(e)
                finally:
                    task.processed += 1
                    await sync_to_async(task.save)()

            # 更新任务状态
            task.status = 'completed'
            task.completed_at = timezone.now()
            await sync_to_async(task.save)()

            return task

        except Exception as e:
            raise ValueError(f"创建任务失败: {str(e)}")

    async def invalidate_cache(self, news_id: int) -> None:
        """清除缓存"""
        try:
            # 更新数据库中的分析结果状态
            results = await sync_to_async(AnalysisResult.objects.filter)(news_id=news_id)
            await sync_to_async(lambda: results.update(is_valid=False))()
            
            # 清除Redis缓存
            pattern = f"ai_service:*:*:{news_id}"
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                
        except Exception as e:
            raise ValueError(f"清除缓存失败: {str(e)}")

    async def clean_expired_cache(self):
        """清理过期缓存"""
        try:
            results = await sync_to_async(AnalysisResult.objects.filter)(
                created_at__lt=timezone.now() - timedelta(seconds=self.cache_ttl)
            )
            await sync_to_async(results.delete)()
        except Exception as e:
            raise ValueError(f"清理缓存失败: {str(e)}")

    async def batch_analyze(
        self, news_articles: List[NewsArticle], analysis_types: List[str] = None
    ) -> Dict[int, Dict[str, Any]]:
        """批量分析新闻文章"""
        if analysis_types is None:
            analysis_types = ["sentiment", "keywords", "summary"]

        results = {}
        
        for article in news_articles:
            article_results = {}
            
            # 重置速率限制
            self.reset_rate_limit()

            for analysis_type in analysis_types:
                try:
                    if analysis_type == "sentiment":
                        result = await self.analyze_sentiment(article.content)
                        article_results["sentiment"] = result
                    elif analysis_type == "keywords":
                        result = await self.extract_keywords(article.content)
                        article_results["keywords"] = result["keywords"]
                    elif analysis_type == "summary":
                        result = await self.generate_summary(article.content)
                        article_results["summary"] = result
                except Exception as e:
                    article_results[analysis_type] = {
                        "error": str(e),
                        "success": False
                    }

            results[article.id] = article_results

        return results

    async def analyze_unprocessed_news(self) -> Dict[int, Dict[str, Any]]:
        """
        分析所有未处理的新闻文章

        Returns:
            Dict[int, Dict[str, Any]]: 分析结果字典
        """
        # 查找所有未分析的新闻
        unprocessed_news = NewsArticle.objects.filter(
            Q(analysis_results__isnull=True)  # 没有任何分析结果
            | Q(analysis_results__is_valid=False)  # 或之前的分析无效
        ).distinct()

        if not unprocessed_news.exists():
            return {}

        # 执行批量分析
        return await self.batch_analyze(list(unprocessed_news))

    async def analyze_news_by_criteria(
        self, start_date=None, end_date=None, categories=None, status=None, analysis_types=None
    ) -> Dict[int, Dict[str, Any]]:
        """
        根据条件批量分析新闻

        Args:
            start_date: 开始日期
            end_date: 结束日期
            categories: 分类ID列表
            status: 新闻状态
            analysis_types: 分析类型列表

        Returns:
            Dict[int, Dict[str, Any]]: 分析结果字典
        """
        # 构建查询条件
        query = Q()
        if start_date:
            query &= Q(created_at__gte=start_date)
        if end_date:
            query &= Q(created_at__lte=end_date)
        if categories:
            query &= Q(category_id__in=categories)
        if status:
            query &= Q(status=status)

        # 查询符合条件的新闻
        news_articles = NewsArticle.objects.filter(query)

        if not news_articles.exists():
            return {}

        # 执行批量分析
        return await self.batch_analyze(list(news_articles), analysis_types=analysis_types)

    async def analyze_with_rules(self, content: str, rules: List[AnalysisRule]) -> Dict[str, Any]:
        """
        使用多个规则分析文本
        """
        results = {}
        for rule in rules:
            try:
                result = await self.analyze_with_rule(content, rule)
                results[str(rule.id)] = result
            except Exception as e:
                results[str(rule.id)] = {
                    "error": str(e),
                    "status": "failed"
                }
        return results

    async def analyze_with_rule(self, content: str, rule: AnalysisRule) -> Dict[str, Any]:
        """
        使用单个规则分析文本
        """
        if not await self._check_rate_limit():
            raise RateLimitExceeded("API调用次数超限，请稍后重试")

        # 生成提示词
        system_prompt = rule.system_prompt
        user_prompt = rule.user_prompt_template.format(
            title="",  # 暂时不使用标题
            content=content
        )

        try:
            # 调用OpenAI API
            response = await self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=float(rule.parameters.get("temperature", self.openai_temperature)),
                max_tokens=int(rule.parameters.get("max_tokens", self.openai_max_tokens))
            )

            # 解析响应
            result = json.loads(response.choices[0].message.content)
            return result

        except json.JSONDecodeError:
            raise ValueError("AI返回的结果格式不正确")
        except Exception as e:
            raise e

    def export_analysis_results(
        self, format="csv", start_date=None, end_date=None, analysis_types=None, categories=None
    ):
        """
        导出分析结果
        """
        # 构建查询条件
        query = Q()
        if start_date:
            query &= Q(created_at__gte=start_date)
        if end_date:
            query &= Q(created_at__lte=end_date)
        if analysis_types:
            query &= Q(analysis_type__in=analysis_types)
        if categories:
            query &= Q(news__category_id__in=categories)

        # 获取分析结果
        results = AnalysisResult.objects.filter(query).select_related("news")

        # 准备数据
        data = []
        for result in results:
            row = {
                "新闻ID": result.news.id,
                "新闻标题": result.news.title,
                "新闻分类": result.news.category.name if result.news.category else "",
                "分析类型": result.analysis_type,
                "分析结果": result.result,
                "是否有效": result.is_valid,
                "错误信息": result.error_message,
                "创建时间": result.created_at,
                "更新时间": result.updated_at,
            }
            data.append(row)

        # 创建DataFrame
        df = pd.DataFrame(data)

        # 导出数据
        buffer = io.BytesIO()
        if format == "csv":
            df.to_csv(buffer, index=False, encoding="utf-8-sig")
            content_type = "text/csv"
            file_ext = ".csv"
        else:  # excel
            df.to_excel(buffer, index=False)
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            file_ext = ".xlsx"

        buffer.seek(0)
        content = buffer.getvalue()
        buffer.close()

        return content, content_type, file_ext

    def export_rule_analysis_results(self, rule_id, format="csv", start_date=None, end_date=None):
        """
        导出规则分析结果
        """
        # 构建查询条件
        query = Q(rule_id=rule_id)
        if start_date:
            query &= Q(created_at__gte=start_date)
        if end_date:
            query &= Q(created_at__lte=end_date)

        # 获取分析结果
        results = RuleAnalysisResult.objects.filter(query).select_related("news", "rule")

        # 准备数据
        data = []
        for result in results:
            row = {
                "新闻ID": result.news.id,
                "新闻标题": result.news.title,
                "新闻分类": result.news.category.name if result.news.category else "",
                "规则名称": result.rule.name,
                "规则描述": result.rule.description,
                "匹配结果": result.matched,
                "匹配详情": result.match_details,
                "创建时间": result.created_at,
            }
            data.append(row)

        # 创建DataFrame
        df = pd.DataFrame(data)

        # 导出数据
        buffer = io.BytesIO()
        if format == "csv":
            df.to_csv(buffer, index=False, encoding="utf-8-sig")
            content_type = "text/csv"
            file_ext = ".csv"
        else:  # excel
            df.to_excel(buffer, index=False)
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            file_ext = ".xlsx"

        buffer.seek(0)
        content = buffer.getvalue()
        buffer.close()

        return content, content_type, file_ext

    async def analyze_text(self, content: str, analysis_types: List[str]) -> Dict[str, Any]:
        """
        分析文本内容
        """
        if not await self._check_rate_limit():
            raise RateLimitExceeded("API调用次数超限，请稍后重试")

        results = {}
        for analysis_type in analysis_types:
            try:
                if analysis_type == 'sentiment':
                    # 生成提示词
                    system_prompt = "你是一个文本分析助手，专门进行情感分析。请分析以下文本的情感倾向，并给出分析结果。"
                    user_prompt = f"请分析以下文本的情感倾向：\n\n{content}"

                    # 调用OpenAI API
                    response = await self.openai_client.chat.completions.create(
                        model=self.openai_model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=self.openai_temperature,
                        max_tokens=self.openai_max_tokens
                    )

                    # 解析响应
                    result = json.loads(response.choices[0].message.content)
                    results[analysis_type] = result
                else:
                    raise ValueError(f"不支持的分析类型: {analysis_type}")

            except json.JSONDecodeError:
                raise ValueError("AI返回的结果格式不正确")
            except Exception as e:
                raise e

        return results


class NotificationService:
    """通知服务类"""

    @staticmethod
    def create_notification(user, notification_type, title, content, data=None):
        """创建通知"""
        try:
            # 检查用户的通知订阅设置
            subscription = NotificationSubscription.objects.get(user=user)
            should_notify = False

            # 根据通知类型和订阅设置判断是否需要通知
            if notification_type == AnalysisNotification.NotificationType.ANALYSIS_COMPLETE:
                should_notify = subscription.notify_on_complete
            elif notification_type == AnalysisNotification.NotificationType.ANALYSIS_ERROR:
                should_notify = subscription.notify_on_error
            elif notification_type == AnalysisNotification.NotificationType.BATCH_COMPLETE:
                should_notify = subscription.notify_on_batch
            elif notification_type == AnalysisNotification.NotificationType.SCHEDULE_COMPLETE:
                should_notify = subscription.notify_on_schedule

            if not should_notify:
                return None

            # 创建通知记录
            notification = AnalysisNotification.objects.create(
                user=user, notification_type=notification_type, title=title, content=content, data=data or {}
            )

            # 发送WebSocket通知
            if subscription.websocket_enabled:
                from asgiref.sync import async_to_sync
                from channels.layers import get_channel_layer

                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f"user_{user.id}_notifications",
                    {
                        "type": "notification.message",
                        "message": {
                            "id": notification.id,
                            "type": notification.notification_type,
                            "title": notification.title,
                            "content": notification.content,
                            "data": notification.data,
                            "created_at": notification.created_at.isoformat(),
                        },
                    },
                )

            # 发送邮件通知
            if subscription.email_enabled:
                from django.conf import settings
                from django.core.mail import send_mail

                send_mail(
                    subject=notification.title,
                    message=notification.content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,
                )

            return notification

        except NotificationSubscription.DoesNotExist:
            # 用户未配置通知订阅，创建默认配置
            NotificationSubscription.objects.create(user=user)
            return None
        except Exception as e:
            logger.error(f"创建通知失败: {str(e)}", exc_info=True)
            return None

    @staticmethod
    def mark_as_read(notification_id, user):
        """标记通知为已读"""
        try:
            notification = AnalysisNotification.objects.get(id=notification_id, user=user)
            notification.is_read = True
            notification.save()
            return True
        except AnalysisNotification.DoesNotExist:
            return False

    @staticmethod
    def mark_all_as_read(user):
        """标记所有通知为已读"""
        AnalysisNotification.objects.filter(user=user, is_read=False).update(is_read=True)

    @staticmethod
    def get_unread_count(user):
        """获取未读通知数量"""
        return AnalysisNotification.objects.filter(user=user, is_read=False).count()

    @staticmethod
    def get_notifications(user, page=1, page_size=20, unread_only=False):
        """获取用户的通知列表"""
        queryset = AnalysisNotification.objects.filter(user=user)
        if unread_only:
            queryset = queryset.filter(is_read=False)

        from django.core.paginator import Paginator

        paginator = Paginator(queryset, page_size)
        return paginator.get_page(page)


class VisualizationService:
    """可视化服务类"""

    @staticmethod
    def generate_chart_data(visualization):
        """生成图表数据"""
        from datetime import timedelta

        from django.db.models import Avg, Count, Max, Min, Sum
        from django.utils import timezone

        # 构建基础查询集
        queryset = AnalysisResult.objects.filter(
            data_type=visualization.data_type, created_at__gte=timezone.now() - timedelta(days=visualization.time_range)
        )

        # 添加分类过滤
        if visualization.categories:
            queryset = queryset.filter(news__category_id__in=visualization.categories)

        # 添加自定义过滤条件
        if visualization.filters:
            queryset = queryset.filter(**visualization.filters)

        # 准备聚合函数
        aggregation_funcs = {"count": Count, "avg": Avg, "sum": Sum, "max": Max, "min": Min}

        # 获取聚合函数
        agg_func = aggregation_funcs[visualization.aggregation_method]

        # 执行分组和聚合
        data = (
            queryset.values(visualization.group_by)
            .annotate(value=agg_func(visualization.aggregation_field))
            .order_by(visualization.group_by)
        )

        # 格式化数据
        if visualization.chart_type == AnalysisVisualization.ChartType.LINE:
            chart_data = {
                "xAxis": [str(item[visualization.group_by]) for item in data],
                "series": [{"name": "数值", "data": [item["value"] for item in data]}],
            }

        elif visualization.chart_type == AnalysisVisualization.ChartType.BAR:
            chart_data = {
                "xAxis": [str(item[visualization.group_by]) for item in data],
                "series": [{"name": "数值", "data": [item["value"] for item in data]}],
            }

        elif visualization.chart_type == AnalysisVisualization.ChartType.PIE:
            chart_data = {
                "series": [
                    {
                        "name": "数值",
                        "data": [{"name": str(item[visualization.group_by]), "value": item["value"]} for item in data],
                    }
                ]
            }

        elif visualization.chart_type == AnalysisVisualization.ChartType.RADAR:
            chart_data = {
                "indicator": [{"name": str(item[visualization.group_by])} for item in data],
                "series": [{"name": "数值", "data": [{"value": [item["value"] for item in data]}]}],
            }

        # 更新缓存
        visualization.cached_data = chart_data
        visualization.last_generated = timezone.now()
        visualization.save()

        return chart_data

    @staticmethod
    def get_chart_data(visualization):
        """获取图表数据，如果缓存有效则返回缓存数据"""
        from datetime import timedelta

        from django.utils import timezone

        # 检查缓存是否有效
        if (
            visualization.cached_data
            and visualization.last_generated
            and visualization.last_generated >= timezone.now() - timedelta(hours=1)
        ):
            return visualization.cached_data

        # 生成新数据
        return VisualizationService.generate_chart_data(visualization)

    @staticmethod
    def get_available_fields():
        """获取可用的字段列表"""
        return {
            "aggregation_fields": [
                {"value": "result", "label": "分析结果"},
                {"value": "is_valid", "label": "是否有效"},
                {"value": "created_at", "label": "创建时间"},
            ],
            "group_by_fields": [
                {"value": "news__category", "label": "新闻分类"},
                {"value": "analysis_type", "label": "分析类型"},
                {"value": "created_at__date", "label": "日期"},
            ],
        }
