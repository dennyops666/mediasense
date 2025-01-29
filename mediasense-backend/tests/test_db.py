import pytest
from django.test import TestCase, TransactionTestCase
from django.db import connection, transaction, OperationalError, connections
from django.conf import settings
from concurrent.futures import ThreadPoolExecutor
import time
from news.models import NewsArticle
from .factories import NewsArticleFactory

pytestmark = pytest.mark.django_db(transaction=True)

class TestDatabasePool(TestCase):
    """数据库连接池测试"""

    def setUp(self):
        """测试初始化"""
        self.db_settings = settings.DATABASES['default']

    def test_connection_settings(self):
        """测试连接池配置"""
        # 验证连接池基本配置
        self.assertEqual(self.db_settings['CONN_MAX_AGE'], 60)  # 连接保持60秒
        self.assertEqual(self.db_settings['OPTIONS']['charset'], 'utf8mb4')  # 字符集utf8mb4
        self.assertEqual(self.db_settings['OPTIONS']['init_command'], "SET sql_mode='STRICT_TRANS_TABLES'")  # SQL模式
        
        # 验证测试数据库配置
        self.assertEqual(self.db_settings['TEST']['NAME'], self.db_settings['NAME'])  # 使用相同的数据库名
        self.assertIsNone(self.db_settings['TEST']['MIRROR'])  # 不使用镜像
        self.assertFalse(self.db_settings['TEST']['CREATE_DB'])  # 不创建新的测试数据库

    def test_connection_reuse(self):
        """测试连接复用"""
        # 第一次查询，建立连接
        with connection.cursor() as cursor:
            cursor.execute('SELECT CONNECTION_ID()')
            first_thread_id = cursor.fetchone()[0]

        # 短时间内第二次查询，应该复用连接
        with connection.cursor() as cursor:
            cursor.execute('SELECT CONNECTION_ID()')
            second_thread_id = cursor.fetchone()[0]

        # 验证两次查询使用了同一个连接
        self.assertEqual(first_thread_id, second_thread_id)

    def test_concurrent_connections(self):
        """测试并发连接"""
        def db_operation():
            try:
                with connection.cursor() as cursor:
                    cursor.execute('SELECT SLEEP(1)')
                return True
            except OperationalError:
                return False

        # 使用线程池模拟并发请求
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(lambda _: db_operation(), range(20)))

        # 验证所有请求都成功完成
        self.assertTrue(all(results))

class TestDatabaseTransaction(TransactionTestCase):
    """数据库事务测试"""

    def setUp(self):
        """测试初始化"""
        super().setUp()
        self.test_table = 'test_transaction'
        # 创建测试表
        with connection.cursor() as cursor:
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS {self.test_table} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    value INT NOT NULL
                )
            ''')

    def tearDown(self):
        """测试清理"""
        super().tearDown()
        # 删除测试表
        with connection.cursor() as cursor:
            cursor.execute(f'DROP TABLE IF EXISTS {self.test_table}')

    def test_successful_transaction(self):
        """测试成功的事务"""
        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    # 插入测试数据
                    cursor.execute(f'INSERT INTO {self.test_table} (value) VALUES (1)')
                    cursor.execute(f'INSERT INTO {self.test_table} (value) VALUES (2)')

            # 验证数据已正确提交
            with connection.cursor() as cursor:
                cursor.execute(f'SELECT COUNT(*) FROM {self.test_table}')
                count = cursor.fetchone()[0]
                self.assertEqual(count, 2)
        except Exception as e:
            self.fail(f"事务执行失败: {str(e)}")

    def test_failed_transaction(self):
        """测试失败的事务"""
        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    # 插入第一条数据
                    cursor.execute(f'INSERT INTO {self.test_table} (value) VALUES (1)')
                    # 故意制造错误
                    cursor.execute('SELECT * FROM nonexistent_table')
        except Exception:
            pass  # 预期会抛出异常

        # 验证数据已回滚
        with connection.cursor() as cursor:
            cursor.execute(f'SELECT COUNT(*) FROM {self.test_table}')
            count = cursor.fetchone()[0]
            self.assertEqual(count, 0)

    def test_nested_transaction(self):
        """测试嵌套事务"""
        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute(f'INSERT INTO {self.test_table} (value) VALUES (1)')

                    try:
                        with transaction.atomic():
                            cursor.execute(f'INSERT INTO {self.test_table} (value) VALUES (2)')
                            raise ValueError('测试回滚')
                    except ValueError:
                        pass  # 内部事务应该回滚

                    cursor.execute(f'INSERT INTO {self.test_table} (value) VALUES (3)')

            # 验证外部事务的数据正确提交，内部事务的数据被回滚
            with connection.cursor() as cursor:
                cursor.execute(f'SELECT COUNT(*) FROM {self.test_table}')
                count = cursor.fetchone()[0]
                self.assertEqual(count, 2)  # 应该只有两条记录（1和3）
        except Exception as e:
            self.fail(f"事务执行失败: {str(e)}")

    def test_transaction_isolation(self):
        """测试事务隔离性"""
        from django.db import connections
        
        # 创建一个新的数据库连接
        new_connection = connections.create_connection('default')
        try:
            # 在主连接中开启事务并插入数据
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute(f'INSERT INTO {self.test_table} (value) VALUES (1)')
                    
                    # 在新连接中查询，不应该看到未提交的数据
                    with new_connection.cursor() as cursor2:
                        cursor2.execute(f'SELECT COUNT(*) FROM {self.test_table}')
                        count = cursor2.fetchone()[0]
                        self.assertEqual(count, 0)  # 在新连接中不应该看到未提交的数据
        finally:
            new_connection.close()

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
        import socket
        
        # 使用一个不存在的主机来测试超时
        original_host = connection.settings_dict.get('HOST')
        original_timeout = connection.settings_dict.get('OPTIONS', {}).get('connect_timeout')
        
        try:
            # 设置一个不存在的主机和较短的超时时间
            connection.settings_dict['HOST'] = 'non-existent-host'
            connection.settings_dict.setdefault('OPTIONS', {})['connect_timeout'] = 1
            
            with pytest.raises((OperationalError, socket.gaierror)):
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
        finally:
            # 恢复原始设置
            connection.settings_dict['HOST'] = original_host
            if original_timeout:
                connection.settings_dict['OPTIONS']['connect_timeout'] = original_timeout
            else:
                del connection.settings_dict['OPTIONS']['connect_timeout']

    def test_connection_release(self):
        """测试连接释放机制"""
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # 验证连接可以重用
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1

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

    @pytest.fixture(autouse=True)
    def setup_cleanup(self):
        """设置和清理测试数据"""
        self.test_news = []
        yield
        # 清理测试数据
        NewsArticle.objects.filter(id__in=[n.id for n in self.test_news]).delete()

    def test_single_table_transaction(self):
        """测试单表事务操作"""
        with transaction.atomic():
            news = NewsArticleFactory(title="Test News")
            self.test_news.append(news)
            assert NewsArticle.objects.filter(id=news.id).exists()
            
            # 回滚事务
            transaction.set_rollback(True)
        
        # 验证数据被回滚
        assert not NewsArticle.objects.filter(id=news.id).exists()

    def test_multi_table_transaction(self):
        """测试多表事务操作"""
        with transaction.atomic():
            # 创建新闻和相关数据
            news = NewsArticleFactory(title="Test News")
            self.test_news.append(news)
            category = news.category
            
            # 验证数据已创建
            assert NewsArticle.objects.filter(id=news.id).exists()
            assert category.articles.filter(id=news.id).exists()
            
            # 回滚事务
            transaction.set_rollback(True)
        
        # 验证所有相关数据都被回滚
        assert not NewsArticle.objects.filter(id=news.id).exists()

    def test_transaction_rollback(self):
        """测试事务回滚"""
        news_id = None
        try:
            with transaction.atomic():
                news = NewsArticleFactory(title="Test News")
                self.test_news.append(news)
                news_id = news.id
                assert NewsArticle.objects.filter(id=news.id).exists()
                raise Exception("Forced rollback")
        except Exception:
            pass
        
        # 验证数据被回滚
        assert not NewsArticle.objects.filter(id=news_id).exists()

    def test_transaction_isolation(self):
        """测试事务隔离级别"""
        def create_news():
            with transaction.atomic():
                news = NewsArticleFactory(title="Concurrent News")
                self.test_news.append(news)
                return news

        def read_news(news_id):
            with transaction.atomic():
                return NewsArticle.objects.filter(id=news_id).exists()

        # 在不同线程中执行事务
        with ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(create_news)
            news = future1.result()
            future2 = executor.submit(read_news, news.id)
            assert future2.result()

    def test_deadlock_handling(self):
        """测试死锁处理"""
        from django.db.utils import OperationalError
        
        news1 = NewsArticleFactory(title="News 1")
        news2 = NewsArticleFactory(title="News 2")
        self.test_news.extend([news1, news2])
        
        def update_news(news1_id, news2_id):
            try:
                with transaction.atomic():
                    # 获取第一个锁
                    n1 = NewsArticle.objects.select_for_update().get(id=news1_id)
                    n1.title = "Updated News 1"
                    n1.save()
                    
                    # 模拟延迟，增加死锁概率
                    import time
                    time.sleep(0.1)
                    
                    # 尝试获取第二个锁
                    n2 = NewsArticle.objects.select_for_update().get(id=news2_id)
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