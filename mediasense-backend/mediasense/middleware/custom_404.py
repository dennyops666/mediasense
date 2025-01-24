from django.http import JsonResponse

class Custom404Middleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if response.status_code == 404:
            return JsonResponse({
                'error': 'not_found',
                'detail': '请求的资源不存在'
            }, status=404)
        return response 