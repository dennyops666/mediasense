from django.conf import settings
import random

class PrimaryReplicaRouter:
    """
    主从数据库路由器，实现读写分离
    """
    
    def db_for_read(self, model, **hints):
        """
        读操作路由到从库
        """
        if hasattr(settings, 'API_GATEWAY') and settings.API_GATEWAY['LOAD_BALANCING']['ENABLED']:
            replicas = settings.API_GATEWAY['LOAD_BALANCING']['REPLICAS']
            if replicas:
                return random.choice(replicas)
        return 'default'

    def db_for_write(self, model, **hints):
        """
        写操作路由到主库
        """
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """
        允许所有数据库之间的关系
        """
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        只在主库上执行迁移
        """
        return db == 'default' 