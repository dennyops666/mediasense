"""新闻管理模块序列化器."""

from django.db import transaction
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Prefetch

from rest_framework import serializers

from .models import (
    NewsArticle,
    NewsAuditLog,
    NewsCategory,
)


class NewsCategorySerializer(serializers.ModelSerializer):
    """新闻分类序列化器."""

    children = serializers.SerializerMethodField()
    article_count = serializers.IntegerField(read_only=True)

    class Meta:
        """元数据类."""

        model = NewsCategory
        fields = [
            'id',
            'name',
            'parent',
            'level',
            'sort_order',
            'is_active',
            'article_count',
            'children',
            'created_at',
            'updated_at',
            'creator',
            'updater',
        ]
        read_only_fields = ['level', 'article_count', 'created_at', 'updated_at', 'creator', 'updater']

    def get_children(self, obj):
        """获取子分类列表."""
        # 使用缓存存储子分类
        cache_key = f'category_children_{obj.id}'
        children = cache.get(cache_key)
        
        if children is None:
            queryset = obj.children.filter(is_active=True).prefetch_related(
                Prefetch(
                    'articles',
                    queryset=NewsArticle.objects.filter(status=NewsArticle.Status.PUBLISHED),
                    to_attr='published_articles'
                )
            ).order_by('sort_order')
            
            serializer = self.__class__(queryset, many=True, context=self.context)
            children = serializer.data
            
            # 缓存结果，设置合理的过期时间
            cache.set(cache_key, children, timeout=3600)  # 1小时过期
            
        return children

    def validate(self, data):
        """验证分类数据."""
        # 验证父分类
        parent = data.get('parent')
        if parent:
            # 检查父分类是否存在且有效
            if not parent.is_active:
                raise serializers.ValidationError('父分类已禁用')
            
            # 检查是否形成循环引用
            current = parent
            visited = {current.id}
            while current.parent:
                if current.parent.id in visited:
                    raise serializers.ValidationError('不能形成循环引用')
                if current.parent.id == self.instance.id if self.instance else None:
                    raise serializers.ValidationError('不能将当前分类的子分类设为父分类')
                visited.add(current.parent.id)
                current = current.parent
                
            # 检查分类层级
            if parent.level >= 2:  # 最多支持三级分类
                raise serializers.ValidationError('分类层级最多支持三级')
                
        return data

    def create(self, validated_data):
        """创建分类时更新缓存."""
        instance = super().create(validated_data)
        if instance.parent:
            cache.delete(f'category_children_{instance.parent.id}')
        return instance

    def update(self, instance, validated_data):
        """更新分类时更新缓存."""
        old_parent = instance.parent
        new_instance = super().update(instance, validated_data)
        
        # 如果父分类发生变化，需要更新两个父分类的缓存
        if old_parent:
            cache.delete(f'category_children_{old_parent.id}')
        if new_instance.parent and new_instance.parent != old_parent:
            cache.delete(f'category_children_{new_instance.parent.id}')
            
        return new_instance


class NewsArticleSerializer(serializers.ModelSerializer):
    """新闻文章序列化器."""

    category_name = serializers.CharField(source='category.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    reviewer_name = serializers.CharField(source='reviewer.username', read_only=True)

    class Meta:
        """元数据类."""

        model = NewsArticle
        fields = [
            'id',
            'title',
            'content',
            'category',
            'category_name',
            'source',
            'author',
            'url',
            'publish_time',
            'tags',
            'status',
            'status_display',
            'reviewer',
            'reviewer_name',
            'review_time',
            'review_comment',
            'created_at',
            'updated_at',
            'creator',
            'updater',
        ]
        read_only_fields = [
            'status',
            'status_display',
            'reviewer',
            'reviewer_name',
            'review_time',
            'review_comment',
            'created_at',
            'updated_at',
            'creator',
            'updater',
        ]

    def validate_category(self, value):
        """验证新闻分类."""
        if not value.is_active:
            raise serializers.ValidationError('所选分类已禁用')
        return value

    def validate_url(self, value):
        """验证URL唯一性."""
        if NewsArticle.objects.filter(url=value).exists():
            raise serializers.ValidationError('该URL已存在')
        return value

    def validate(self, attrs):
        """验证文章数据."""
        # 设置默认值
        attrs.setdefault('publish_time', timezone.now())
        attrs.setdefault('status', NewsArticle.Status.DRAFT)

        # 验证发布时间
        if attrs['publish_time'] > timezone.now():
            raise serializers.ValidationError({'publish_time': '发布时间不能晚于当前时间'})

        return attrs


class NewsArticleCreateSerializer(NewsArticleSerializer):
    """新闻文章创建序列化器."""

    class Meta(NewsArticleSerializer.Meta):
        """元数据类."""

        read_only_fields = NewsArticleSerializer.Meta.read_only_fields + ['status']

    def create(self, validated_data):
        """创建文章时默认为草稿状态."""
        validated_data['status'] = NewsArticle.Status.DRAFT
        return super().create(validated_data)


class NewsArticleUpdateSerializer(NewsArticleSerializer):
    """新闻文章更新序列化器."""

    def validate_status(self, value):
        """验证状态变更."""
        if not self.instance:
            return value

        # 已发布的文章只能变为已归档
        if self.instance.status == NewsArticle.Status.PUBLISHED:
            if value != NewsArticle.Status.ARCHIVED:
                raise serializers.ValidationError('已发布的文章只能变更为已归档状态')

        # 已归档的文章不能再变更状态
        if self.instance.status == NewsArticle.Status.ARCHIVED:
            raise serializers.ValidationError('已归档的文章不能变更状态')

        return value


class NewsArticleReviewSerializer(serializers.ModelSerializer):
    """新闻文章审核序列化器."""

    class Meta:
        """元数据类."""

        model = NewsArticle
        fields = [
            'id',
            'title',
            'content',
            'category',
            'source',
            'url',
            'author',
            'publish_time',
            'tags',
            'status',
            'reviewer',
            'review_time',
            'review_comment',
        ]
        read_only_fields = [
            'id',
            'title',
            'content',
            'category',
            'source',
            'url',
            'author',
            'publish_time',
            'tags',
        ]

    def _validate_review_status(self, article, action, attrs):
        """验证审核状态."""
        if action == 'submit':
            if article.status != NewsArticle.Status.DRAFT:
                raise serializers.ValidationError('只有草稿状态的文章可以提交审核')
        elif action == 'assign':
            if article.status != NewsArticle.Status.PENDING:
                raise serializers.ValidationError('只有待审核状态的文章可以分配审核人')
            if not attrs.get('reviewer'):
                raise serializers.ValidationError('必须指定审核人')
        elif action in ['approve', 'reject']:
            if article.status != NewsArticle.Status.PENDING:
                raise serializers.ValidationError('只有待审核状态的文章可以进行审核')
            if not attrs.get('review_comment'):
                raise serializers.ValidationError('必须填写审核意见')
        elif action == 'withdraw':
            if article.status != NewsArticle.Status.PENDING:
                raise serializers.ValidationError('只有待审核状态的文章可以撤回')
        else:
            raise serializers.ValidationError('无效的审核动作')

    def validate(self, attrs):
        """验证审核数据."""
        action = self.context.get('action')
        if not action:
            raise serializers.ValidationError('未指定审核动作')

        article = self.instance
        if not article:
            raise serializers.ValidationError('文章不存在')

        self._validate_review_status(article, action, attrs)
        return attrs

    @transaction.atomic
    def update(self, instance, validated_data):
        """更新审核信息."""
        validated_data['reviewer'] = self.context['request'].user
        validated_data['review_time'] = timezone.now()

        # 如果审核通过，设置发布时间
        if validated_data['status'] == NewsArticle.Status.PUBLISHED:
            validated_data['publish_time'] = timezone.now()

        # 创建审核日志
        NewsAuditLog.objects.create(
            article=instance,
            action=self.context['action'],
            operator=self.context['request'].user,
            comment=validated_data.get('review_comment', '')
        )

        return super().update(instance, validated_data)


class NewsArticleExportSerializer(NewsArticleSerializer):
    """新闻文章导出序列化器."""

    category_name = serializers.CharField(source='category.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    reviewer_name = serializers.CharField(source='reviewer.username', read_only=True)

    class Meta:
        """元数据类."""

        model = NewsArticle
        fields = [
            'id',
            'title',
            'content',
            'category',
            'category_name',
            'source',
            'url',
            'author',
            'publish_time',
            'tags',
            'status',
            'status_display',
            'reviewer',
            'reviewer_name',
            'review_time',
            'review_comment',
            'created_at',
            'updated_at',
            'creator',
            'updater',
        ]
        read_only_fields = fields


class NewsArticleImportSerializer(serializers.ModelSerializer):
    """新闻文章导入序列化器."""

    class Meta:
        """元数据类."""

        model = NewsArticle
        fields = [
            'title',
            'content',
            'category',
            'source',
            'url',
            'author',
            'publish_time',
            'tags',
        ]

    def validate_category(self, value):
        """验证新闻分类."""
        try:
            category = NewsCategory.objects.get(name=value, is_active=True)
            return category
        except NewsCategory.DoesNotExist:
            raise serializers.ValidationError('所选分类不存在或已禁用')

    @transaction.atomic
    def create(self, validated_data):
        """批量创建文章."""
        if isinstance(validated_data, list):
            articles = []
            for article_data in validated_data:
                article = NewsArticle(**article_data)
                articles.append(article)
            return NewsArticle.objects.bulk_create(articles)
        return super().create(validated_data)


class ImportResultSerializer(serializers.Serializer):
    """导入结果序列化器."""

    total = serializers.IntegerField()
    success = serializers.IntegerField()
    failed = serializers.IntegerField()
    errors = serializers.ListField(child=serializers.CharField())


class NewsAuditLogSerializer(serializers.ModelSerializer):
    """新闻审核日志序列化器."""

    operator_name = serializers.CharField(source='operator.username', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        """元数据类."""

        model = NewsAuditLog
        fields = [
            'id',
            'article',
            'action',
            'action_display',
            'operator',
            'operator_name',
            'comment',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'article',
            'action',
            'action_display',
            'operator',
            'operator_name',
            'created_at',
        ]


class NewsArticleAuditSerializer(serializers.ModelSerializer):
    """新闻文章审核序列化器."""

    # 定义状态流转图
    STATE_TRANSITIONS = {
        NewsArticle.Status.DRAFT: {
            'submit': NewsArticle.Status.PENDING,
        },
        NewsArticle.Status.PENDING: {
            'assign': NewsArticle.Status.PENDING,  # 分配审核人不改变状态
            'approve': NewsArticle.Status.PUBLISHED,
            'reject': NewsArticle.Status.REJECTED,
            'withdraw': NewsArticle.Status.DRAFT,
        },
        NewsArticle.Status.REJECTED: {
            'revise': NewsArticle.Status.DRAFT,
        },
        NewsArticle.Status.PUBLISHED: {
            'archive': NewsArticle.Status.ARCHIVED,
        }
    }

    # 定义需要审核意见的动作
    ACTIONS_REQUIRE_COMMENT = ['reject', 'revise']
    
    # 定义需要审核人的动作
    ACTIONS_REQUIRE_REVIEWER = ['assign', 'approve', 'reject']

    class Meta:
        """元数据类."""

        model = NewsArticle
        fields = [
            'id',
            'title',
            'content',
            'category',
            'source',
            'url',
            'author',
            'publish_time',
            'tags',
            'status',
            'reviewer',
            'review_time',
            'review_comment',
        ]
        read_only_fields = [
            'id',
            'title',
            'content',
            'category',
            'source',
            'url',
            'author',
            'publish_time',
            'tags',
        ]

    def validate_action(self, action, instance, attrs):
        """验证审核动作."""
        current_status = instance.status
        
        # 检查当前状态是否允许该动作
        if current_status not in self.STATE_TRANSITIONS:
            raise serializers.ValidationError(f'当前状态({current_status})不支持任何审核动作')
            
        allowed_actions = self.STATE_TRANSITIONS[current_status].keys()
        if action not in allowed_actions:
            raise serializers.ValidationError(f'当前状态({current_status})不支持{action}动作')
        
        # 检查是否需要审核意见
        if action in self.ACTIONS_REQUIRE_COMMENT and not attrs.get('review_comment'):
            raise serializers.ValidationError(f'{action}动作必须填写审核意见')
            
        # 检查是否需要审核人
        if action in self.ACTIONS_REQUIRE_REVIEWER and not attrs.get('reviewer'):
            raise serializers.ValidationError(f'{action}动作必须指定审核人')
            
        # 特殊规则检查
        user = self.context['request'].user
        if action in ['approve', 'reject']:
            # 检查审核权限
            if not user.has_perm('news.review_article'):
                raise serializers.ValidationError('您没有审核权限')
            # 检查是否是指定的审核人
            if instance.reviewer and instance.reviewer != user:
                raise serializers.ValidationError('只有指定的审核人才能进行审核')
                
        return True

    def get_next_status(self, current_status, action):
        """获取下一个状态."""
        return self.STATE_TRANSITIONS[current_status].get(action)

    @transaction.atomic
    def update(self, instance, validated_data):
        """更新审核信息."""
        action = self.context['action']
        user = self.context['request'].user
        old_status = instance.status
        
        # 验证审核动作
        self.validate_action(action, instance, validated_data)
        
        # 获取下一个状态
        next_status = self.get_next_status(old_status, action)
        if next_status:
            instance.status = next_status
        
        # 根据动作更新相关字段
        if action == 'submit':
            instance.reviewer = None
            instance.review_time = None
            instance.review_comment = ''
        elif action == 'assign':
            instance.reviewer = validated_data['reviewer']
        elif action in ['approve', 'reject']:
            instance.reviewer = user
            instance.review_time = timezone.now()
            instance.review_comment = validated_data.get('review_comment', '')
            # 如果是发布，设置发布时间
            if action == 'approve':
                instance.publish_time = timezone.now()
        elif action == 'withdraw':
            instance.reviewer = None
            instance.review_time = None
            instance.review_comment = ''
        elif action == 'revise':
            instance.reviewer = None
            instance.review_time = None
            # 保留审核意见供修改参考
        
        # 保存更改
        instance.save()
        
        # 创建审核日志
        self.create_audit_log(
            article=instance,
            action=action,
            from_status=old_status,
            to_status=instance.status,
            operator=user,
            comment=validated_data.get('review_comment', '')
        )
        
        return instance

    def create_audit_log(self, article, action, from_status, to_status, operator, comment=''):
        """创建审核日志."""
        return NewsAuditLog.objects.create(
            article=article,
            action=action,
            from_status=from_status,
            to_status=to_status,
            operator=operator,
            comment=comment
        )


class CategoryTreeSerializer(NewsCategorySerializer):
    """新闻分类树形序列化器."""

    class Meta(NewsCategorySerializer.Meta):
        """元数据类."""

        fields = NewsCategorySerializer.Meta.fields

    @classmethod
    def get_category_tree(cls, queryset=None):
        """获取完整的分类树."""
        cache_key = 'category_tree'
        tree = cache.get(cache_key)
        
        if tree is None:
            if queryset is None:
                queryset = NewsCategory.objects.filter(
                    parent__isnull=True,
                    is_active=True
                ).prefetch_related(
                    Prefetch(
                        'children',
                        queryset=NewsCategory.objects.filter(is_active=True),
                        to_attr='active_children'
                    ),
                    Prefetch(
                        'articles',
                        queryset=NewsArticle.objects.filter(status=NewsArticle.Status.PUBLISHED),
                        to_attr='published_articles'
                    )
                ).order_by('sort_order')
            
            serializer = cls(queryset, many=True)
            tree = serializer.data
            
            # 缓存结果
            cache.set(cache_key, tree, timeout=3600)  # 1小时过期
            
        return tree


class CategoryMoveSerializer(serializers.Serializer):
    """新闻分类移动序列化器."""

    target_parent_id = serializers.IntegerField(required=True, allow_null=True)

    def validate_target_parent_id(self, value):
        """验证目标父分类ID."""
        if value is not None:
            try:
                target_parent = NewsCategory.objects.get(id=value, is_active=True)
                if target_parent.level >= 3:  # 最多支持三级分类
                    raise serializers.ValidationError('分类层级最多支持三级')
                return target_parent
            except NewsCategory.DoesNotExist:
                raise serializers.ValidationError('目标父分类不存在或已禁用')
        return None
