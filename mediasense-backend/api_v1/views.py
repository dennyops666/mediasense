from django.conf import settings
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="MediaSense API",
        default_version='v1',
        description="MediaSense新闻舆情监测系统API文档",
        terms_of_service="https://www.mediasense.com/terms/",
        contact=openapi.Contact(email="admin@mediasense.test"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

docs_view = schema_view.with_ui('swagger', cache_timeout=0)
