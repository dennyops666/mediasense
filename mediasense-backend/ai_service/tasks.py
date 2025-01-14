import asyncio
import logging

from celery import shared_task
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from news.models import NewsArticle

from .models import AnalysisSchedule, BatchAnalysisResult, BatchAnalysisTask, ScheduleExecution
from .services import AIService

logger = logging.getLogger(__name__)


@shared_task
def process_batch_analysis(task_id):
    """
    处理批量分析任务
    """
    try:
        # 获取任务信息
        task = BatchAnalysisTask.objects.get(id=task_id)
        task.status = "processing"
        task.started_at = timezone.now()
        task.save()

        # 获取需要分析的新闻
        news_articles = NewsArticle.objects.filter(id__in=task.news_ids)

        # 创建AI服务实例
        ai_service = AIService()

        # 运行异步分析
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(
                ai_service.batch_analyze(list(news_articles), analysis_types=task.analysis_types)
            )
        finally:
            loop.close()

        # 保存分析结果
        with transaction.atomic():
            for article_id, article_results in results.items():
                BatchAnalysisResult.objects.create(
                    task=task,
                    news_id=article_id,
                    results=article_results,
                    is_success=all(r.get("success", False) for r in article_results.values()),
                )

            # 更新任务状态
            task.status = "completed"
            task.completed_at = timezone.now()
            task.total_articles = len(news_articles)
            task.processed_articles = len(results)
            task.success_articles = sum(
                1 for r in results.values() if all(ar.get("success", False) for ar in r.values())
            )
            task.save()

        return {"task_id": task_id, "status": "completed", "total": len(news_articles), "processed": len(results)}

    except Exception as e:
        logger.error(f"批量分析任务 {task_id} 失败: {str(e)}", exc_info=True)

        # 更新任务状态为失败
        task.status = "failed"
        task.error_message = str(e)
        task.completed_at = timezone.now()
        task.save()

        return {"task_id": task_id, "status": "failed", "error": str(e)}


@shared_task
def cleanup_old_analysis_results():
    """
    清理旧的分析结果
    """
    try:
        # 清理30天前的批量分析结果
        threshold = timezone.now() - timezone.timedelta(days=30)
        BatchAnalysisResult.objects.filter(task__completed_at__lt=threshold, task__status="completed").delete()

        # 清理过期的分析缓存
        ai_service = AIService()
        ai_service.clean_expired_cache()

        return {"status": "success", "message": "清理完成"}

    except Exception as e:
        logger.error(f"清理旧分析结果失败: {str(e)}", exc_info=True)
        return {"status": "failed", "error": str(e)}


@shared_task
def process_schedule_execution(execution_id):
    """
    处理调度任务执行
    """
    try:
        # 获取执行记录
        execution = ScheduleExecution.objects.select_related("schedule").get(id=execution_id)
        schedule = execution.schedule

        # 更新执行状态
        execution.status = "processing"
        execution.save()

        # 获取需要分析的新闻
        from datetime import timedelta

        from django.utils import timezone

        # 计算时间范围
        end_time = timezone.now()
        start_time = end_time - timedelta(minutes=schedule.time_window)

        # 构建查询条件
        query = Q(created_at__range=(start_time, end_time))
        if schedule.categories:
            query &= Q(category_id__in=schedule.categories)

        news_articles = NewsArticle.objects.filter(query)

        # 创建AI服务实例
        ai_service = AIService()

        # 运行异步分析
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # 执行标准分析
            if schedule.analysis_types:
                results = loop.run_until_complete(
                    ai_service.batch_analyze(list(news_articles), analysis_types=schedule.analysis_types)
                )

            # 执行规则分析
            if schedule.rules.exists():
                rule_results = loop.run_until_complete(
                    ai_service.batch_analyze_with_rules(
                        list(news_articles), rules=schedule.rules.filter(is_active=True)
                    )
                )

                # 合并结果
                if schedule.analysis_types:
                    for article_id in results:
                        if article_id in rule_results:
                            results[article_id].update(rule_results[article_id])
                else:
                    results = rule_results

        finally:
            loop.close()

        # 更新执行记录
        execution.status = "success"
        execution.completed_at = timezone.now()
        execution.total_articles = len(news_articles)
        execution.processed_articles = len(results)
        execution.success_articles = sum(
            1 for r in results.values() if all(ar.get("success", False) for ar in r.values())
        )
        execution.save()

        # 更新调度信息
        schedule.last_run = execution.completed_at
        schedule.next_run = schedule.calculate_next_run()
        schedule.save()

        return {
            "execution_id": execution_id,
            "status": "success",
            "total": len(news_articles),
            "processed": len(results),
        }

    except Exception as e:
        logger.error(f"调度任务执行 {execution_id} 失败: {str(e)}", exc_info=True)

        try:
            # 更新执行记录为失败
            execution.status = "failed"
            execution.error_message = str(e)
            execution.completed_at = timezone.now()
            execution.save()

            # 更新调度信息
            schedule = execution.schedule
            schedule.last_run = execution.completed_at
            schedule.next_run = schedule.calculate_next_run()
            schedule.save()
        except Exception as inner_e:
            logger.error(f"更新执行记录失败: {str(inner_e)}", exc_info=True)

        return {"execution_id": execution_id, "status": "failed", "error": str(e)}


@shared_task
def check_and_execute_schedules():
    """
    检查并执行到期的调度任务
    """
    try:
        # 获取所有启用且到期的调度
        now = timezone.now()
        schedules = AnalysisSchedule.objects.filter(is_active=True, next_run__lte=now)

        for schedule in schedules:
            try:
                # 创建执行记录
                execution = ScheduleExecution.objects.create(schedule=schedule, status=ScheduleExecution.Status.PENDING)

                # 异步执行任务
                process_schedule_execution.delay(execution.id)

            except Exception as e:
                logger.error(f"创建调度任务执行失败: {str(e)}", exc_info=True)

        return {"status": "success", "scheduled": len(schedules)}

    except Exception as e:
        logger.error(f"检查调度任务失败: {str(e)}", exc_info=True)
        return {"status": "failed", "error": str(e)}
