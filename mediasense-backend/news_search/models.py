from django.db import models


class SearchSuggestion(models.Model):
    """
    搜索建议模型
    """

    keyword = models.CharField("关键词", max_length=100, unique=True)
    search_count = models.IntegerField("搜索次数", default=0)
    is_hot = models.BooleanField("是否热门", default=False)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "搜索建议"
        verbose_name_plural = verbose_name
        ordering = ["-search_count", "-updated_at"]
        indexes = [
            models.Index(fields=["-search_count"]),
            models.Index(fields=["keyword"]),
        ]

    def __str__(self):
        return self.keyword
