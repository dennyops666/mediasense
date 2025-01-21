import json
import os
import asyncio
from io import BytesIO
from django.test import AsyncClient
from rest_framework.test import APIClient, APIRequestFactory
from asgiref.sync import sync_to_async, async_to_sync
from django.http import HttpResponse
from django.test.client import FakePayload, RequestFactory, encode_multipart, BOUNDARY, MULTIPART_CONTENT
from django.test import Client
from rest_framework.test import APIRequestFactory
from rest_framework.response import Response
from django.http import HttpResponse
from rest_framework.renderers import JSONRenderer
from django.urls import resolve
from django.core.handlers.wsgi import WSGIRequest
from rest_framework import status

class AsyncAPIClient(APIClient):
    """异步 API 客户端"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._credentials = {}
        self.headers = {}

    async def force_authenticate(self, user=None, token=None):
        """强制认证"""
        if user:
            self._credentials = {
                'HTTP_AUTHORIZATION': f'Token {token or "dummy"}',
                'user': user
            }
            self.handler._force_user = user
            self.handler._force_token = token
        else:
            self._credentials = {}
            self.handler._force_user = None
            self.handler._force_token = None

    async def _encode_json_data(self, data):
        """编码 JSON 数据"""
        if data is None:
            return None
        return json.dumps(data)

    async def _handle_response(self, response):
        """处理响应"""
        if isinstance(response, Response):
            content = await sync_to_async(JSONRenderer().render)(response.data)
            http_response = HttpResponse(
                content=content,
                status=response.status_code,
                content_type='application/json'
            )
            http_response.headers = getattr(response, 'headers', {})
            http_response._resource_closers = []
            return http_response
        return response

    async def request(self, method, path, data=None, format=None, content_type=None, follow=False, secure=False, **extra):
        """发送请求"""
        try:
            # 设置 content_type
            if format == 'json' and content_type is None:
                content_type = 'application/json'

            # 过滤掉 None 值
            credentials = {k: v for k, v in self._credentials.items() if v is not None}
            request_headers = {**self.headers, **credentials}

            # 序列化数据
            if format == 'json' and data is not None:
                data = await self._encode_json_data(data)

            # 调用父类的 request 方法
            response = await sync_to_async(super().request)(
                method=method,
                path=path,
                data=data,
                content_type=content_type,
                follow=follow,
                secure=secure,
                **{**extra, **request_headers}
            )

            return await self._handle_response(response)
        except Exception as e:
            return HttpResponse(
                content=json.dumps({'error': str(e)}),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content_type='application/json'
            )

    async def get(self, path, data=None, follow=False, **extra):
        """GET 请求"""
        return await self.request('GET', path, data=data, follow=follow, **extra)

    async def post(self, path, data=None, format=None, follow=False, **extra):
        """POST 请求"""
        return await self.request('POST', path, data=data, format=format, follow=follow, **extra)

    async def put(self, path, data=None, format=None, follow=False, **extra):
        """PUT 请求"""
        return await self.request('PUT', path, data=data, format=format, follow=follow, **extra)

    async def patch(self, path, data=None, format=None, follow=False, **extra):
        """PATCH 请求"""
        return await self.request('PATCH', path, data=data, format=format, follow=follow, **extra)

    async def delete(self, path, data=None, follow=False, **extra):
        """DELETE 请求"""
        return await self.request('DELETE', path, data=data, follow=follow, **extra)

    async def options(self, path, data=None, follow=False, **extra):
        """OPTIONS 请求"""
        return await self.request('OPTIONS', path, data=data, follow=follow, **extra)

    async def head(self, path, data=None, follow=False, **extra):
        """HEAD 请求"""
        return await self.request('HEAD', path, data=data, follow=follow, **extra)

    async def logout(self):
        """登出"""
        try:
            await sync_to_async(self.client.logout)()
            self.cookies = {}
            self.session = {}
            self._credentials = {}
        except Exception as e:
            return HttpResponse(
                content=json.dumps({'error': str(e)}),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content_type='application/json'
            ) 