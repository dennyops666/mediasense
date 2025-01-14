from django.db import models
from django.utils import timezone


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
    last_run_time = models.DateTimeField("上次运行时间", null=True, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "爬虫配置"
        verbose_name_plural = verbose_name
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["status", "-updated_at"]),
        ]

    def __str__(self):
        return self.name


class CrawlerTask(models.Model):
    """
    爬虫任务模型
    """

    config = models.ForeignKey(CrawlerConfig, verbose_name="爬虫配置", on_delete=models.CASCADE)
    task_id = models.CharField("任务ID", max_length=100, unique=True)
    status = models.IntegerField(
        "状态",
        choices=(
            (0, "未开始"),
            (1, "运行中"),
            (2, "已完成"),
            (3, "已停止"),
            (4, "出错"),
        ),
        default=0,
    )
    start_time = models.DateTimeField("开始时间", null=True, blank=True)
    end_time = models.DateTimeField("结束时间", null=True, blank=True)
    result = models.JSONField("执行结果", default=dict)
    error_message = models.TextField("错误信息", blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "爬虫任务"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["config", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.config.name}-{self.task_id}"


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
