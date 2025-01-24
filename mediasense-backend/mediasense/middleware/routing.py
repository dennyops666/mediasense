from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.urls import resolve, Resolver404
import logging

logger = logging.getLogger(__name__)

class RoutingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.route_config = getattr(settings, 'API_GATEWAY', {}).get('ROUTE_CONFIG', {})
        self.service_registry = getattr(settings, 'SERVICE_REGISTRY', {})

    def __call__(self, request):
        try:
            # 解析请求路径
            resolver_match = resolve(request.path)
            
            # 根据URL前缀转发到对应服务
            for prefix, service in self.route_config.items():
                if request.path.startswith(prefix):
                    # 获取服务URL
                    service_url = self.service_registry.get(service)
                    if not service_url:
                        logger.error(f"Service {service} not found in registry")
                        return JsonResponse({
                            'error': 'service_not_found',
                            'detail': f'服务 {service} 未注册'
                        }, status=503)

                    # 记录路由信息
                    logger.info(f"Routing request {request.path} to {service_url}")
                    request.META['HTTP_X_FORWARDED_SERVICE'] = service
                    request.META['HTTP_X_SERVICE_URL'] = service_url
                    break
            
            response = self.get_response(request)
            return response
            
        except Resolver404:
            logger.warning(f"Resource not found: {request.path}")
            return JsonResponse({
                'error': 'not_found',
                'detail': '请求的资源不存在'
            }, status=404)
        except Exception as e:
            logger.error(f"路由转发错误: {str(e)}", exc_info=True)
            return JsonResponse({
                'error': 'internal_error',
                'detail': '服务器内部错误'
            }, status=500) 