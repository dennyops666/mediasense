import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from news.models import NewsArticle, NewsCategory
from news_search.models import SearchSuggestion, SearchHistory
from elasticsearch_dsl.connections import connections
from django.conf import settings
import elasticsearch
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError
import time
from django.utils import timezone

User = get_user_model()

@pytest.fixture(scope='session')
def es_client():
    """创建Elasticsearch测试客户端"""
    # 重试连接
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            client = Elasticsearch(hosts=settings.ELASTICSEARCH_HOSTS)
            # 创建测试索引
            index_name = f"{settings.ELASTICSEARCH_INDEX_PREFIX}news_articles"
            if not client.indices.exists(index=index_name):
                client.indices.create(
                    index=index_name,
                    body={
                        "mappings": {
                            "properties": {
                                "title": {"type": "text", "analyzer": "standard"},
                                "content": {"type": "text", "analyzer": "standard"},
                                "category": {"type": "keyword"},
                                "source": {"type": "keyword"},
                                "publish_time": {"type": "date"}
                            }
                        },
                        "settings": {
                            "number_of_shards": 1,
                            "number_of_replicas": 0
                        }
                    }
                )
            return client
        except ConnectionError as e:
            if attempt == max_retries - 1:
                pytest.skip(f"Elasticsearch连接失败: {str(e)}")
            time.sleep(retry_delay)
    
    pytest.skip("无法连接到Elasticsearch")

@pytest.fixture(autouse=True)
def setup_es(es_client):
    """设置Elasticsearch连接"""
    try:
        connections.create_connection(hosts=settings.ELASTICSEARCH_HOSTS)
        # 清理测试数据
        index_name = f"{settings.ELASTICSEARCH_INDEX_PREFIX}news_articles"
        if es_client.indices.exists(index=index_name):
            es_client.indices.delete(index=index_name)
            es_client.indices.create(
                index=index_name,
                body={
                    "mappings": {
                        "properties": {
                            "title": {"type": "text", "analyzer": "standard"},
                            "content": {"type": "text", "analyzer": "standard"},
                            "category": {"type": "keyword"},
                            "source": {"type": "keyword"},
                            "publish_time": {"type": "date"}
                        }
                    },
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0
                    }
                }
            )
    except ConnectionError:
        pytest.skip("Elasticsearch服务未启动")
    yield
    try:
        if es_client.indices.exists(index=index_name):
            es_client.indices.delete(index=index_name)
    except:
        pass

@pytest.fixture
def authenticated_client(api_client, test_user):
    login_url = reverse('api:auth:token_obtain')
    login_response = api_client.post(login_url, {
        'username': test_user.username,
        'password': 'testpass123'
    })
    access_token = login_response.data['access']
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    return api_client

@pytest.fixture
def test_user(db):
    user = User.objects.create_user(
        username='testuser',
        password='testpass123',
        email='test@example.com'
    )
    return user

@pytest.fixture
def test_category():
    return NewsCategory.objects.create(
        name='Test Category',
        description='Test category description'
    )

@pytest.fixture
def test_articles(test_category, test_user):
    articles = []
    for i in range(5):
        article = NewsArticle.objects.create(
            title=f'Test Article {i}',
            content=f'Test content {i}',
            summary=f'Test summary {i}',
            source='Test Source',
            author='Test Author',
            source_url=f'http://example.com/article-{i}',
            category=test_category,
            status='published',
            created_by=test_user,
            publish_time=timezone.now()
        )
        articles.append(article)
    return articles

@pytest.fixture
def test_suggestions(db):
    suggestions = []
    for i in range(3):
        suggestion = SearchSuggestion.objects.create(
            keyword=f'测试关键词{i}',
            search_count=10-i,
            is_hot=(i == 0)
        )
        suggestions.append(suggestion)
    return suggestions

@pytest.mark.django_db
class TestSearchAPI:
    """搜索模块API测试"""

    @pytest.fixture
    def test_user(self):
        """创建测试用户"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )

    @pytest.fixture
    def authenticated_client(self, test_user):
        """创建已认证的测试客户端"""
        from rest_framework.test import APIClient
        client = APIClient()
        client.force_authenticate(user=test_user)
        return client

    @pytest.fixture
    def es_client(self):
        """创建Elasticsearch客户端"""
        from elasticsearch import Elasticsearch
        from django.conf import settings
        return Elasticsearch(settings.ELASTICSEARCH_HOSTS)

    @pytest.fixture
    def test_articles(self, test_user):
        """创建测试文章"""
        from news.models import NewsArticle, NewsCategory
        category = NewsCategory.objects.create(name="Test Category")
        articles = []
        for i in range(5):
            article = NewsArticle.objects.create(
                title=f"Test Article {i}",
                content=f"Test content {i}",
                summary=f"Test summary {i}",
                category=category,
                source="Test Source",
                author="Test Author",
                source_url=f"http://example.com/article{i}",
                status="published",
                created_by=test_user
            )
            articles.append(article)
        return articles

    def test_basic_search(self, authenticated_client, test_articles, es_client):
        """测试基础搜索功能"""
        try:
            # 索引测试文章
            index_name = f"{settings.ELASTICSEARCH_INDEX_PREFIX}news_articles"
            for article in test_articles:
                es_client.index(
                    index=index_name,
                    id=article.id,
                    body={
                        'title': article.title,
                        'content': article.content,
                        'summary': article.summary,
                        'category': article.category.id,
                        'source': article.source,
                        'author': article.author,
                        'source_url': article.source_url,
                        'status': article.status,
                        'publish_time': article.publish_time.isoformat() if article.publish_time else None,
                        'created_by': article.created_by.id if article.created_by else None
                    },
                    refresh=True
                )

            # 测试基本搜索
            url = reverse('api:news_search:news-search-search')
            response = authenticated_client.get(url, {'q': 'Test'})
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data['results']) == 5
            assert 'total' in response.data
            assert 'page' in response.data
            assert 'page_size' in response.data
            
            # 测试空搜索
            response = authenticated_client.get(url)
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data['results']) == 5
            
            # 测试无结果搜索
            response = authenticated_client.get(url, {'q': 'NonExistentKeyword'})
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data['results']) == 0
            
        except ConnectionError:
            pytest.skip("Elasticsearch服务未启动")

    def test_advanced_search(self, authenticated_client, test_articles, es_client):
        """测试高级搜索功能"""
        try:
            # 索引测试文章
            index_name = f"{settings.ELASTICSEARCH_INDEX_PREFIX}news_articles"
            for article in test_articles:
                es_client.index(
                    index=index_name,
                    id=article.id,
                    body={
                        'title': article.title,
                        'content': article.content,
                        'summary': article.summary,
                        'category': article.category.id,
                        'source': article.source,
                        'author': article.author,
                        'source_url': article.source_url,
                        'status': article.status,
                        'publish_time': article.publish_time.isoformat() if article.publish_time else None,
                        'created_by': article.created_by.id if article.created_by else None
                    },
                    refresh=True
                )

            url = reverse('api:news_search:news-search-search')
            
            # 测试多条件搜索
            response = authenticated_client.get(url, {
                'q': 'Test',
                'source': 'Test Source',
                'category': test_articles[0].category.id,
                'start_date': (timezone.now() - timezone.timedelta(days=1)).isoformat(),
                'end_date': timezone.now().isoformat()
            })
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data['results']) == 5
            
            # 测试排序
            response = authenticated_client.get(url, {
                'q': 'Test',
                'sort': '-publish_time'
            })
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data['results']) == 5
            
            # 测试字段过滤
            response = authenticated_client.get(url, {
                'q': 'Test',
                'fields': ['title', 'source']
            })
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data['results']) == 5
            assert all('title' in result for result in response.data['results'])
            assert all('source' in result for result in response.data['results'])
            
        except ConnectionError:
            pytest.skip("Elasticsearch服务未启动")

    def test_search_with_pagination(self, authenticated_client, test_articles, es_client):
        """测试搜索分页功能"""
        try:
            # 索引测试文章
            index_name = f"{settings.ELASTICSEARCH_INDEX_PREFIX}news_articles"
            for article in test_articles:
                es_client.index(
                    index=index_name,
                    id=article.id,
                    body={
                        'title': article.title,
                        'content': article.content,
                        'summary': article.summary,
                        'category': article.category.id,
                        'source': article.source,
                        'author': article.author,
                        'source_url': article.source_url,
                        'status': article.status,
                        'publish_time': article.publish_time.isoformat() if article.publish_time else None,
                        'created_by': article.created_by.id if article.created_by else None
                    },
                    refresh=True
                )

            url = reverse('api:news_search:news-search-search')
            response = authenticated_client.get(url, {
                'q': 'Test',
                'page': 1,
                'page_size': 2
            })
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data['results']) == 2
            assert response.data['count'] > 2
        except ConnectionError:
            pytest.skip("Elasticsearch服务未启动")

    def test_search_suggestions(self, authenticated_client):
        """测试搜索建议功能"""
        # 创建一些搜索建议
        suggestions = [
            ('python programming', 100),
            ('python web', 80),
            ('python tutorial', 60),
            ('django tutorial', 40)
        ]
        
        for keyword, count in suggestions:
            SearchSuggestion.objects.create(
                keyword=keyword,
                search_count=count
            )
        
        url = reverse('api:news_search:news-search-suggest')
        
        # 测试前缀匹配
        response = authenticated_client.get(url, {'prefix': 'python'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3
        
        # 验证按搜索次数降序排序
        search_counts = [item['search_count'] for item in response.data]
        assert search_counts == sorted(search_counts, reverse=True)
        
        # 测试空前缀
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == len(suggestions)
        
        # 测试无匹配结果
        response = authenticated_client.get(url, {'prefix': 'nonexistent'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0
        
        # 测试分页
        response = authenticated_client.get(url, {
            'prefix': 'python',
            'page': 1,
            'page_size': 2
        })
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        
        # 验证返回字段
        for item in response.data:
            assert 'keyword' in item
            assert 'search_count' in item

    def test_search_history(self, authenticated_client):
        """测试搜索历史功能"""
        # 确保用户已认证
        user = authenticated_client.handler._force_user
        assert user is not None and user.is_authenticated
        
        # 创建一些搜索历史
        search_url = reverse('api:news_search:news-search-search')
        search_terms = ['python', 'django', 'elasticsearch']
        for term in search_terms:
            SearchHistory.objects.create(
                user=user,
                keyword=term
            )
        
        # 测试获取搜索历史
        history_url = reverse('api:news_search:news-search-history')
        response = authenticated_client.get(history_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['history']) == 3
        
        # 验证返回的历史记录
        for item in response.data['history']:
            assert 'keyword' in item
            assert 'created_at' in item
            assert item['keyword'] in search_terms

    def test_clear_search_history(self, authenticated_client):
        """测试清除搜索历史功能"""
        # 创建一些搜索历史
        search_terms = ['python', 'django', 'elasticsearch']
        for term in search_terms:
            SearchHistory.objects.create(
                user=authenticated_client.handler._force_user,
                keyword=term
            )
        
        # 验证搜索历史存在
        history_url = reverse('api:news_search:news-search-history')
        history_response = authenticated_client.get(history_url)
        assert history_response.status_code == status.HTTP_200_OK
        assert len(history_response.data['history']) > 0
        
        # 清除搜索历史
        url = reverse('api:news_search:news-search-clear-history')
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        
        # 验证搜索历史已清除
        history_response = authenticated_client.get(history_url)
        assert history_response.status_code == status.HTTP_200_OK
        assert len(history_response.data['history']) == 0

    def test_hot_searches(self, authenticated_client):
        """测试热门搜索功能"""
        # 创建一些热门搜索
        hot_keywords = [
            ('热门搜索1', 100, True),
            ('热门搜索2', 80, True),
            ('热门搜索3', 60, True),
            ('普通搜索', 20, False)
        ]
        
        suggestions = []
        for keyword, count, is_hot in hot_keywords:
            suggestion = SearchSuggestion.objects.create(
                keyword=keyword,
                search_count=count,
                is_hot=is_hot,
                created_at=timezone.now()
            )
            suggestions.append(suggestion)
        
        url = reverse('api:news_search:news-search-hot')
        
        # 测试基本热门搜索
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3  # 只返回热门搜索
        
        # 验证按搜索次数降序排序
        search_counts = [item['search_count'] for item in response.data]
        assert search_counts == sorted(search_counts, reverse=True)
        
        # 验证返回字段
        for item in response.data:
            assert 'keyword' in item
            assert 'search_count' in item
            assert 'is_hot' in item
            assert item['is_hot'] is True
        
        # 测试分页
        response = authenticated_client.get(url, {'page': 1, 'page_size': 2})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        
        # 测试时间范围过滤
        params = {
            'start_time': (timezone.now() - timezone.timedelta(hours=1)).isoformat(),
            'end_time': timezone.now().isoformat()
        }
        response = authenticated_client.get(url, params)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3  # 所有热门搜索都在时间范围内
        
        # 测试最小搜索次数过滤
        response = authenticated_client.get(url, {'min_count': 70})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2  # 只有两个搜索次数大于70
        
        # 测试关键词前缀过滤
        response = authenticated_client.get(url, {'prefix': '热门'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3  # 只有三个以"热门"开头的搜索

    def test_search_with_highlight(self, authenticated_client, test_articles, es_client):
        """测试搜索结果高亮功能"""
        try:
            # 索引测试文章
            index_name = f"{settings.ELASTICSEARCH_INDEX_PREFIX}news_articles"
            for article in test_articles:
                es_client.index(
                    index=index_name,
                    id=article.id,
                    body={
                        'title': article.title,
                        'content': article.content,
                        'summary': article.summary,
                        'category': article.category.id,
                        'source': article.source,
                        'author': article.author,
                        'source_url': article.source_url,
                        'status': article.status,
                        'publish_time': article.publish_time.isoformat() if article.publish_time else None,
                        'created_by': article.created_by.id if article.created_by else None
                    },
                    refresh=True
                )

            url = reverse('api:news_search:news-search-search')
            
            # 测试标题高亮
            response = authenticated_client.get(url, {
                'q': 'Test',
                'highlight': 'true',
                'fields': ['title']
            })
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data['results']) > 0
            assert '<em>Test</em>' in response.data['results'][0]['title']
            
            # 测试内容高亮
            response = authenticated_client.get(url, {
                'q': 'content',
                'highlight': 'true',
                'fields': ['content']
            })
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data['results']) > 0
            assert '<em>content</em>' in response.data['results'][0]['content']
            
            # 测试多字段高亮
            response = authenticated_client.get(url, {
                'q': 'Test',
                'highlight': 'true',
                'fields': ['title', 'content', 'summary']
            })
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data['results']) > 0
            result = response.data['results'][0]
            assert any('<em>Test</em>' in field for field in [result.get('title', ''), result.get('content', ''), result.get('summary', '')])
            
            # 测试自定义高亮标签
            response = authenticated_client.get(url, {
                'q': 'Test',
                'highlight': 'true',
                'highlight_pre_tags': '<strong>',
                'highlight_post_tags': '</strong>',
                'fields': ['title']
            })
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data['results']) > 0
            assert '<strong>Test</strong>' in response.data['results'][0]['title']
            
        except ConnectionError:
            pytest.skip("Elasticsearch服务未启动")

    def test_search_with_field_filter(self, authenticated_client, test_articles, es_client):
        """测试特定字段搜索功能"""
        try:
            # 索引测试文章
            index_name = f"{settings.ELASTICSEARCH_INDEX_PREFIX}news_articles"
            for article in test_articles:
                es_client.index(
                    index=index_name,
                    id=article.id,
                    body={
                        'title': article.title,
                        'content': article.content,
                        'summary': article.summary,
                        'category': article.category.id,
                        'source': article.source,
                        'author': article.author,
                        'source_url': article.source_url,
                        'status': article.status,
                        'publish_time': article.publish_time.isoformat() if article.publish_time else None,
                        'created_by': article.created_by.id if article.created_by else None
                    },
                    refresh=True
                )

            url = reverse('api:news_search:news-search-search')
            
            # 测试单字段过滤
            response = authenticated_client.get(url, {
                'q': 'Test',
                'fields': 'title'
            })
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data['results']) > 0
            result = response.data['results'][0]
            assert 'title' in result
            assert 'content' not in result
            
            # 测试多字段过滤
            response = authenticated_client.get(url, {
                'q': 'Test',
                'fields': 'title,content,source'
            })
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data['results']) > 0
            result = response.data['results'][0]
            assert 'title' in result
            assert 'content' in result
            assert 'source' in result
            assert 'summary' not in result
            
            # 测试所有字段
            response = authenticated_client.get(url, {
                'q': 'Test',
                'fields': '*'
            })
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data['results']) > 0
            result = response.data['results'][0]
            assert all(field in result for field in [
                'title', 'content', 'summary', 'source', 
                'author', 'source_url', 'status', 'publish_time'
            ])
            
            # 测试无效字段
            response = authenticated_client.get(url, {
                'q': 'Test',
                'fields': 'invalid_field'
            })
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data['results']) > 0
            result = response.data['results'][0]
            assert len(result.keys()) == 0
            
        except ConnectionError:
            pytest.skip("Elasticsearch服务未启动")
