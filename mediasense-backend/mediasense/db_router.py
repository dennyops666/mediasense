from django.conf import settings
import random
import logging

logger = logging.getLogger(__name__)

class PrimaryReplicaRouter:
    """主从数据库路由"""

    def __init__(self):
        self.load_balancing = getattr(settings, 'API_GATEWAY', {}).get('LOAD_BALANCING', {})
        self.app_mapping = getattr(settings, 'DATABASE_APPS_MAPPING', {})

    def _get_replica_for_app(self, app_label):
        """获取应用对应的从库"""
        for db, apps in self.app_mapping.items():
            if app_label in apps and db != 'default':
                return db
        return None

    def db_for_read(self, model, **hints):
        """读操作路由到从库"""
        if not self.load_balancing.get('enabled', False):
            return 'default'

        # 获取应用名称
        app_label = model._meta.app_label

        # 根据应用映射选择数据库
        replica = self._get_replica_for_app(app_label)
        if replica:
            logger.debug(f"Routing read operation for {app_label} to {replica}")
            return replica

        # 如果没有特定映射，使用默认数据库
        logger.debug(f"No specific mapping for {app_label}, using default")
        return 'default'

    def db_for_write(self, model, **hints):
        """写操作路由到主库"""
        app_label = model._meta.app_label
        logger.debug(f"Routing write operation for {app_label} to default")
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """允许所有数据库之间的关系"""
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """只允许在主库上进行迁移"""
        if db == 'default':
            return True
        return False 