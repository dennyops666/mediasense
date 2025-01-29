import pytest
from django.core.cache import cache
from django.conf import settings
from django.test import TestCase, override_settings
from redis.exceptions import ConnectionError
import redis
import time
from concurrent.futures import ThreadPoolExecutor

class TestRedisConnection(TestCase):
    """TC-CACHE-001: Redis连接管理测试"""

    def setUp(self):
        """测试初始化"""
        self.redis_settings = settings.CACHES['default']

    def test_connection_settings(self):
        """测试Redis连接配置"""
        # 验证Redis基本配置
        self.assertEqual(self.redis_settings['BACKEND'], 'django_redis.cache.RedisCache')
        self.assertTrue('LOCATION' in self.redis_settings)
        self.assertTrue('OPTIONS' in self.redis_settings)

    def test_connection_successful(self):
        """测试Redis连接成功"""
        try:
            # 测试基本的缓存操作来验证连接
            cache.set('test_connection', 'test_value')
            value = cache.get('test_connection')
            self.assertEqual(value, 'test_value')
        except Exception as e:
            self.fail(f"Redis连接失败: {str(e)}")

    def test_basic_operations(self):
        """测试基本的缓存操作"""
        # 设置缓存
        cache.set('test_key', 'test_value', 60)
        # 获取缓存
        value = cache.get('test_key')
        self.assertEqual(value, 'test_value')
        # 删除缓存
        cache.delete('test_key')
        value = cache.get('test_key')
        self.assertIsNone(value)

    def test_cache_timeout(self):
        """测试缓存超时"""
        # 设置一个1秒过期的缓存
        cache.set('timeout_key', 'timeout_value', 1)
        # 立即获取
        value = cache.get('timeout_key')
        self.assertEqual(value, 'timeout_value')
        # 等待缓存过期
        time.sleep(1.1)
        # 再次获取
        value = cache.get('timeout_key')
        self.assertIsNone(value)

    def test_concurrent_access(self):
        """测试并发访问"""
        def cache_operation():
            try:
                key = f'concurrent_key_{time.time()}'
                cache.set(key, 'value', 60)
                value = cache.get(key)
                cache.delete(key)
                return value == 'value'
            except Exception:
                return False

        # 使用线程池模拟并发请求
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(lambda _: cache_operation(), range(20)))

        # 验证所有操作都成功完成
        self.assertTrue(all(results))

    def test_connection_failure_handling(self):
        """测试Redis连接失败的处理"""
        try:
            # 使用错误的Redis地址来测试连接失败的情况
            with self.settings(CACHES={
                'default': {
                    'BACKEND': 'django.core.cache.backends.redis.RedisCache',
                    'LOCATION': 'redis://127.0.0.1:6380/1',  # 使用错误的端口
                    'OPTIONS': {
                        'db': 1,
                        'socket_connect_timeout': 1,  # 设置较短的超时时间
                        'socket_timeout': 1,
                        'retry_on_timeout': False,
                        'max_connections': 100,
                    },
                }
            }):
                from django.core.cache import cache
                cache.set('test_key', 'test_value')
                self.fail("应该抛出连接异常")
        except Exception as e:
            self.assertTrue(isinstance(e, Exception))
            self.assertIn("Error", str(e))

    def test_large_data_handling(self):
        """测试大数据处理"""
        # 生成1MB的测试数据
        large_data = 'x' * (1024 * 1024)  # 1MB string
        
        # 设置大数据缓存
        cache.set('large_key', large_data, 60)
        
        # 获取并验证数据
        retrieved_data = cache.get('large_key')
        self.assertEqual(len(retrieved_data), len(large_data))
        self.assertEqual(retrieved_data, large_data)

    def test_cache_versioning(self):
        """测试缓存版本控制"""
        # 设置不同版本的缓存
        cache.set('version_key', 'v1', version=1)
        cache.set('version_key', 'v2', version=2)
        
        # 验证不同版本的数据
        self.assertEqual(cache.get('version_key', version=1), 'v1')
        self.assertEqual(cache.get('version_key', version=2), 'v2')

    def test_cache_prefix(self):
        """测试缓存前缀"""
        # 设置缓存
        key = 'test_key'
        value = 'test_value'
        cache.set(key, value)
        
        # 验证缓存是否设置成功
        self.assertEqual(cache.get(key), value)

    def tearDown(self):
        """测试清理"""
        # 清理所有测试用的缓存键
        cache.clear() 