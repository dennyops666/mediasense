import os
import sys
import pytest
from django.test.runner import DiscoverRunner
from django.conf import settings
from django.db import connections

class PytestTestRunner(DiscoverRunner):
    """自定义测试运行器"""
    
    def __init__(self, *args, **kwargs):
        self.pytest_args = []
        super().__init__(*args, **kwargs)
        
    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        """运行测试"""
        self.setup_test_environment()
        self.setup_databases()
        
        # 添加pytest参数
        self.pytest_args = [
            '--verbose',
            '--reuse-db',  # 重用数据库
            '--nomigrations',  # 禁用迁移
        ]
        
        # 如果指定了测试标签，添加到参数中
        if test_labels:
            self.pytest_args.extend(test_labels)
            
        # 运行测试
        result = pytest.main(self.pytest_args)
        
        # 清理
        self.teardown_databases(None)
        self.teardown_test_environment()
        
        return result
    
    def setup_databases(self, **kwargs):
        """设置数据库连接"""
        # 确保所有数据库连接都已关闭
        connections.close_all()
        
        # 对每个数据库连接进行初始化
        for alias in connections:
            connection = connections[alias]
            connection.connect()
            
            # 设置事务隔离级别
            if connection.vendor == 'mysql':
                with connection.cursor() as cursor:
                    cursor.execute('SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED')
                    cursor.execute('SET SESSION autocommit = 1')
        
        return None
    
    def teardown_databases(self, old_config, **kwargs):
        """清理数据库连接"""
        # 关闭所有数据库连接
        connections.close_all() 