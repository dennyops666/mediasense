import pytest
from django.core.cache import cache
from django.conf import settings
from redis import Redis
from redis.sentinel import Sentinel
import time
from concurrent.futures import ThreadPoolExecutor

pytestmark = pytest.mark.django_db

class TestRedisConnectionManagement:
    """TC-CACHE-001: Redis连接管理测试"""

    @pytest.fixture
    def redis_client(self):
        """获取Redis客户端"""
        if hasattr(settings, 'REDIS_SENTINEL_HOSTS'):
            sentinel = Sentinel(settings.REDIS_SENTINEL_HOSTS)
            return sentinel.master_for('mymaster')
        else:
            return Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB
            )

    def test_redis_connection_establishment(self, redis_client):
        """测试Redis连接建立"""
        assert redis_client.ping()
        
        # 测试基本的读写操作
        redis_client.set('test_key', 'test_value')
        assert redis_client.get('test_key') == b'test_value'
        redis_client.delete('test_key')

    def test_connection_pool_management(self, redis_client):
        """测试连接池管理"""
        def redis_operation():
            # 执行一个简单的Redis操作
            return redis_client.incr('test_counter')

        # 并发执行多个Redis操作
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(redis_operation) for _ in range(10)]
            results = [f.result() for f in futures]
        
        # 验证计数器的最终值
        assert redis_client.get('test_counter') == b'10'
        redis_client.delete('test_counter')

    def test_connection_failure_recovery(self, redis_client):
        """测试连接失败恢复"""
        # 模拟连接断开
        redis_client.connection_pool.disconnect()
        
        # 尝试重新连接
        max_retries = 3
        for i in range(max_retries):
            try:
                assert redis_client.ping()
                break
            except Exception:
                if i == max_retries - 1:
                    raise
                time.sleep(0.1)

    def test_connection_timeout_handling(self, redis_client):
        """测试连接超时处理"""
        from redis.exceptions import TimeoutError
        
        # 设置一个很短的超时时间
        redis_client.connection_pool.connection_kwargs['socket_timeout'] = 0.001
        
        try:
            # 执行一个耗时操作，应该触发超时
            with pytest.raises(TimeoutError):
                redis_client.execute_command('DEBUG', 'SLEEP', '0.1')
        finally:
            # 恢复正常的超时设置
            redis_client.connection_pool.connection_kwargs['socket_timeout'] = 1.0

    def test_sentinel_mode_switching(self):
        """测试哨兵模式切换"""
        if not hasattr(settings, 'REDIS_SENTINEL_HOSTS'):
            pytest.skip("Sentinel configuration not found")
        
        sentinel = Sentinel(settings.REDIS_SENTINEL_HOSTS)
        master = sentinel.master_for('mymaster')
        slave = sentinel.slave_for('mymaster')
        
        # 测试主从连接
        assert master.ping()
        assert slave.ping()
        
        # 写入测试数据到主节点
        master.set('test_sentinel', 'value')
        
        # 从从节点读取数据（可能需要等待复制）
        max_retries = 3
        for _ in range(max_retries):
            if slave.get('test_sentinel') == b'value':
                break
            time.sleep(0.1)
        else:
            pytest.fail("Data replication to slave failed")
        
        # 清理测试数据
        master.delete('test_sentinel')

    def test_cache_operations(self, redis_client):
        """测试缓存基本操作"""
        # 测试设置缓存
        cache.set('test_key', 'test_value', 60)
        assert cache.get('test_key') == 'test_value'
        
        # 测试缓存过期
        cache.set('expire_key', 'expire_value', 1)
        time.sleep(1.1)
        assert cache.get('expire_key') is None
        
        # 测试删除缓存
        cache.set('delete_key', 'delete_value')
        cache.delete('delete_key')
        assert cache.get('delete_key') is None
        
        # 测试缓存命中率
        cache.set('hit_key', 'hit_value')
        for _ in range(10):
            assert cache.get('hit_key') == 'hit_value' 