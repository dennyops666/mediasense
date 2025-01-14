import asyncio
import csv
import hashlib
import io
import json
from datetime import timedelta
from io import BytesIO, StringIO
from typing import Any, Dict, List

import openai
import openpyxl
import pandas as pd
from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from news.models import NewsArticle, NewsCategory

from .models import AnalysisCache, AnalysisResult, AnalysisRule


class AIService:
    """AI服务类，提供文本分析相关功能"""

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.api_base = settings.OPENAI_API_BASE
        self.model = settings.OPENAI_MODEL
        self.temperature = settings.OPENAI_TEMPERATURE
        self.max_tokens = settings.OPENAI_MAX_TOKENS

        # 配置OpenAI客户端
        openai.api_key = self.api_key
        openai.api_base = self.api_base

        self.cache_ttl = timedelta(hours=24)  # 缓存24小时

    def _get_cache_key(self, text, analysis_type):
        """生成缓存键"""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return f"{analysis_type}:{text_hash}"

    def _get_cached_result(self, cache_key):
        """获取缓存结果"""
        try:
            cache = AnalysisCache.objects.get(cache_key=cache_key, expires_at__gt=timezone.now())
            return cache.result
        except AnalysisCache.DoesNotExist:
            return None

    def _cache_result(self, cache_key, result):
        """缓存分析结果"""
        expires_at = timezone.now() + self.cache_ttl
        AnalysisCache.objects.create(cache_key=cache_key, result=result, expires_at=expires_at)

    async def analyze_sentiment(self, news_article):
        """情感分析"""
        cache_key = self._get_cache_key(news_article.content, "sentiment")
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            return cached_result

        try:
            # 调用OpenAI API进行情感分析
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的新闻情感分析助手。请分析以下新闻文本的情感倾向，并给出详细分析。",
                    },
                    {"role": "user", "content": f"标题：{news_article.title}\n\n正文：{news_article.content}"},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            result = {"sentiment": response.choices[0].message["content"], "score": 0.0}  # TODO: 实现情感分数计算

            # 缓存结果
            self._cache_result(cache_key, result)

            # 保存分析结果
            AnalysisResult.objects.update_or_create(
                news=news_article,
                analysis_type=AnalysisResult.AnalysisType.SENTIMENT,
                defaults={"result": result, "is_valid": True},
            )

            return result

        except Exception as e:
            # 记录错误
            AnalysisResult.objects.update_or_create(
                news=news_article,
                analysis_type=AnalysisResult.AnalysisType.SENTIMENT,
                defaults={"result": {}, "is_valid": False, "error_message": str(e)},
            )
            raise

    async def extract_keywords(self, news_article):
        """关键词提取"""
        cache_key = self._get_cache_key(news_article.content, "keywords")
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            return cached_result

        try:
            # 调用OpenAI API提取关键词
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的新闻关键词提取助手。请从以下新闻中提取最重要的10个关键词，并按重要性排序。每个关键词请给出重要性权重（1-10）。",
                    },
                    {"role": "user", "content": f"标题：{news_article.title}\n\n正文：{news_article.content}"},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            result = {"keywords": response.choices[0].message["content"], "timestamp": timezone.now().isoformat()}

            # 缓存结果
            self._cache_result(cache_key, result)

            # 保存分析结果
            AnalysisResult.objects.update_or_create(
                news=news_article,
                analysis_type=AnalysisResult.AnalysisType.KEYWORDS,
                defaults={"result": result, "is_valid": True},
            )

            return result

        except Exception as e:
            # 记录错误
            AnalysisResult.objects.update_or_create(
                news=news_article,
                analysis_type=AnalysisResult.AnalysisType.KEYWORDS,
                defaults={"result": {}, "is_valid": False, "error_message": str(e)},
            )
            raise

    async def generate_summary(self, news_article):
        """生成新闻摘要"""
        cache_key = self._get_cache_key(news_article.content, "summary")
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            return cached_result

        try:
            # 调用OpenAI API生成摘要
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的新闻摘要生成助手。请生成一段简洁的新闻摘要，突出新闻的主要内容和关键信息。摘要长度控制在200字以内。",
                    },
                    {"role": "user", "content": f"标题：{news_article.title}\n\n正文：{news_article.content}"},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            result = {"summary": response.choices[0].message["content"], "timestamp": timezone.now().isoformat()}

            # 缓存结果
            self._cache_result(cache_key, result)

            # 保存分析结果
            AnalysisResult.objects.update_or_create(
                news=news_article,
                analysis_type=AnalysisResult.AnalysisType.SUMMARY,
                defaults={"result": result, "is_valid": True},
            )

            return result

        except Exception as e:
            # 记录错误
            AnalysisResult.objects.update_or_create(
                news=news_article,
                analysis_type=AnalysisResult.AnalysisType.SUMMARY,
                defaults={"result": {}, "is_valid": False, "error_message": str(e)},
            )
            raise

    def invalidate_cache(self):
        """使所有缓存失效"""
        AnalysisCache.objects.filter(expires_at__gt=timezone.now()).update(expires_at=timezone.now())

    def clean_expired_cache(self):
        """清理过期缓存"""
        AnalysisCache.objects.filter(expires_at__lte=timezone.now()).delete()

    async def batch_analyze(
        self, news_articles: List[NewsArticle], analysis_types: List[str] = None
    ) -> Dict[int, Dict[str, Any]]:
        """
        批量分析新闻文章

        Args:
            news_articles: 新闻文章列表
            analysis_types: 分析类型列表，可选值：['sentiment', 'keywords', 'summary']
                          如果为None，则执行所有类型的分析

        Returns:
            Dict[int, Dict[str, Any]]: 分析结果字典，key为文章ID，value为各类分析结果
        """
        if analysis_types is None:
            analysis_types = ["sentiment", "keywords", "summary"]

        results = {}
        tasks = []

        for article in news_articles:
            article_tasks = []

            if "sentiment" in analysis_types:
                article_tasks.append(self.analyze_sentiment(article))
            if "keywords" in analysis_types:
                article_tasks.append(self.extract_keywords(article))
            if "summary" in analysis_types:
                article_tasks.append(self.generate_summary(article))

            # 将每篇文章的所有分析任务打包
            tasks.append((article.id, article_tasks))

        # 异步执行所有分析任务
        for article_id, article_tasks in tasks:
            try:
                # 并行执行单篇文章的所有分析任务
                article_results = await asyncio.gather(*article_tasks, return_exceptions=True)

                # 整理分析结果
                results[article_id] = {}
                for i, result in enumerate(article_results):
                    if isinstance(result, Exception):
                        # 如果某个分析任务失败，记录错误信息
                        analysis_type = analysis_types[i]
                        results[article_id][analysis_type] = {"error": str(result), "success": False}
                    else:
                        # 分析任务成功，记录结果
                        analysis_type = analysis_types[i]
                        results[article_id][analysis_type] = {"data": result, "success": True}

            except Exception as e:
                # 如果整个文章的分析过程失败，记录错误信息
                results[article_id] = {"error": str(e), "success": False}

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

    async def analyze_with_rule(self, news_article, rule):
        """使用自定义规则进行分析"""
        cache_key = f"{self._get_cache_key(news_article.content, rule.rule_type)}:rule_{rule.id}"
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            return cached_result

        try:
            # 生成用户提示词
            user_prompt = rule.user_prompt_template.format(title=news_article.title, content=news_article.content)

            # 调用OpenAI API
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[{"role": "system", "content": rule.system_prompt}, {"role": "user", "content": user_prompt}],
                temperature=float(rule.parameters.get("temperature", self.temperature)),
                max_tokens=int(rule.parameters.get("max_tokens", self.max_tokens)),
            )

            result = {
                "content": response.choices[0].message["content"],
                "rule_id": rule.id,
                "rule_name": rule.name,
                "timestamp": timezone.now().isoformat(),
            }

            # 缓存结果
            self._cache_result(cache_key, result)

            # 保存分析结果
            AnalysisResult.objects.update_or_create(
                news=news_article, analysis_type=rule.rule_type, defaults={"result": result, "is_valid": True}
            )

            return result

        except Exception as e:
            # 记录错误
            AnalysisResult.objects.update_or_create(
                news=news_article,
                analysis_type=rule.rule_type,
                defaults={"result": {}, "is_valid": False, "error_message": str(e)},
            )
            raise

    async def batch_analyze_with_rules(self, news_articles, rules=None):
        """使用自定义规则批量分析新闻"""
        if rules is None:
            # 获取所有启用的规则
            rules = AnalysisRule.objects.filter(is_active=True)

        results = {}
        for article in news_articles:
            article_results = {}
            for rule in rules:
                try:
                    result = await self.analyze_with_rule(article, rule)
                    article_results[rule.id] = {"data": result, "success": True}
                except Exception as e:
                    article_results[rule.id] = {"error": str(e), "success": False}
            results[article.id] = article_results

        return results

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
