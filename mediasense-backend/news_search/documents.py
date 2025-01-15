from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from news.models import NewsArticle


@registry.register_document
class NewsArticleDocument(Document):
    """新闻文章的 ElasticSearch 文档"""

    # 分类信息
    category = fields.ObjectField(
        properties={
            "id": fields.IntegerField(),
            "name": fields.KeywordField(),
        }
    )

    # 标签使用关键字字段，便于精确匹配和聚合
    tags = fields.KeywordField(multi=True)

    # 审核信息
    reviewer = fields.ObjectField(
        properties={
            "id": fields.IntegerField(),
            "username": fields.KeywordField(),
        }
    )

    # 使用自定义分析器的文本字段
    title_suggest = fields.CompletionField(
        analyzer='standard',
        search_analyzer='standard',
        preserve_separators=True,
        preserve_position_increments=True,
        max_input_length=50
    )  # 用于搜索建议
    content_analyzed = fields.TextField(analyzer='html_strip')  # 用于全文搜索

    class Index:
        name = "news_articles"
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "analyzer": {
                    "html_strip": {
                        "tokenizer": "standard",
                        "filter": ["lowercase", "stop", "snowball"],
                        "char_filter": ["html_strip"],
                    }
                }
            },
        }

    class Django:
        model = NewsArticle
        fields = [
            "id",
            "title",
            "content",
            "summary",
            "source",
            "author",
            "url",
            "status",
            "sentiment_score",
            "publish_time",
            "created_at",
            "updated_at",
        ]

    def prepare_category(self, instance):
        """准备分类数据"""
        if instance.category:
            return {
                "id": instance.category.id,
                "name": instance.category.name,
            }
        return None

    def prepare_reviewer(self, instance):
        """准备审核人数据"""
        if instance.reviewer:
            return {
                "id": instance.reviewer.id,
                "username": instance.reviewer.username,
            }
        return None

    def prepare_title_suggest(self, instance):
        """
        准备标题建议数据
        :param instance: NewsArticle实例
        :return: 标题建议数据,包含输入和权重
        """
        inputs = [instance.title]
        if instance.tags:
            inputs.extend(instance.tags)
        
        # 根据状态设置权重,已发布的文章权重更高
        weight = 100 if instance.status == 'published' else 50
        
        return {
            'input': inputs,
            'weight': weight
        }
