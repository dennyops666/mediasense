from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from rest_framework import status

class Custom404Middleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        if response.status_code == 404 and not hasattr(response, 'data'):
            return JsonResponse(
                {'message': '请求的资源不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return response 