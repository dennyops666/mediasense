from rest_framework import viewsets, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from django.db.models import Count, Avg, Max, Min
from django.utils import timezone
from datetime import timedelta
from asgiref.sync import sync_to_async
import json
from rest_framework.request import Request
from django.http import Http404

from .models import MonitorRule, MonitorAlert, SystemMetric, ErrorLog
from .serializers import (
    MonitorRuleSerializer, 
    MonitorAlertSerializer, 
    SystemMetricSerializer,
    ErrorLogSerializer
)
from .services import MonitorService
from monitoring.mixins import SyncAsyncViewSetMixin

class MonitorRuleViewSet(SyncAsyncViewSetMixin, viewsets.ModelViewSet):
    serializer_class = MonitorRuleSerializer
    queryset = MonitorRule.objects.all()
    renderer_classes = [JSONRenderer]
    parser_classes = [JSONParser]
    lookup_field = 'pk'

    async def initialize_request(self, request, *args, **kwargs):
        """初始化请求"""
        if not isinstance(request, Request):
            request = Request(request)

        request.method = request.method.upper()
        if request.content_type == 'application/json' or request.content_type is None:
            request.META['CONTENT_TYPE'] = 'application/json'
            request.META['HTTP_ACCEPT'] = 'application/json'
            if request.body:
                try:
                    data = json.loads(request.body.decode('utf-8'))
                    print(f"原始请求体: {request.body.decode('utf-8')}")  # 调试信息
                    print(f"解析后的数据: {data}")  # 调试信息
                    request._data = data
                    request._full_data = data
                except json.JSONDecodeError as e:
                    print(f"JSON解析错误: {str(e)}")  # 调试信息
                    request._data = {}
                    request._full_data = {}
            else:
                print("请求体为空")  # 调试信息
                request._data = {}
                request._full_data = {}
        
        return request

    async def get_queryset(self):
        """获取查询集"""
        return await sync_to_async(self.queryset.all)()

    async def get_object(self):
        """获取单个对象"""
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs[lookup_url_arg]

        try:
            obj = await sync_to_async(self.queryset.get)(pk=lookup_value)
            return obj
        except MonitorRule.DoesNotExist:
            raise Http404

    def get_serializer(self, *args, **kwargs):
        """获取序列化器实例"""
        serializer_class = self.serializer_class
        kwargs['context'] = {
            'request': getattr(self, 'request', None),
            'format': getattr(self, 'format_kwarg', None),
            'view': self
        }
        # 如果是retrieve动作，不设置many=True
        if self.action == 'retrieve':
            kwargs['many'] = False
        elif len(args) > 0 and isinstance(args[0], (list, tuple)):
            kwargs['many'] = True
            # 如果是列表，将每个元素转换为模型实例
            if isinstance(args[0], list):
                args = (args[0],)
        return serializer_class(*args, **kwargs)

    async def create(self, request, *args, **kwargs):
        """创建规则"""
        try:
            # 初始化请求
            request = await self.initialize_request(request, *args, **kwargs)
            self.request = request
            
            # 获取序列化器
            serializer = self.get_serializer(data=request._data)
            
            # 验证数据
            await sync_to_async(serializer.is_valid)(raise_exception=True)
            
            # 保存数据
            instance = await sync_to_async(serializer.save)(created_by=request.user)
            
            # 返回响应
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            import traceback
            error_msg = f"Error in MonitorRuleViewSet.create: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)  # 开发环境打印错误
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def list(self, request, *args, **kwargs):
        """获取规则列表"""
        try:
            queryset = await self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            data = await sync_to_async(lambda: serializer.data)()
            return Response(data)
        except Exception as e:
            import traceback
            error_msg = f"Error in MonitorRuleViewSet.list: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)  # 开发环境打印错误
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_serializer_context(self):
        """获取序列化器上下文"""
        return {
            'request': getattr(self, 'request', None),
            'format': self.format_kwarg,
            'view': self
        }

    @action(detail=True, methods=['post'])
    async def toggle_status(self, request, *args, **kwargs):
        """切换规则状态"""
        try:
            # 获取对象
            lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
            lookup_value = kwargs.get(lookup_url_kwarg)
            
            try:
                rule = await sync_to_async(self.queryset.get)(pk=lookup_value)
            except MonitorRule.DoesNotExist:
                return Response(
                    {"detail": "规则不存在"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # 切换状态
            rule.is_active = not rule.is_active
            await sync_to_async(rule.save)()
            
            # 序列化返回数据
            serializer = self.get_serializer(rule)
            data = await sync_to_async(lambda: serializer.data)()
            
            return Response(data, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            error_msg = f"Error in MonitorRuleViewSet.toggle_status: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)  # 开发环境打印错误
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def dispatch(self, request, *args, **kwargs):
        """分发请求"""
        try:
            print(f"开始处理请求: {request.method} {request.path}")  # 调试信息
            
            # 初始化请求
            request = await self.initialize_request(request, *args, **kwargs)
            self.request = request
            self.args = args
            self.kwargs = kwargs
            
            print(f"请求数据: {request.data}")  # 调试信息
            print(f"请求用户: {request.user}")  # 调试信息
            
            # 处理自定义动作
            if request.path.endswith('/toggle_status/'):
                return await self.toggle_status(request, *args, **kwargs)
            
            # 获取处理器
            handler = await self.get_handler(request)
            print(f"处理器: {handler}")  # 调试信息
            
            # 执行处理
            try:
                response = await handler(request, *args, **kwargs)
                print(f"处理结果: {response}")  # 调试信息
            except Exception as e:
                print(f"处理异常: {str(e)}")  # 调试信息
                raise
            
            # 完成响应
            try:
                response = await self.finalize_response(request, response, *args, **kwargs)
                print(f"最终响应: {response}")  # 调试信息
                return response
            except Exception as e:
                print(f"完成响应异常: {str(e)}")  # 调试信息
                raise
            
        except Exception as e:
            print(f"请求处理异常: {str(e)}")  # 调试信息
            return await self.handle_exception(e)

class MonitorAlertViewSet(SyncAsyncViewSetMixin, viewsets.ModelViewSet):
    serializer_class = MonitorAlertSerializer
    queryset = MonitorAlert.objects.all()
    renderer_classes = [JSONRenderer]
    lookup_field = 'pk'
    
    async def list(self, request, *args, **kwargs):
        """获取告警列表"""
        try:
            print(f"序列化器参数: action={self.action}, args={args}, kwargs={kwargs}")
            # 获取查询集
            queryset = await self.get_queryset()
            # 序列化数据
            serializer = self.get_serializer(queryset, many=True)
            data = await sync_to_async(lambda: serializer.data)()
            return Response(data)
        except Exception as e:
            import traceback
            error_msg = f"Error in MonitorAlertViewSet.list: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)  # 开发环境打印错误
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def retrieve(self, request, *args, **kwargs):
        """获取单个告警详情"""
        try:
            # 获取对象
            instance = await self.get_object()
            
            # 序列化数据
            serializer = self.get_serializer(instance)
            data = await sync_to_async(lambda: serializer.data)()
            
            # 确保status字段存在
            if not data.get('status') and hasattr(instance, 'status'):
                data['status'] = instance.status
            
            return Response(data)
        except MonitorAlert.DoesNotExist:
            raise Http404(f"未找到ID为 {kwargs.get('pk')} 的告警记录")
        except Exception as e:
            import traceback
            error_msg = f"Error in MonitorAlertViewSet.retrieve: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)  # 开发环境打印错误
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_object(self):
        """获取单个对象"""
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs[lookup_url_kwarg]

        try:
            obj = await sync_to_async(self.queryset.get)(pk=lookup_value)
            return obj
        except MonitorAlert.DoesNotExist:
            raise Http404(f"未找到ID为 {lookup_value} 的告警记录")

    async def get_queryset(self):
        """获取查询集"""
        if self.action == 'list':
            alerts = await sync_to_async(lambda: list(self.queryset.all()))()
            return alerts
        elif self.action == 'retrieve':
            return self.queryset
        return await sync_to_async(lambda: list(self.queryset.all()))()

    def get_serializer(self, *args, **kwargs):
        """获取序列化器实例"""
        serializer_class = self.serializer_class
        kwargs['context'] = {
            'request': getattr(self, 'request', None),
            'format': getattr(self, 'format_kwarg', None),
            'view': self
        }
        
        if self.action == 'list':
            kwargs['many'] = True
        elif self.action == 'retrieve':
            kwargs['many'] = False
        elif len(args) > 0 and isinstance(args[0], (list, tuple)):
            kwargs['many'] = True
            
        return serializer_class(*args, **kwargs)

    async def dispatch(self, request, *args, **kwargs):
        """分发请求"""
        try:
            print(f"开始处理请求: {request.method} {request.path}")  # 调试信息
            
            # 初始化请求
            request = await self.initialize_request(request, *args, **kwargs)
            self.request = request
            self.args = args
            self.kwargs = kwargs
            
            print(f"请求数据: {request.data}")  # 调试信息
            print(f"请求用户: {request.user}")  # 调试信息
            
            # 获取处理器
            handler = await self.get_handler(request)
            print(f"处理器: {handler}")  # 调试信息
            
            # 执行处理
            try:
                response = await handler(request, *args, **kwargs)
                print(f"处理结果: {response}")  # 调试信息
            except Exception as e:
                print(f"处理异常: {str(e)}")  # 调试信息
                raise
            
            # 完成响应
            try:
                response = await self.finalize_response(request, response, *args, **kwargs)
                print(f"最终响应: {response}")  # 调试信息
                return response
            except Exception as e:
                print(f"完成响应异常: {str(e)}")  # 调试信息
                raise
            
        except Exception as e:
            print(f"请求处理异常: {str(e)}")  # 调试信息
            return await self.handle_exception(e)
    
    async def initialize_request(self, request, *args, **kwargs):
        """初始化请求"""
        try:
            if not isinstance(request, Request):
                request = Request(request)

            request.method = request.method.upper()
            if request.content_type == 'application/json' or request.content_type is None:
                request.META['CONTENT_TYPE'] = 'application/json'
                request.META['HTTP_ACCEPT'] = 'application/json'
                if request.body:
                    try:
                        data = json.loads(request.body.decode('utf-8'))
                        print(f"原始请求体: {request.body.decode('utf-8')}")  # 调试信息
                        print(f"解析后的数据: {data}")  # 调试信息
                        # 创建一个新的请求对象
                        new_request = Request(request)
                        # 设置请求属性
                        object.__setattr__(new_request, '_data', data if data is not None else Empty)
                        object.__setattr__(new_request, '_full_data', data if data is not None else Empty)
                        object.__setattr__(new_request, '_request', request)
                        object.__setattr__(new_request, 'method', request.method)
                        object.__setattr__(new_request, 'META', request.META)
                        object.__setattr__(new_request, 'user', request.user)
                        object.__setattr__(new_request, 'authenticators', request.authenticators)
                        object.__setattr__(new_request, 'successful_authenticator', request.successful_authenticator)
                        object.__setattr__(new_request, 'parser_context', {
                            'kwargs': kwargs,
                            'args': args,
                            'request': new_request,
                            'encoding': request.encoding or 'utf-8'
                        })
                        return new_request
                    except json.JSONDecodeError as e:
                        print(f"JSON解析错误: {str(e)}")  # 调试信息
                        new_request = Request(request)
                        # 设置请求属性
                        object.__setattr__(new_request, '_data', Empty)
                        object.__setattr__(new_request, '_full_data', Empty)
                        object.__setattr__(new_request, '_request', request)
                        object.__setattr__(new_request, 'method', request.method)
                        object.__setattr__(new_request, 'META', request.META)
                        object.__setattr__(new_request, 'user', request.user)
                        object.__setattr__(new_request, 'authenticators', request.authenticators)
                        object.__setattr__(new_request, 'successful_authenticator', request.successful_authenticator)
                        object.__setattr__(new_request, 'parser_context', {
                            'kwargs': kwargs,
                            'args': args,
                            'request': new_request,
                            'encoding': request.encoding or 'utf-8'
                        })
                        return new_request
                else:
                    print("请求体为空")  # 调试信息
                    new_request = Request(request)
                    # 设置请求属性
                    object.__setattr__(new_request, '_data', Empty)
                    object.__setattr__(new_request, '_full_data', Empty)
                    object.__setattr__(new_request, '_request', request)
                    object.__setattr__(new_request, 'method', request.method)
                    object.__setattr__(new_request, 'META', request.META)
                    object.__setattr__(new_request, 'user', request.user)
                    object.__setattr__(new_request, 'authenticators', request.authenticators)
                    object.__setattr__(new_request, 'successful_authenticator', request.successful_authenticator)
                    object.__setattr__(new_request, 'parser_context', {
                        'kwargs': kwargs,
                        'args': args,
                        'request': new_request,
                        'encoding': request.encoding or 'utf-8'
                    })
                    return new_request
            
            return request
        except Exception as e:
            print(f"初始化请求异常: {str(e)}")  # 调试信息
            raise
    
    @action(detail=True, methods=['post'])
    async def resolve(self, request, *args, **kwargs):
        """解决告警"""
        try:
            self.kwargs = kwargs
            alert = await self.get_object()
            alert.status = MonitorAlert.Status.RESOLVED
            await sync_to_async(alert.save)()
            
            serializer = self.get_serializer(alert)
            data = await sync_to_async(lambda: serializer.data)()
            return Response(data)
        except Exception as e:
            print(f"Error in MonitorAlertViewSet.resolve: {str(e)}")
            if settings.DEBUG:
                import traceback
                traceback.print_exc()
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    async def ignore(self, request, pk=None):
        """忽略告警"""
        try:
            alert = await self.get_object()
            alert.status = 'ignored'
            await sync_to_async(alert.save)()
            
            serializer = self.get_serializer(alert)
            data = await sync_to_async(lambda: serializer.data)()
            return Response(data)
        except Exception as e:
            import traceback
            error_msg = f"Error in MonitorAlertViewSet.ignore: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)  # 开发环境打印错误
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    async def stats(self, request):
        """获取统计信息"""
        try:
            queryset = await self.get_queryset()
            total = await sync_to_async(queryset.count)()
            active = await sync_to_async(queryset.filter(status='active').count)()
            resolved = await sync_to_async(queryset.filter(status='resolved').count)()
            ignored = await sync_to_async(queryset.filter(status='ignored').count)()
            
            return Response({
                'total': total,
                'active': active,
                'resolved': resolved,
                'ignored': ignored
            })
        except Exception as e:
            import traceback
            error_msg = f"Error in MonitorAlertViewSet.stats: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)  # 开发环境打印错误
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class SystemMetricViewSet(SyncAsyncViewSetMixin, viewsets.ModelViewSet):
    serializer_class = SystemMetricSerializer
    queryset = SystemMetric.objects.all()
    renderer_classes = [JSONRenderer]
    format_kwarg = None

    async def get_queryset(self):
        """获取查询集"""
        queryset = self.queryset.all()
        return await sync_to_async(list)(queryset.order_by('-timestamp'))

    def get_serializer(self, *args, **kwargs):
        """获取序列化器实例"""
        serializer_class = self.serializer_class
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)

    def get_serializer_context(self):
        """获取序列化器上下文"""
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }

    async def list(self, request, *args, **kwargs):
        """获取系统指标列表"""
        try:
            # 获取查询集
            queryset = await self.get_queryset()
            
            # 获取序列化器并序列化数据
            serializer = self.get_serializer(queryset, many=True)
            data = serializer.data
            
            return Response(data)
        except Exception as e:
            import traceback
            error_msg = f"Error in SystemMetricViewSet.list: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)  # 开发环境打印错误
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    async def latest(self, request):
        latest_metrics = {}
        queryset = await self.get_queryset()
        
        async for metric in queryset:
            if metric.metric_name not in latest_metrics:
                serializer = await self.get_serializer(metric)
                latest_metrics[metric.metric_name] = serializer.data
        
        return Response(list(latest_metrics.values()))

    @action(detail=False, methods=['get'])
    async def stats(self, request):
        queryset = await self.get_queryset()
        stats = await sync_to_async(lambda: queryset.values('metric_name').annotate(
            count=Count('id'),
            avg=Avg('value'),
            max=Max('value'),
            min=Min('value')
        ))()
        return Response(list(stats))

class HealthCheckView(SyncAsyncViewSetMixin, views.APIView):
    """系统健康状态检查视图"""
    renderer_classes = [JSONRenderer]
    format_kwarg = None

    async def get(self, request, *args, **kwargs):
        """获取系统健康状态"""
        try:
            service = MonitorService()
            health_status = await service.check_system_health()
            return Response(health_status)
        except Exception as e:
            print(f"健康检查失败: {str(e)}")
            return Response(
                {"status": "unhealthy", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def dispatch(self, request, *args, **kwargs):
        """分发请求"""
        try:
            print(f"开始处理请求: {request.method} {request.path}")  # 调试信息
            
            # 初始化请求
            if not isinstance(request, Request):
                request = Request(request)
            self.request = request
            self.args = args
            self.kwargs = kwargs
            
            print(f"请求数据: {request.data}")  # 调试信息
            print(f"请求用户: {request.user}")  # 调试信息
            
            # 获取处理器
            handler = getattr(self, request.method.lower(), None)
            if handler is None:
                return Response(
                    {"error": f"Method {request.method} not allowed"},
                    status=status.HTTP_405_METHOD_NOT_ALLOWED
                )
            print(f"处理器: {handler}")  # 调试信息
            
            # 执行处理
            try:
                response = await handler(request, *args, **kwargs)
                print(f"处理结果: {response}")  # 调试信息
                return response
            except Exception as e:
                print(f"处理异常: {str(e)}")  # 调试信息
                raise
            
        except Exception as e:
            print(f"请求处理异常: {str(e)}")  # 调试信息
            return Response(
                {"status": "unhealthy", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class HealthReportView(SyncAsyncViewSetMixin, views.APIView):
    """系统健康报告视图"""
    renderer_classes = [JSONRenderer]
    format_kwarg = None

    async def get(self, request, *args, **kwargs):
        """获取系统健康报告"""
        try:
            service = MonitorService()
            report = await service.generate_health_report()
            return Response(report)
        except Exception as e:
            print(f"生成健康报告失败: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def dispatch(self, request, *args, **kwargs):
        """分发请求"""
        try:
            response = await super().dispatch(request, *args, **kwargs)
            return response
        except Exception as e:
            print(f"请求处理异常: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ErrorLogViewSet(SyncAsyncViewSetMixin, viewsets.ModelViewSet):
    serializer_class = ErrorLogSerializer
    queryset = ErrorLog.objects.all()
    renderer_classes = [JSONRenderer]
    format_kwarg = None
    
    @action(detail=False, methods=['get'])
    async def stats(self, request):
        period = request.query_params.get('period', '24h')
        
        if period == '24h':
            start_time = timezone.now() - timedelta(hours=24)
        elif period == '7d':
            start_time = timezone.now() - timedelta(days=7)
        else:
            start_time = timezone.now() - timedelta(hours=24)
            
        queryset = self.get_queryset().filter(timestamp__gte=start_time)
        stats = await self.annotate_queryset_async(
            queryset.values('level'),
            count=Count('id')
        )
        
        return Response(stats) 