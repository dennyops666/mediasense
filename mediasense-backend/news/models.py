from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class NewsCategory(models.Model):
    """新闻分类模型"""

    name = models.CharField(_("分类名称"), max_length=100, unique=True)
    description = models.TextField(_("分类描述"), blank=True)
    parent = models.ForeignKey(
        "self", verbose_name=_("父分类"), on_delete=models.SET_NULL, null=True, blank=True, related_name="children"
    )
    level = models.IntegerField(_("分类层级"), default=1)
    sort_order = models.IntegerField(_("排序"), default=0)
    is_active = models.IntegerField(_("是否启用"), default=1)
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)

    class Meta:
        verbose_name = _("新闻分类")
        verbose_name_plural = _("新闻分类")
        db_table = "news_category"
        ordering = ["sort_order", "id"]
        indexes = [
            models.Index(fields=["parent_id"]),
            models.Index(fields=["level"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """重写save方法，自动计算分类层级"""
        if self.parent:
            self.level = self.parent.level + 1
        else:
            self.level = 1
        super().save(*args, **kwargs)


class NewsArticle(models.Model):
    """新闻文章模型"""

    class Status(models.TextChoices):
        DRAFT = "draft", _("草稿")
        PENDING = "pending", _("待审核")
        PUBLISHED = "published", _("已发布")
        REJECTED = "rejected", _("已拒绝")
        ARCHIVED = "archived", _("已归档")

    title = models.CharField(_("标题"), max_length=255)
    content = models.TextField(_("正文内容"))
    summary = models.TextField(_("摘要"), blank=True)
    source = models.CharField(_("来源"), max_length=100, blank=True)
    author = models.CharField(_("作者"), max_length=100, blank=True)
    source_url = models.CharField(_("原文链接"), max_length=255, unique=True)
    category = models.ForeignKey(
        NewsCategory, verbose_name=_("所属分类"), on_delete=models.SET_NULL, null=True, related_name="articles"
    )
    tags = models.JSONField(_("标签"), default=list)
    status = models.CharField(_("状态"), max_length=20, choices=Status.choices, default=Status.DRAFT)
    sentiment_score = models.FloatField(_("情感得分"), default=0.0)
    publish_time = models.DateTimeField(_("发布时间"), null=True, blank=True)
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)

    # 统计字段
    read_count = models.PositiveIntegerField(_("阅读数"), default=0)
    like_count = models.PositiveIntegerField(_("点赞数"), default=0)
    comment_count = models.PositiveIntegerField(_("评论数"), default=0)

    # 审核相关字段
    reviewer = models.ForeignKey(
        User,
        verbose_name=_("审核人"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_articles",
    )
    review_time = models.DateTimeField(_("审核时间"), null=True, blank=True)
    review_comment = models.TextField(_("审核意见"), blank=True)

    # 创建者
    created_by = models.ForeignKey(
        User,
        verbose_name=_("创建者"),
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_articles",
    )

    class Meta:
        verbose_name = _("新闻文章")
        verbose_name_plural = _("新闻文章")
        db_table = "news_article"
        ordering = ["-publish_time", "-id"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["category"]),
            models.Index(fields=["publish_time"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["read_count"]),
            models.Index(fields=["like_count"]),
            models.Index(fields=["comment_count"]),
        ]

    def __str__(self):
        return self.title

    @property
    def is_published(self):
        """是否已发布"""
        return self.status == self.Status.PUBLISHED

    def publish(self, reviewer=None):
        """发布文章"""
        from django.utils import timezone

        self.status = self.Status.PUBLISHED
        self.reviewer = reviewer
        self.review_time = timezone.now()
        self.save()


class NewsAuditLog(models.Model):
    """新闻审核日志"""

    class Action(models.TextChoices):
        SUBMIT = "submit", _("提交审核")
        ASSIGN = "assign", _("分配审核")
        APPROVE = "approve", _("审核通过")
        REJECT = "reject", _("审核拒绝")
        WITHDRAW = "withdraw", _("撤回审核")

    article = models.ForeignKey(
        "NewsArticle", verbose_name=_("新闻文章"), on_delete=models.CASCADE, related_name="audit_logs"
    )
    action = models.CharField(_("审核动作"), max_length=20, choices=Action.choices)
    from_status = models.CharField(_("原状态"), max_length=20, choices=NewsArticle.Status.choices)
    to_status = models.CharField(_("新状态"), max_length=20, choices=NewsArticle.Status.choices)
    operator = models.ForeignKey(
        User, verbose_name=_("操作人"), on_delete=models.SET_NULL, null=True, related_name="audit_operations"
    )
    comment = models.TextField(_("审核意见"), blank=True)
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)

    class Meta:
        verbose_name = _("审核日志")
        verbose_name_plural = _("审核日志")
        db_table = "news_audit_log"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["article", "action"]),
            models.Index(fields=["operator", "created_at"]),
        ]

    def __str__(self):
        return f"{self.article.title} - {self.get_action_display()}"
