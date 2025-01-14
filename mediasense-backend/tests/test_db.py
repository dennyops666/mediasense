import pytest
from django.db import connection, transaction
from django.conf import settings
from concurrent.futures import ThreadPoolExecutor
import threading
from news.models import News
from .factories import NewsFactory

pytestmark = pytest.mark.django_db

class TestDatabaseConnectionPool:
    """TC-DB-001: 数据库连接池测试"""

    def test_connection_pool_initialization(self):
        """测试连接池初始化"""
        assert connection.settings_dict['CONN_MAX_AGE'] > 0
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1

    def test_concurrent_connections(self):
        """测试并发请求获取连接"""
        def db_operation():
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return cursor.fetchone()[0]

        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(lambda _: db_operation(), range(10)))
            assert all(r == 1 for r in results)

    def test_connection_timeout(self):
        """测试连接超时处理"""
        from django.db.utils import OperationalError
        
        # 模拟超时设置
        original_timeout = connection.settings_dict.get('OPTIONS', {}).get('connect_timeout')
        connection.settings_dict.setdefault('OPTIONS', {})['connect_timeout'] = 1
        
        try:
            with pytest.raises(OperationalError):
                with connection.cursor() as cursor:
                    # 执行一个会超时的查询
                    cursor.execute("SELECT SLEEP(2)")
        finally:
            # 恢复原始超时设置
            if original_timeout:
                connection.settings_dict['OPTIONS']['connect_timeout'] = original_timeout
            else:
                del connection.settings_dict['OPTIONS']['connect_timeout']

    def test_connection_release(self):
        """测试连接释放机制"""
        initial_connections = len(connection.connection_pool._connections)
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # 验证连接被正确释放回连接池
        assert len(connection.connection_pool._connections) == initial_connections

    def test_connection_pool_max_capacity(self):
        """测试连接池满载情况"""
        max_connections = settings.DATABASES['default'].get('CONN_MAX_AGE', 0)
        connections = []
        
        try:
            # 尝试获取超过最大连接数的连接
            for _ in range(max_connections + 1):
                connections.append(connection.cursor())
        except Exception as e:
            assert "too many connections" in str(e).lower()
        finally:
            # 清理连接
            for conn in connections:
                conn.close()

class TestDatabaseTransactions:
    """TC-DB-002: 数据库事务测试"""

    def test_single_table_transaction(self):
        """测试单表事务操作"""
        with transaction.atomic():
            news = NewsFactory(title="Test News")
            assert News.objects.filter(id=news.id).exists()
            
            # 回滚事务
            transaction.set_rollback(True)
        
        # 验证数据被回滚
        assert not News.objects.filter(id=news.id).exists()

    def test_multi_table_transaction(self):
        """测试多表事务操作"""
        with transaction.atomic():
            # 创建新闻和相关数据
            news = NewsFactory(title="Test News")
            category = news.category
            
            # 验证数据已创建
            assert News.objects.filter(id=news.id).exists()
            assert category.news_set.filter(id=news.id).exists()
            
            # 回滚事务
            transaction.set_rollback(True)
        
        # 验证所有相关数据都被回滚
        assert not News.objects.filter(id=news.id).exists()

    def test_transaction_rollback(self):
        """测试事务回滚"""
        try:
            with transaction.atomic():
                news = NewsFactory(title="Test News")
                assert News.objects.filter(id=news.id).exists()
                raise Exception("Forced rollback")
        except Exception:
            pass
        
        # 验证数据被回滚
        assert not News.objects.filter(id=news.id).exists()

    def test_transaction_isolation(self):
        """测试事务隔离级别"""
        def create_news():
            with transaction.atomic():
                return NewsFactory(title="Concurrent News")

        def read_news(news_id):
            with transaction.atomic():
                return News.objects.filter(id=news_id).exists()

        # 在不同线程中执行事务
        with ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(create_news)
            news = future1.result()
            future2 = executor.submit(read_news, news.id)
            assert future2.result()

    def test_deadlock_handling(self):
        """测试死锁处理"""
        from django.db.utils import OperationalError
        
        news1 = NewsFactory(title="News 1")
        news2 = NewsFactory(title="News 2")
        
        def update_news(news1_id, news2_id):
            try:
                with transaction.atomic():
                    # 获取第一个锁
                    n1 = News.objects.select_for_update().get(id=news1_id)
                    n1.title = "Updated News 1"
                    n1.save()
                    
                    # 模拟延迟，增加死锁概率
                    import time
                    time.sleep(0.1)
                    
                    # 尝试获取第二个锁
                    n2 = News.objects.select_for_update().get(id=news2_id)
                    n2.title = "Updated News 2"
                    n2.save()
            except OperationalError as e:
                assert "deadlock" in str(e).lower()
                raise
        
        # 在不同线程中执行可能导致死锁的操作
        with ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(update_news, news1.id, news2.id)
            future2 = executor.submit(update_news, news2.id, news1.id)
            
            # 至少有一个事务应该成功
            try:
                future1.result()
            except OperationalError:
                future2.result() 