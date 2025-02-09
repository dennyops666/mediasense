from .base import BaseCrawler
import logging
import requests
import json
import re
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
from django.utils import timezone
from datetime import datetime
import dateutil.parser
from ..exceptions import FetchError, ParseError
import time
import concurrent.futures
from functools import wraps
import copy

logger = logging.getLogger(__name__)

def rate_limit(func):
    """请求频率限制装饰器"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        rate_limit_config = self.config.config_data.get('rate_limit', {})
        if rate_limit_config:
            requests_limit = rate_limit_config.get('requests', 1)
            time_window = rate_limit_config.get('per_seconds', 1)
            
            current_time = time.time()
            if hasattr(self, '_last_request_time'):
                elapsed = current_time - self._last_request_time
                if elapsed < time_window / requests_limit:
                    sleep_time = time_window / requests_limit - elapsed
                    logger.debug(f"频率限制: 休眠 {sleep_time:.2f} 秒")
                    time.sleep(sleep_time)
                    
            self._last_request_time = time.time()
            
        return func(self, *args, **kwargs)
    return wrapper

class APICrawler(BaseCrawler):
    """API爬虫基类"""

    def __init__(self, config):
        """初始化API爬虫"""
        super().__init__(config)
        self.headers = config.headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }
        
        # 设置压缩支持
        if self.config.config_data.get('compression'):
            self.headers['Accept-Encoding'] = 'gzip, deflate'
            
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # 设置代理
        if 'proxy' in self.config.config_data:
            self.session.proxies = self.config.config_data['proxy']
            
        # 设置其他会话参数
        if 'verify' in self.config.config_data:
            self.session.verify = self.config.config_data['verify']
            
        if 'cookies' in self.config.config_data:
            self.session.cookies.update(self.config.config_data['cookies'])
            
        self._cache = {}
        self._last_request_time = 0

    def _prepare_request_kwargs(self) -> Dict[str, Any]:
        """
        准备请求参数
        :return: 请求参数字典
        """
        kwargs = {
            'timeout': 30,  # 默认超时
            'allow_redirects': True,
            'headers': self.headers.copy()  # 添加默认请求头
        }
        
        # 处理请求参数
        params = self.config.config_data.get('params', {})
        if params:
            kwargs['params'] = params
        
        # 处理超时设置
        timeout_config = self.config.config_data.get('timeout')
        if isinstance(timeout_config, dict):
            kwargs['timeout'] = (
                timeout_config.get('connect', 5),
                timeout_config.get('read', 30)
            )
        elif isinstance(timeout_config, (int, float)):
            kwargs['timeout'] = timeout_config
            
        # 处理重定向设置
        if 'max_redirects' in self.config.config_data:
            kwargs['max_redirects'] = self.config.config_data['max_redirects']
            
        # 处理流式传输
        if 'stream' in self.config.config_data:
            kwargs['stream'] = self.config.config_data['stream']
            
        return kwargs

    @rate_limit
    def fetch_data(self) -> Dict[str, Any]:
        """
        获取API数据
        :return: 包含状态和数据的字典
        :raises: FetchError 当获取数据失败时
        """
        try:
            logger.info(f"开始获取API数据: {self.source_url}")
            
            # 检查缓存
            cache_config = self.config.config_data.get('cache', {})
            if cache_config.get('enabled'):
                cache_key = self.source_url
                cache_data = self._cache.get(cache_key)
                if cache_data:
                    cache_time = cache_data.get('timestamp', 0)
                    if time.time() - cache_time < cache_config.get('ttl', 300):
                        logger.info("使用缓存数据")
                        return cache_data
            
            # 准备请求参数
            kwargs = self._prepare_request_kwargs()
            method = self.config.config_data.get('method', 'GET').upper()
            
            # 处理动态请求头
            dynamic_headers = self.config.config_data.get('dynamic_headers', {})
            if dynamic_headers:
                for key, value in dynamic_headers.items():
                    if isinstance(value, str):
                        kwargs['headers'][key] = value
                    elif callable(value):
                        try:
                            kwargs['headers'][key] = value()
                        except Exception as e:
                            logger.error(f"生成动态请求头失败: {str(e)}")
            
            # 发送请求
            if method == 'POST':
                kwargs['json'] = self.config.config_data.get('body', {})
                if 'params' in kwargs and not kwargs['params']:
                    del kwargs['params']
                response = self.session.post(self.source_url, **kwargs)
            else:
                response = self.session.get(self.source_url, **kwargs)
                
            response.raise_for_status()
            
            # 处理响应编码
            if response.encoding == 'ISO-8859-1':
                response.encoding = response.apparent_encoding
            
            try:
                result = {
                    'status': 'success',
                    'message': '成功获取API数据',
                    'data': response.json(),
                    'timestamp': time.time()
                }
                
                # 验证响应
                if not self._validate_response(result['data']):
                    return {
                        'status': 'error',
                        'message': '响应验证失败',
                        'data': []
                    }
                
                # 更新缓存
                if cache_config.get('enabled'):
                    self._cache[cache_key] = result
                    
                return result
                
            except (json.JSONDecodeError, ValueError):
                # 尝试从JavaScript中提取JSON
                pattern = r'({[^{]*?"newsstream":[^}]*?})'
                match = re.search(pattern, response.text)
                if match:
                    try:
                        return {
                            'status': 'success',
                            'message': '成功从JavaScript中提取JSON数据',
                            'data': json.loads(match.group(1))
                        }
                    except json.JSONDecodeError as e:
                        error_msg = f"解析JSON数据失败: {str(e)}"
                        logger.error(error_msg)
                        return {
                            'status': 'error',
                            'message': error_msg,
                            'data': []
                        }
                else:
                    error_msg = "解析JSON数据失败: 未找到有效的JSON数据"
                    logger.error(error_msg)
                    return {
                        'status': 'error',
                        'message': error_msg,
                        'data': []
                    }
                    
        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求失败: {str(e)}"
            logger.error(error_msg)
            return {
                'status': 'error',
                'message': error_msg,
                'data': []
            }
        except Exception as e:
            error_msg = f"获取API数据失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'status': 'error',
                'message': error_msg,
                'data': []
            }

    def parse_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        解析API响应数据
        :param data: fetch_data返回的数据字典
        :return: 解析后的文章列表
        :raises: ParseError 当解析数据失败时
        """
        try:
            logger.info("开始解析API数据")
            
            if data.get('status') != 'success' or not data.get('data'):
                logger.error(f"获取API数据失败: {data.get('message')}")
                return []
                
            # 获取数据路径
            data_path = self.config.config_data.get('data_path', '')
            if not data_path:
                logger.error(f'数据路径未配置: {self.source_name}')
                return []
                
            # 根据数据路径获取新闻列表
            news_list = data['data']
            for key in data_path.split('.'):
                if not isinstance(news_list, dict):
                    logger.error(f'无效的数据路径: {data_path}, 当前值: {news_list}')
                    return []
                news_list = news_list.get(key, {})
                
            if not isinstance(news_list, list):
                news_list = [news_list] if news_list else []
                
            # 解析每条新闻
            articles = []
            for item in news_list:
                try:
                    if not isinstance(item, dict):
                        continue
                        
                    # 获取字段值
                    title = self._get_field_value(item, self.config.config_data.get('title_path'))
                    if not title:
                        logger.warning("跳过无标题文章")
                        continue
                        
                    url = self._get_field_value(item, self.config.config_data.get('link_path'))
                    if not url or not url.startswith(('http://', 'https://')):
                        logger.warning(f"跳过无效URL: {url}")
                        continue
                        
                    author = self._get_field_value(item, self.config.config_data.get('author_path'))
                    source = self._get_field_value(item, self.config.config_data.get('source_path'))
                    pub_time = self._get_field_value(item, self.config.config_data.get('pub_time_path'))
                    content = self._get_field_value(item, self.config.config_data.get('content_path'))
                    description = self._get_field_value(item, self.config.config_data.get('description_path'))
                    
                    # 获取新闻详情
                    if not content and url:
                        try:
                            detail_response = self.session.get(url, timeout=30)
                            detail_response.raise_for_status()
                            detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
                            
                            # 使用选择器获取内容
                            content_selector = self.config.config_data.get('content_selector')
                            if content_selector:
                                content_elem = detail_soup.select_one(content_selector)
                                if content_elem:
                                    content = content_elem.get_text(separator='\n').strip()
                                    
                        except Exception as e:
                            logger.error(f'获取新闻详情失败: {str(e)}', exc_info=True)
                            
                    # 构建文章数据
                    article = {
                        'title': title,
                        'url': url,
                        'content': content or description or '',
                        'description': description or '',
                        'author': author or '',
                        'source': source or self.source_name,
                        'pub_time': self._parse_datetime(pub_time) if pub_time else timezone.now(),
                        'tags': [],
                        'images': []
                    }
                    
                    # 验证内容长度
                    min_length = self.config.config_data.get('validation', {}).get('min_content_length', 0)
                    if min_length and len(article['content']) < min_length:
                        logger.warning(f"跳过内容长度不足的文章: {article['title']}")
                        continue
                    
                    articles.append(article)
                    logger.debug(f"成功解析文章: {article['title']}")
                        
                except Exception as e:
                    logger.error(f"解析文章失败: {str(e)}", exc_info=True)
                    continue
                    
            logger.info(f"API解析完成，共获取{len(articles)}篇文章")
            return articles
            
        except Exception as e:
            error_msg = f"API解析失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return []
            
    def _get_field_value(self, data: Dict[str, Any], path: Optional[str]) -> Any:
        """
        根据路径获取字段值
        :param data: 数据字典
        :param path: 字段路径，使用点号分隔，支持数组索引如 'items[0].title'
        :return: 字段值，如果路径无效则返回None
        """
        if not path:
            return None
            
        try:
            value = data
            parts = re.split(r'\.|\[|\]', path)
            parts = [p for p in parts if p]  # 移除空字符串
            
            for part in parts:
                if part.isdigit():  # 处理数组索引
                    index = int(part)
                    if not isinstance(value, (list, tuple)) or index >= len(value):
                        return None
                    value = value[index]
                else:  # 处理字典键
                    if not isinstance(value, dict):
                        return None
                    value = value.get(part)
                    if value is None:
                        return None
            return value
            
        except Exception as e:
            logger.error(f"获取字段值失败: {str(e)}", exc_info=True)
            return None

    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """
        解析日期时间字符串
        :param date_str: 日期时间字符串
        :return: datetime对象，如果解析失败则返回None
        """
        if not date_str:
            return None
            
        try:
            return dateutil.parser.parse(date_str)
        except (ValueError, TypeError):
            try:
                # 尝试常见的日期格式
                formats = [
                    '%Y-%m-%dT%H:%M:%SZ',  # ISO格式
                    '%Y-%m-%d %H:%M:%S',   # 标准格式
                    '%Y/%m/%d %H:%M:%S',   # 斜线分隔
                    '%Y-%m-%d',            # 仅日期
                    '%Y/%m/%d',            # 仅日期（斜线）
                ]
                
                for fmt in formats:
                    try:
                        return datetime.strptime(date_str, fmt)
                    except ValueError:
                        continue
                        
                return None
            except Exception:
                return None

    def _validate_response(self, data: Dict[str, Any]) -> bool:
        """
        验证响应数据
        :param data: 响应数据
        :return: 验证是否通过
        """
        validation = self.config.config_data.get('validation', {})
        if not validation:
            return True
            
        try:
            # 获取数据路径
            data_path = self.config.config_data.get('data_path', '')
            if not data_path:
                return True
                
            # 根据数据路径获取新闻列表
            items = data
            for key in data_path.split('.'):
                if not isinstance(items, dict):
                    return True
                items = items.get(key, {})
                
            if not isinstance(items, list):
                items = [items]
                
            # 检查数量限制
            max_items = validation.get('max_items')
            if max_items and len(items) > max_items:
                logger.error(f"数据项数量超过限制: {len(items)} > {max_items}")
                return False
                
            # 检查必需字段
            required_fields = validation.get('required_fields', [])
            for item in items:
                if not isinstance(item, dict):
                    continue
                for field in required_fields:
                    if not self._get_field_value(item, field):
                        logger.error(f"缺少必需字段: {field}")
                        return False
                        
            # 检查内容长度
            min_length = validation.get('min_content_length')
            if min_length:
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    content = self._get_field_value(item, self.config.config_data.get('content_path', '')) or ''
                    if len(content) < min_length:
                        logger.error(f"内容长度不足: {len(content)} < {min_length}")
                        return False
                        
            return True
            
        except Exception as e:
            logger.error(f"响应验证失败: {str(e)}", exc_info=True)
            return True  # 如果验证过程出错，返回True以允许继续处理

    def _process_concurrent_requests(self, max_workers: int) -> Dict[str, Any]:
        """
        处理并发请求
        :param max_workers: 最大工作线程数
        :return: 包含状态和数据的字典
        """
        # 处理无效的max_workers
        if max_workers <= 0:
            logger.warning(f"无效的max_workers值: {max_workers}，使用默认单线程模式")
            return self.fetch_data()
            
        all_items = []
        success_count = 0
        errors = []
        
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = []
                # 创建多个不同的请求参数
                for i in range(max_workers):
                    # 复制配置并添加worker_id
                    worker_kwargs = self._prepare_request_kwargs()
                    if 'params' not in worker_kwargs:
                        worker_kwargs['params'] = {}
                    worker_kwargs['params']['worker_id'] = i
                    
                    # 提交任务
                    future = executor.submit(self._make_request, worker_kwargs)
                    futures.append(future)
                    
                # 收集结果
                for future in concurrent.futures.as_completed(futures):
                    try:
                        result = future.result()
                        if result['status'] == 'success':
                            items = self.parse_response(result)
                            if items:
                                all_items.extend(items)
                                success_count += 1
                        else:
                            errors.append(result['message'])
                    except Exception as e:
                        errors.append(str(e))
                        logger.error(f"并发请求失败: {str(e)}", exc_info=True)
                        
            # 返回结果
            if success_count > 0:
                return {
                    'status': 'success',
                    'message': f'成功获取并解析{success_count}个并发请求的数据',
                    'data': all_items
                }
            else:
                error_msg = '所有并发请求均失败: ' + '; '.join(errors)
                return {
                    'status': 'error',
                    'message': error_msg,
                    'data': []
                }
                
        except Exception as e:
            error_msg = f"并发请求处理失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'status': 'error',
                'message': error_msg,
                'data': []
            }

    def _retry_request(self, func, *args, **kwargs) -> Dict[str, Any]:
        """
        执行带重试的请求
        :param func: 要执行的函数
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 请求结果
        """
        retry_config = self.config.config_data.get('retry', {})
        max_attempts = retry_config.get('max_attempts', 1)
        delay = retry_config.get('delay', 0)
        
        last_error = None
        for attempt in range(max_attempts):
            try:
                if attempt > 0:
                    logger.info(f"第{attempt + 1}次重试, 延迟{delay}秒")
                    time.sleep(delay)
                    
                result = func(*args, **kwargs)
                if result['status'] == 'success':
                    return result
                last_error = result
                    
            except Exception as e:
                logger.error(f"请求失败: {str(e)}", exc_info=True)
                last_error = {
                    'status': 'error',
                    'message': str(e),
                    'data': []
                }
                
        return last_error or {
            'status': 'error',
            'message': '所有重试均失败',
            'data': []
        }
        
    def run(self) -> Dict[str, Any]:
        """
        运行爬虫
        :return: 包含状态和数据的字典
        """
        try:
            # 处理分页
            pagination = self.config.config_data.get('pagination', {})
            if pagination.get('enabled'):
                all_items = []
                current_page = pagination.get('start_page', 1)
                max_pages = pagination.get('max_pages', 1)
                page_param = pagination.get('page_param', 'page')
                size_param = pagination.get('size_param', 'size')
                page_size = pagination.get('page_size', 20)
                
                # 保存原始参数
                original_params = self.config.config_data.get('params', {}).copy()
                
                try:
                    while current_page <= max_pages:
                        # 更新分页参数
                        if 'params' not in self.config.config_data:
                            self.config.config_data['params'] = {}
                        self.config.config_data['params'][page_param] = current_page
                        if size_param:
                            self.config.config_data['params'][size_param] = page_size
                        
                        # 获取当前页数据
                        page_result = self._retry_request(self.fetch_data)
                        if page_result['status'] != 'success':
                            break
                            
                        # 解析数据
                        items = self.parse_response(page_result)
                        if not items:
                            break
                            
                        all_items.extend(items)
                        current_page += 1
                        
                        # 检查是否有更多数据
                        if not pagination.get('has_more_data', True):
                            break
                        
                    if all_items:
                        return {
                            'status': 'success',
                            'message': '成功获取并解析分页数据',
                            'data': all_items
                        }
                    else:
                        return {
                            'status': 'error',
                            'message': '未获取到有效文章',
                            'data': []
                        }
                finally:
                    # 恢复原始参数
                    self.config.config_data['params'] = original_params
            
            # 处理并发请求
            concurrency = self.config.config_data.get('concurrency', {})
            if concurrency.get('enabled'):
                max_workers = concurrency.get('max_workers', 3)
                return self._process_concurrent_requests(max_workers)
            
            # 执行带重试的请求
            result = self._retry_request(self.fetch_data)
            if result['status'] != 'success':
                return result
            
            # 解析数据
            articles = self.parse_response(result)
            if not articles:
                return {
                    'status': 'error',
                    'message': '未获取到有效文章',
                    'data': []
                }
            
            # 返回结果
            return {
                'status': 'success',
                'message': '成功获取并解析API数据',
                'data': articles
            }
            
        except Exception as e:
            error_msg = f"API爬虫运行失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'status': 'error',
                'message': error_msg,
                'data': []
            }

    def _make_request(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行单个请求
        :param kwargs: 请求参数
        :return: 请求结果
        """
        try:
            method = self.config.config_data.get('method', 'GET').upper()
            
            # 发送请求
            if method == 'POST':
                kwargs['json'] = self.config.config_data.get('body', {})
                if 'params' in kwargs and not kwargs['params']:
                    del kwargs['params']
                response = self.session.post(self.source_url, **kwargs)
            else:
                response = self.session.get(self.source_url, **kwargs)
                
            response.raise_for_status()
            
            # 处理响应编码
            if response.encoding == 'ISO-8859-1':
                response.encoding = response.apparent_encoding
            
            try:
                result = {
                    'status': 'success',
                    'message': '成功获取API数据',
                    'data': response.json(),
                    'timestamp': time.time()
                }
                
                # 验证响应
                if not self._validate_response(result['data']):
                    return {
                        'status': 'error',
                        'message': '响应验证失败',
                        'data': []
                    }
                    
                return result
                
            except json.JSONDecodeError as e:
                error_msg = f"解析JSON数据失败: {str(e)}"
                logger.error(error_msg)
                return {
                    'status': 'error',
                    'message': error_msg,
                    'data': []
                }
                
        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求失败: {str(e)}"
            logger.error(error_msg)
            return {
                'status': 'error',
                'message': error_msg,
                'data': []
            }
        except Exception as e:
            error_msg = f"请求处理失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'status': 'error',
                'message': error_msg,
                'data': []
            } 