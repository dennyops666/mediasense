#!/usr/bin/env python3
import os
import django
import pytz
from datetime import datetime, timedelta

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediasense.settings')
django.setup()

from crawler.models import CrawlerTask, NewsArticle

def fix_time_records():
    # 计算时间差（从2025年调整到2024年）
    time_diff = timedelta(days=365)  # 减少一年
    
    try:
        # 修正爬虫任务的时间记录
        print("开始修正爬虫任务时间记录...")
        tasks = CrawlerTask.objects.all()
        task_count = 0
        for task in tasks:
            try:
                if task.start_time:
                    task.start_time -= time_diff
                if task.end_time:
                    task.end_time -= time_diff
                if task.created_at:
                    task.created_at -= time_diff
                if task.updated_at:
                    task.updated_at -= time_diff
                task.save()
                task_count += 1
            except Exception as e:
                print(f"修正任务记录失败 (ID: {task.id}): {str(e)}")
        print(f"完成修正 {task_count} 条爬虫任务记录")
        
        # 修正新闻文章的时间记录
        print("\n开始修正新闻文章时间记录...")
        articles = NewsArticle.objects.all()
        article_count = 0
        for article in articles:
            try:
                if article.pub_time:
                    article.pub_time -= time_diff
                if article.created_at:
                    article.created_at -= time_diff
                if article.updated_at:
                    article.updated_at -= time_diff
                article.save()
                article_count += 1
            except Exception as e:
                print(f"修正文章记录失败 (ID: {article.id}): {str(e)}")
        print(f"完成修正 {article_count} 条新闻文章记录")
        
    except Exception as e:
        print(f"执行过程中发生错误: {str(e)}")

if __name__ == '__main__':
    print("开始时间修正...")
    fix_time_records()
    print("时间修正完成！") 