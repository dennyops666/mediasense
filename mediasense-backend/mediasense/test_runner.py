import os
import sys
import pytest
from django.test.runner import DiscoverRunner
from django.conf import settings
from django.db import connections, connection
from django.core.management import call_command

class PytestTestRunner(DiscoverRunner):
    """自定义测试运行器"""
    
    def __init__(self, *args, **kwargs):
        kwargs['keepdb'] = True  # 强制保持数据库
        kwargs['interactive'] = False  # 禁用交互
        self.pytest_args = []
        super().__init__(*args, **kwargs)
        
    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        """运行测试"""
        self.setup_test_environment()
        
        # 添加pytest参数
        self.pytest_args = [
            '--verbose',
            '--reuse-db',  # 重用数据库
            '--no-migrations',  # 禁用迁移
            '--asyncio-mode=strict',  # 严格的异步模式
            '--capture=no',  # 显示所有输出
            '--tb=short',  # 简短的错误追踪
            '--maxfail=1',  # 第一个失败后停止
        ]
        
        # 如果指定了测试标签，添加到参数中
        if test_labels:
            self.pytest_args.extend(test_labels)
            
        # 运行测试
        result = pytest.main(self.pytest_args)
        
        # 清理
        self.teardown_test_environment()
        
        return result
    
    def setup_databases(self, **kwargs):
        """设置数据库连接"""
        # 确保所有数据库连接都已关闭
        connections.close_all()
        
        # 对每个数据库连接进行初始化
        for alias in connections:
            connection = connections[alias]
            if connection.vendor == 'mysql':
                try:
                    with connection.cursor() as cursor:
                        # 基本设置
                        cursor.execute('SET autocommit=1')
                        cursor.execute('SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED')
                        cursor.execute('SET SESSION innodb_lock_wait_timeout=50')
                        cursor.execute('SET SESSION max_execution_time=30000')
                        
                        # 性能优化
                        cursor.execute('SET SESSION innodb_flush_log_at_trx_commit=0')
                        cursor.execute('SET SESSION sync_binlog=0')
                        cursor.execute('SET SESSION innodb_buffer_pool_size=134217728')
                        
                        # 约束和检查
                        cursor.execute('SET FOREIGN_KEY_CHECKS=1')
                        cursor.execute('SET UNIQUE_CHECKS=1')
                        cursor.execute('SET SESSION sql_mode="STRICT_TRANS_TABLES"')
                        
                        # 清理和提交
                        cursor.execute('COMMIT')
                        cursor.execute('SET SESSION group_concat_max_len=1000000')
                except Exception as e:
                    print(f"数据库设置错误: {e}")
                    connection.close()
                    raise
        
        return None
    
    def teardown_databases(self, old_config, **kwargs):
        """清理数据库连接"""
        # 提交或回滚所有挂起的事务
        for alias in connections:
            connection = connections[alias]
            if connection.vendor == 'mysql':
                try:
                    with connection.cursor() as cursor:
                        # 恢复设置
                        cursor.execute('SET FOREIGN_KEY_CHECKS=1')
                        cursor.execute('SET UNIQUE_CHECKS=1')
                        cursor.execute('SET SESSION innodb_flush_log_at_trx_commit=1')
                        cursor.execute('SET SESSION sync_binlog=1')
                        cursor.execute('COMMIT')
                except Exception:
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute('ROLLBACK')
                    except Exception:
                        pass
                finally:
                    try:
                        connection.close()
                    except Exception:
                        pass
        
        # 关闭所有数据库连接
        connections.close_all()