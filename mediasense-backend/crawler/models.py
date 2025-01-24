from django.db import models
from django.utils import timezone
import uuid


class CrawlerConfig(models.Model):
    """
    爬虫配置模型
    """

    name = models.CharField("配置名称", max_length=100)
    description = models.TextField("配置描述", blank=True)
    source_url = models.URLField("数据源URL", max_length=500)
    crawler_type = models.IntegerField(
        "爬虫类型",
        choices=(
            (1, "RSS"),
            (2, "API"),
            (3, "网页"),
        ),
    )
    config_data = models.JSONField("配置数据", default=dict)
    headers = models.JSONField("请求头", default=dict)
    interval = models.IntegerField("抓取间隔(分钟)", default=60)
    status = models.IntegerField(
        "状态",
        choices=(
            (0, "禁用"),
            (1, "启用"),
        ),
        default=0,
    )
    is_active = models.BooleanField("是否激活", default=False)
    last_run_time = models.DateTimeField("上次运行时间", null=True, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "爬虫配置"
        verbose_name_plural = verbose_name
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["status", "-updated_at"]),
            models.Index(fields=["is_active", "-updated_at"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # 同步status和is_active状态
        if self.status == 1:
            self.is_active = True
        else:
            self.is_active = False
        super().save(*args, **kwargs)


class CrawlerTask(models.Model):
    """
    爬虫任务模型
    """

    class Status(models.IntegerChoices):
        PENDING = 0, '未开始'
        RUNNING = 1, '运行中'
        COMPLETED = 2, '已完成'
        CANCELLED = 3, '已取消'
        ERROR = 4, '出错'

    config = models.ForeignKey(CrawlerConfig, on_delete=models.CASCADE, verbose_name='爬虫配置')
    task_id = models.CharField(max_length=36, unique=True, verbose_name='任务ID', default=uuid.uuid4)
    status = models.IntegerField(choices=Status.choices, default=Status.PENDING, verbose_name='状态')
    start_time = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='结束时间')
    result = models.JSONField(null=True, blank=True, verbose_name='执行结果')
    error_message = models.TextField(null=True, blank=True, verbose_name='错误信息')
    retry_count = models.IntegerField(default=0, verbose_name='重试次数')
    is_test = models.BooleanField(default=False, verbose_name='是否测试任务')
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "爬虫任务"
        verbose_name_plural = verbose_name
        ordering = ["-start_time"]
        indexes = [
            models.Index(fields=["config", "-start_time"]),
            models.Index(fields=["status", "-start_time"]),
            models.Index(fields=["is_test", "-start_time"]),
        ]

    def __str__(self):
        return f"{self.config.name} - {self.task_id}"

    def start(self):
        """开始任务"""
        self.status = self.Status.RUNNING
        self.start_time = timezone.now()
        self.save()

    def complete(self, result=None):
        """完成任务"""
        self.status = self.Status.COMPLETED
        self.end_time = timezone.now()
        if result:
            self.result = result
        self.save()

    def fail(self, error_message):
        """任务失败"""
        self.status = self.Status.ERROR
        self.end_time = timezone.now()
        self.error_message = error_message
        self.save()

    def cancel(self):
        """取消任务"""
        self.status = self.Status.CANCELLED
        self.end_time = timezone.now()
        self.save()


class ProxyPool(models.Model):
    """代理池模型"""

    STATUS_CHOICES = ((0, "未验证"), (1, "可用"), (2, "不可用"))

    ip = models.CharField("IP地址", max_length=64)
    port = models.IntegerField("端口号")
    protocol = models.CharField("协议", max_length=10, choices=(("http", "HTTP"), ("https", "HTTPS")))
    location = models.CharField("地理位置", max_length=100, blank=True)
    speed = models.IntegerField("响应速度(ms)", default=0)
    success_rate = models.FloatField("成功率", default=0.0)
    status = models.IntegerField("状态", choices=STATUS_CHOICES, default=0)
    last_check_time = models.DateTimeField("最后检查时间", null=True, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "代理池"
        verbose_name_plural = verbose_name
        db_table = "crawler_proxy_pool"
        ordering = ["-success_rate", "speed"]
        indexes = [models.Index(fields=["status", "protocol"]), models.Index(fields=["success_rate", "speed"])]

    def __str__(self):
        return f"{self.protocol}://{self.ip}:{self.port}"

    @property
    def proxy_url(self):
        """获取代理URL"""
        return f"{self.protocol}://{self.ip}:{self.port}"

    def check_availability(self, timeout=10):
        """检查代理可用性"""
        import requests

        try:
            start_time = timezone.now()
            response = requests.get("https://www.baidu.com", proxies={self.protocol: self.proxy_url}, timeout=timeout)
            response.raise_for_status()

            # 更新状态
            self.speed = int((timezone.now() - start_time).total_seconds() * 1000)
            self.success_rate = (self.success_rate * 5 + 100) / 6  # 加权计算成功率
            self.status = 1

        except Exception:
            self.success_rate = (self.success_rate * 5) / 6  # 降低成功率
            self.status = 2

        self.last_check_time = timezone.now()
        self.save()

        return self.status == 1


class NewsArticle(models.Model):
    """新闻文章模型"""

    title = models.CharField("标题", max_length=500)
    description = models.TextField("描述", blank=True)
    content = models.TextField("内容", blank=True)
    url = models.URLField("链接", max_length=255, unique=True)
    source = models.CharField("来源", max_length=100)
    author = models.CharField("作者", max_length=100, blank=True)
    pub_time = models.DateTimeField("发布时间")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "新闻文章"
        verbose_name_plural = verbose_name
        ordering = ["-pub_time"]
        indexes = [
            models.Index(fields=["-pub_time"], name="news_article_pub_time_idx"),
            models.Index(fields=["source", "-pub_time"], name="news_article_source_idx"),
        ]

    def __str__(self):
        return self.title
