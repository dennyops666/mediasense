from django.test.runner import DiscoverRunner
from django.db import connections

class NoDbTestRunner(DiscoverRunner):
    def setup_databases(self, **kwargs):
        """保持现有数据库连接"""
        for alias in connections:
            connection = connections[alias]
            if connection.vendor == 'mysql':
                with connection.cursor() as cursor:
                    # 基本设置
                    cursor.execute('SET autocommit=1')
                    cursor.execute('SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED')
                    cursor.execute('SET SESSION innodb_lock_wait_timeout=50')
                    cursor.execute('SET SESSION max_execution_time=30000')
                    
                    # 约束和检查
                    cursor.execute('SET FOREIGN_KEY_CHECKS=1')
                    cursor.execute('SET UNIQUE_CHECKS=1')
                    cursor.execute('SET SESSION sql_mode="STRICT_TRANS_TABLES"')
                    
                    # 清理和提交
                    cursor.execute('COMMIT')
        return []

    def teardown_databases(self, old_config, **kwargs):
        """保持数据库连接"""
        pass 