from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework import viewsets, status, exceptions
from asgiref.sync import sync_to_async
import asyncio
from django.core.exceptions import ValidationError
from django.db import models

class AsyncViewSet:
    """异步视图集"""

    async def list(self, request, *args, **kwargs):
        """列表"""
        queryset = await sync_to_async(self.get_queryset)()
        serializer = self.get_serializer(queryset, many=True)
        response = Response(serializer.data)
        if asyncio.iscoroutine(response):
            response = await response
        if not isinstance(response, HttpResponse):
            response = Response(response)
        return response

    async def create(self, request, *args, **kwargs):
        """创建"""
        serializer = self.get_serializer(data=request.data)
        if await sync_to_async(serializer.is_valid)(raise_exception=True):
            instance = await sync_to_async(serializer.save)()
            response = Response(serializer.data, status=status.HTTP_201_CREATED)
            if asyncio.iscoroutine(response):
                response = await response
            if not isinstance(response, HttpResponse):
                response = Response(response)
            return response

    async def retrieve(self, request, *args, **kwargs):
        """获取"""
        instance = await sync_to_async(self.get_object)()
        serializer = self.get_serializer(instance)
        response = Response(serializer.data)
        if asyncio.iscoroutine(response):
            response = await response
        if not isinstance(response, HttpResponse):
            response = Response(response)
        return response

    async def update(self, request, *args, **kwargs):
        """更新"""
        instance = await sync_to_async(self.get_object)()
        serializer = self.get_serializer(instance, data=request.data)
        if await sync_to_async(serializer.is_valid)(raise_exception=True):
            instance = await sync_to_async(serializer.save)()
            response = Response(serializer.data)
            if asyncio.iscoroutine(response):
                response = await response
            if not isinstance(response, HttpResponse):
                response = Response(response)
            return response

    async def destroy(self, request, *args, **kwargs):
        """删除"""
        instance = await sync_to_async(self.get_object)()
        await sync_to_async(instance.delete)()
        response = Response(status=status.HTTP_204_NO_CONTENT)
        if asyncio.iscoroutine(response):
            response = await response
        if not isinstance(response, HttpResponse):
            response = Response(response)
        return response 