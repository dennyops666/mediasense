from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MonitorConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "monitor"
    verbose_name = _('系统监控')

    def ready(self):
        try:
            import monitor.signals
        except ImportError:
            pass
