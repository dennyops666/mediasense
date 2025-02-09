from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from django.conf import settings
from news.models import NewsArticle


@registry.register_document
class NewsArticleDocument(Document):
    """新闻文章文档"""

    title = fields.TextField(
        fields={
            'raw': fields.KeywordField(),
            'suggest': fields.CompletionField(),
        }
    )
    content = fields.TextField()
    summary = fields.TextField()
    source = fields.KeywordField()
    author = fields.KeywordField()
    url = fields.KeywordField()
    status = fields.KeywordField()
    sentiment_score = fields.FloatField()
    publish_time = fields.DateField()
    created_at = fields.DateField()
    updated_at = fields.DateField()

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
    content_analyzed = fields.TextField(analyzer='html_strip')  # 用于全文搜索

    class Index:
        name = 'news_articles'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
            'analysis': {
                'analyzer': {
                    'html_strip': {
                        'tokenizer': 'standard',
                        'filter': ['lowercase', 'stop', 'snowball'],
                        'char_filter': ['html_strip']
                    }
                }
            }
        }

    class Django:
        model = NewsArticle
        fields = [
            'id',
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
        weight = 10 if instance.status == NewsArticle.Status.PUBLISHED else 5
        
        return {
            'input': inputs,
            'weight': weight
        }
