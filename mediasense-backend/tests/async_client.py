from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import SESSION_KEY, BACKEND_SESSION_KEY
from django.contrib.sessions.backends.db import SessionStore
from django.conf import settings
from asgiref.sync import sync_to_async
import json
import asyncio
import os
from io import BytesIO

User = get_user_model()

class AsyncAPIClient(APIClient):
    """异步 API 测试客户端"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.renderer = JSONRenderer()
        self.parser = JSONParser()
        self.default_format = 'json'
        self.csrf_checks = False
        self._credentials = {}
        self._auth = None

    def _prepare_json_data(self, data=None, format=None):
        """准备JSON数据"""
        if format == 'json' and data is not None:
            return json.dumps(data).encode()
        return data

    async def _process_response(self, response):
        """处理响应"""
        if asyncio.iscoroutine(response):
            response = await response

        if isinstance(response, Response):
            if not hasattr(response, 'accepted_renderer'):
                response.accepted_renderer = self.renderer
                response.accepted_media_type = 'application/json'
                response.renderer_context = {
                    'request': getattr(response, 'wsgi_request', None),
                    'response': response,
                }

            if asyncio.iscoroutine(response.data):
                response.data = await response.data

            if not hasattr(response, 'rendered_content'):
                response.rendered_content = self.renderer.render(response.data)

            if hasattr(response, 'render') and callable(response.render):
                await sync_to_async(response.render)()

        return response

    async def request(self, method, path, data=None, follow=False, **extra):
        """发送请求"""
        request_kwargs = {
            'path': path,
            'data': self._prepare_json_data(data, extra.get('format')),
            'follow': follow,
            **extra
        }

        # 使用 sync_to_async 包装 super().request
        response = await sync_to_async(super().request)(**request_kwargs)
        return await self._process_response(response)

    async def get(self, path, data=None, follow=False, **extra):
        """GET 请求"""
        return await self.request('GET', path, data=data, follow=follow, **extra)

    async def post(self, path, data=None, follow=False, **extra):
        """POST 请求"""
        return await self.request('POST', path, data=data, follow=follow, **extra)

    async def put(self, path, data=None, follow=False, **extra):
        """PUT 请求"""
        return await self.request('PUT', path, data=data, follow=follow, **extra)

    async def patch(self, path, data=None, follow=False, **extra):
        """PATCH 请求"""
        return await self.request('PATCH', path, data=data, follow=follow, **extra)

    async def delete(self, path, data=None, follow=False, **extra):
        """DELETE 请求"""
        return await self.request('DELETE', path, data=data, follow=follow, **extra)

    async def options(self, path, data=None, follow=False, **extra):
        """OPTIONS 请求"""
        return await self.request('OPTIONS', path, data=data, follow=follow, **extra)

    async def head(self, path, data=None, follow=False, **extra):
        """HEAD 请求"""
        return await self.request('HEAD', path, data=data, follow=follow, **extra)

    async def trace(self, path, data=None, follow=False, **extra):
        """TRACE 请求"""
        return await self.request('TRACE', path, data=data, follow=follow, **extra)

    async def force_login(self, user):
        """强制登录"""
        self._force_user = user
        if user is None:
            self._credentials = {}
        else:
            token = await sync_to_async(Token.objects.get_or_create)(user=user)
            self._credentials = {
                'HTTP_AUTHORIZATION': f'Token {token[0].key}',
                'REMOTE_USER': str(user.id),
            }

    async def force_authenticate(self, user=None, token=None):
        """强制认证"""
        self._force_user = user
        if user is None and token is None:
            self._credentials = {}
        else:
            self._credentials = {}
            if user:
                self._credentials['REMOTE_USER'] = str(user.id)
            if token:
                self._credentials['HTTP_AUTHORIZATION'] = f'Token {token}'

    async def logout(self):
        """登出"""
        self._force_user = None
        self._credentials = {}

    def get_default_format(self):
        """获取默认格式"""
        return self.default_format

    def get_parser_context(self, http_request):
        """获取解析器上下文"""
        return {
            'view': self,
            'request': http_request,
            'args': getattr(self, 'args', ()),
            'kwargs': getattr(self, 'kwargs', {})
        }

    def get_renderer_context(self):
        """获取渲染器上下文"""
        return {
            'view': self,
            'request': getattr(self, 'request', None),
            'response': getattr(self, 'response', None),
            'args': getattr(self, 'args', ()),
            'kwargs': getattr(self, 'kwargs', {})
        }

    def get_exception_handler_context(self):
        """获取异常处理器上下文"""
        return {
            'view': self,
            'args': getattr(self, 'args', ()),
            'kwargs': getattr(self, 'kwargs', {}),
            'request': getattr(self, 'request', None)
        }

    def get_view_name(self):
        """获取视图名称"""
        return self.__class__.__name__

    def get_view_description(self, html=False):
        """获取视图描述"""
        return self.__class__.__doc__

    def get_format_suffix(self, **kwargs):
        """获取格式后缀"""
        return None

    def get_renderers(self):
        """获取渲染器"""
        return [renderer() for renderer in self.renderer_classes]

    def get_parsers(self):
        """获取解析器"""
        return [parser() for parser in self.parser_classes]

    def get_authenticators(self):
        """获取认证器"""
        return []

    def get_permissions(self):
        """获取权限"""
        return []

    def get_throttles(self):
        """获取限流器"""
        return []

    def get_content_negotiator(self):
        """获取内容协商器"""
        return None

    def get_exception_handler(self):
        """获取异常处理器"""
        return None

    def get_view_description_context(self):
        """获取视图描述上下文"""
        return {} 