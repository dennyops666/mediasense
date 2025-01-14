from rest_framework import serializers

from news.models import NewsArticle

from .models import SearchSuggestion


class NewsSearchSerializer(serializers.ModelSerializer):
    """
    新闻搜索结果序列化器
    """

    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = NewsArticle
        fields = [
            "id",
            "title",
            "summary",
            "source",
            "category_name",
            "author",
            "publish_time",
            "keywords",
            "sentiment_score",
        ]


class SearchSuggestionSerializer(serializers.ModelSerializer):
    """
    搜索建议序列化器
    """

    class Meta:
        model = SearchSuggestion
        fields = ["id", "keyword", "search_count", "is_hot", "updated_at"]
        read_only_fields = ["search_count", "is_hot", "updated_at"]


class TimeRangeSerializer(serializers.Serializer):
    """时间范围序列化器"""

    start = serializers.DateField(required=False)
    end = serializers.DateField(required=False)


class SentimentRangeSerializer(serializers.Serializer):
    """情感得分范围序列化器"""

    min = serializers.FloatField(required=False, min_value=-1, max_value=1)
    max = serializers.FloatField(required=False, min_value=-1, max_value=1)


class SearchQuerySerializer(serializers.Serializer):
    """搜索查询序列化器"""

    query = serializers.CharField(required=True, max_length=100)
    category = serializers.IntegerField(required=False)
    status = serializers.CharField(required=False)
    source = serializers.CharField(required=False, max_length=100)
    author = serializers.CharField(required=False, max_length=100)
    time_range = TimeRangeSerializer(required=False)
    sentiment = SentimentRangeSerializer(required=False)
    tags = serializers.ListField(child=serializers.CharField(max_length=50), required=False)
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    size = serializers.IntegerField(required=False, min_value=1, max_value=50, default=10)

    def validate_time_range(self, value):
        """验证时间范围"""
        if value and "start" in value and "end" in value:
            if value["start"] > value["end"]:
                raise serializers.ValidationError("开始时间不能大于结束时间")
        return value

    def validate_sentiment(self, value):
        """验证情感得分范围"""
        if value and "min" in value and "max" in value:
            if value["min"] > value["max"]:
                raise serializers.ValidationError("最小值不能大于最大值")
        return value


class SearchResultSerializer(serializers.Serializer):
    """搜索结果序列化器"""

    id = serializers.IntegerField()
    title = serializers.CharField()
    summary = serializers.CharField()
    url = serializers.URLField()
    publish_time = serializers.DateTimeField()
    score = serializers.FloatField()
    source = serializers.CharField()
    author = serializers.CharField()
    tags = serializers.ListField(child=serializers.CharField())
    sentiment_score = serializers.FloatField()
    title_highlight = serializers.CharField(required=False)
    summary_highlight = serializers.CharField(required=False)
    content_highlight = serializers.CharField(required=False)


class SearchResponseSerializer(serializers.Serializer):
    """搜索响应序列化器"""

    total = serializers.IntegerField()
    results = SearchResultSerializer(many=True)


class SuggestQuerySerializer(serializers.Serializer):
    """搜索建议查询序列化器"""

    prefix = serializers.CharField(required=True, max_length=50)
    size = serializers.IntegerField(required=False, min_value=1, max_value=20, default=5)


class SuggestResultSerializer(serializers.Serializer):
    """搜索建议结果序列化器"""

    id = serializers.IntegerField()
    title = serializers.CharField()
    score = serializers.FloatField()


class HotArticleQuerySerializer(serializers.Serializer):
    """热点文章查询序列化器"""

    days = serializers.IntegerField(required=False, min_value=1, max_value=30, default=7)
    size = serializers.IntegerField(required=False, min_value=1, max_value=50, default=10)


class HotArticleSerializer(serializers.Serializer):
    """热点文章序列化器"""

    id = serializers.IntegerField()
    title = serializers.CharField()
    summary = serializers.CharField()
    url = serializers.URLField()
    publish_time = serializers.DateTimeField()
    sentiment_score = serializers.FloatField()
