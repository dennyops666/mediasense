import pytest
from django.test import TestCase
from unittest.mock import patch, MagicMock, call
from django.utils import timezone
from crawler.crawlers.api_crawler import APICrawler
from crawler.models import CrawlerConfig
import requests
import json
from datetime import datetime
import time

class TestAPICrawler(TestCase):
    """API爬虫测试类"""
    
    def setUp(self):
        """测试初始化"""
        self.config = CrawlerConfig.objects.create(
            name='测试API源',
            crawler_type=2,  # API类型
            source_url='https://api.test.com/news',
            status=1,
            is_active=True,
            interval=60,
            config_data={
                'data_path': 'data.data.items',
                'title_path': 'title',
                'link_path': 'url',
                'author_path': 'author',
                'pub_time_path': 'published_at',
                'content_path': 'content',
                'description_path': 'summary',
                'method': 'GET',
                'params': {
                    'page': 1,
                    'size': 20
                },
                'validation': {
                    'required_fields': ['title', 'url'],
                    'min_content_length': 10
                }
            }
        )
        self.crawler = APICrawler(self.config)

    def test_init_headers(self):
        """测试初始化请求头"""
        # 测试默认请求头
        self.assertIn('User-Agent', self.crawler.headers)
        self.assertIn('Accept', self.crawler.headers)
        self.assertEqual(self.crawler.headers['Accept'], 'application/json')
        
        # 测试自定义请求头
        custom_headers = {
            'User-Agent': 'Custom Agent',
            'Authorization': 'Bearer token123'
        }
        config = CrawlerConfig.objects.create(
            name='测试自定义头部',
            crawler_type=2,
            source_url='https://api.test.com/news',
            headers=custom_headers
        )
        crawler = APICrawler(config)
        self.assertEqual(crawler.headers['User-Agent'], 'Custom Agent')
        self.assertEqual(crawler.headers['Authorization'], 'Bearer token123')

    @patch('requests.Session.get')
    def test_fetch_data_success(self, mock_get):
        """测试成功获取API数据"""
        # Mock响应数据
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {
                'items': [
                    {
                        'title': '测试文章',
                        'url': 'https://test.com/article/1',
                        'author': '测试作者',
                        'published_at': '2024-03-20T10:00:00Z',
                        'content': '测试内容',
                        'summary': '测试摘要'
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        # 执行测试
        result = self.crawler.fetch_data()
        
        # 验证结果
        self.assertEqual(result['status'], 'success')
        self.assertIsNotNone(result['data'])
        self.assertIn('items', result['data']['data'])
        
    @patch('requests.Session.get')
    def test_fetch_data_network_error(self, mock_get):
        """测试网络错误情况"""
        # 测试不同类型的网络错误
        error_cases = [
            requests.exceptions.ConnectionError('连接错误'),
            requests.exceptions.Timeout('请求超时'),
            requests.exceptions.RequestException('网络连接失败')
        ]
        
        for error in error_cases:
            mock_get.side_effect = error
            result = self.crawler.fetch_data()
            self.assertEqual(result['status'], 'error')
            self.assertIn('网络请求失败', result['message'])
            self.assertEqual(result['data'], [])

    @patch('requests.Session.get')
    def test_fetch_data_http_error(self, mock_get):
        """测试HTTP错误响应"""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError('404 Client Error')
        mock_get.return_value = mock_response

        result = self.crawler.fetch_data()
        self.assertEqual(result['status'], 'error')
        self.assertIn('网络请求失败', result['message'])
        self.assertEqual(result['data'], [])

    @patch('requests.Session.get')
    def test_fetch_data_invalid_json(self, mock_get):
        """测试无效JSON响应"""
        # 测试各种无效JSON情况
        test_cases = [
            ('invalid json data', '解析JSON数据失败'),
            ('{"incomplete": "json"', '解析JSON数据失败'),
            ('[]', '解析JSON数据失败')
        ]
        
        for test_data, expected_message in test_cases:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.side_effect = ValueError('无效的JSON数据')
            mock_response.text = test_data
            mock_get.return_value = mock_response

            result = self.crawler.fetch_data()
            self.assertEqual(result['status'], 'error')
            self.assertIn(expected_message, result['message'])
            self.assertEqual(result['data'], [])

    def test_parse_response_success(self):
        """测试成功解析响应数据"""
        test_data = {
            'status': 'success',
            'data': {
                'data': {
                    'items': [
                        {
                            'title': '测试文章',
                            'url': 'https://test.com/article/1',
                            'author': '测试作者',
                            'published_at': '2024-03-20T10:00:00Z',
                            'content': '测试内容' * 10,
                            'summary': '测试摘要'
                        }
                    ]
                }
            }
        }

        articles = self.crawler.parse_response(test_data)
        self.assertEqual(len(articles), 1)
        article = articles[0]
        self.assertEqual(article['title'], '测试文章')
        self.assertEqual(article['url'], 'https://test.com/article/1')
        self.assertEqual(article['author'], '测试作者')
        self.assertEqual(article['content'], '测试内容' * 10)
        self.assertEqual(article['description'], '测试摘要')

    def test_parse_response_data_validation(self):
        """测试数据验证"""
        # 测试各种数据验证场景
        test_cases = [
            # 空数据
            {'status': 'success', 'data': None},
            # 无效的数据路径
            {'status': 'success', 'data': {'wrong_path': []}},
            # 无效的数据类型
            {'status': 'success', 'data': {'data': {'items': 'not_a_list'}}},
            # 缺少必需字段
            {'status': 'success', 'data': {'data': {'items': [{}]}}},
            # 无效的URL格式
            {'status': 'success', 'data': {'data': {'items': [{'title': 'test', 'url': 'invalid_url'}]}}}
        ]
        
        for test_data in test_cases:
            articles = self.crawler.parse_response(test_data)
            self.assertEqual(len(articles), 0)

    def test_get_field_value(self):
        """测试字段值获取"""
        test_data = {
            'nested': {
                'field': {
                    'value': 'test'
                }
            },
            'array': ['item1', 'item2'],
            'simple': 'value'
        }
        
        # 测试各种路径
        self.assertEqual(
            self.crawler._get_field_value(test_data, 'nested.field.value'),
            'test'
        )
        self.assertEqual(
            self.crawler._get_field_value(test_data, 'array[0]'),
            'item1'
        )
        self.assertEqual(
            self.crawler._get_field_value(test_data, 'simple'),
            'value'
        )
        
        # 测试无效路径
        self.assertIsNone(self.crawler._get_field_value(test_data, 'invalid.path'))
        self.assertIsNone(self.crawler._get_field_value(test_data, 'array[99]'))
        self.assertIsNone(self.crawler._get_field_value(test_data, None))

    def test_run_with_retry(self):
        """测试带重试的运行"""
        with patch.object(APICrawler, 'fetch_data') as mock_fetch:
            # 模拟第一次失败，第二次成功
            mock_fetch.side_effect = [
                {'status': 'error', 'message': '网络错误', 'data': []},
                {
                    'status': 'success',
                    'data': {'data': {'items': [{'title': '测试', 'url': 'https://test.com'}]}}
                }
            ]
            
            result = self.crawler.run()
            self.assertEqual(result['status'], 'error')
            
            result = self.crawler.run()
            self.assertEqual(result['status'], 'success')
            self.assertEqual(len(result['data']), 1)

    def test_parse_datetime(self):
        """测试日期时间解析"""
        # 测试各种日期时间格式
        test_cases = [
            ('2024-03-20T10:00:00Z', True),
            ('2024-03-20 10:00:00', True),
            ('2024/03/20', True),
            ('invalid_date', False),
            ('', False),
            (None, False)
        ]
        
        for date_str, should_succeed in test_cases:
            try:
                result = self.crawler._parse_datetime(date_str) if hasattr(self.crawler, '_parse_datetime') else None
                if should_succeed:
                    self.assertIsInstance(result, datetime)
                else:
                    self.assertIsNone(result)
            except Exception as e:
                if should_succeed:
                    self.fail(f"日期解析失败: {date_str}, 错误: {str(e)}")

    def _get_field_value(self, data, path):
        """辅助方法：获取字段值"""
        if not path:
            return None
            
        try:
            value = data
            for key in path.split('.'):
                if key.startswith('[') and key.endswith(']'):
                    index = int(key[1:-1])
                    if not isinstance(value, (list, tuple)) or index >= len(value):
                        return None
                    value = value[index]
                else:
                    if not isinstance(value, dict):
                        return None
                    value = value.get(key)
                    if value is None:
                        return None
            return value
        except Exception:
            return None

    def test_post_request(self):
        """测试POST请求"""
        # 配置POST请求
        self.config.config_data['method'] = 'POST'
        self.config.config_data['body'] = {
            'query': 'test',
            'filters': {'category': 'news'}
        }
        self.config.config_data['params'] = {}  # 清空params
        self.config.save()
        
        with patch('requests.Session.post') as mock_post:
            # Mock响应
            mock_response = MagicMock(
                status_code=200,
                json=lambda: {
                    'data': {
                        'data': {
                            'items': [{
                                'title': 'POST测试文章',
                                'url': 'https://test.com/article/1',
                                'content': '测试内容' * 10
                            }]
                        }
                    }
                }
            )
            mock_post.return_value = mock_response
            
            # 执行请求
            result = self.crawler.fetch_data()
            
            # 验证结果
            self.assertEqual(result['status'], 'success')
            self.assertEqual(
                result['data']['data']['items'][0]['title'],
                'POST测试文章'
            )
            
            # 验证请求参数
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            self.assertEqual(call_args.args[0], self.config.source_url)
            self.assertEqual(call_args.kwargs['json'], self.config.config_data['body'])
            self.assertEqual(call_args.kwargs['timeout'], 30)
            self.assertTrue(call_args.kwargs['allow_redirects'])

    def test_rate_limiting(self):
        """测试请求频率限制"""
        # 配置频率限制
        self.config.config_data['rate_limit'] = {
            'requests': 2,  # 每秒最多2个请求
            'per_seconds': 1
        }
        self.config.save()
        
        with patch('time.sleep') as mock_sleep, \
             patch('requests.Session.get') as mock_get:
            # Mock响应
            mock_response = MagicMock(
                status_code=200,
                json=lambda: {
                    'data': {
                        'data': {
                            'items': [{
                                'title': '测试文章',
                                'url': 'https://test.com/article/1',
                                'content': '测试内容' * 10
                            }]
                        }
                    }
                }
            )
            mock_get.return_value = mock_response
            
            # 连续发送3个请求
            start_time = time.time()
            self.crawler._last_request_time = start_time
            
            # 第一个请求
            result1 = self.crawler.fetch_data()
            self.assertEqual(result1['status'], 'success')
            self.assertEqual(mock_sleep.call_count, 0)  # 第一个请求不需要延迟
            
            # 第二个请求
            result2 = self.crawler.fetch_data()
            self.assertEqual(result2['status'], 'success')
            self.assertEqual(mock_sleep.call_count, 1)  # 第二个请求需要延迟
            
            # 第三个请求
            result3 = self.crawler.fetch_data()
            self.assertEqual(result3['status'], 'success')
            self.assertEqual(mock_sleep.call_count, 2)  # 第三个请求需要延迟
            
            # 验证延迟时间
            expected_delay = 1 / 2  # 每秒2个请求，所以间隔是0.5秒
            for call in mock_sleep.call_args_list:
                delay = call.args[0]
                self.assertAlmostEqual(delay, expected_delay, places=1)

    def test_pagination(self):
        """测试分页请求"""
        # 配置分页
        self.config.config_data['pagination'] = {
            'enabled': True,
            'start_page': 1,
            'max_pages': 3,
            'page_param': 'page',
            'size_param': 'size',
            'page_size': 10,
            'has_more_data': True
        }
        self.config.save()
        
        with patch('requests.Session.get') as mock_get:
            # Mock响应
            def get_page_response(page):
                return MagicMock(
                    status_code=200,
                    json=lambda: {
                        'data': {
                            'data': {
                                'items': [{
                                    'title': f'文章{page}',
                                    'url': f'https://test.com/article/{page}',
                                    'content': f'内容{page}' * 10
                                }]
                            }
                        }
                    }
                )
                
            mock_get.side_effect = [get_page_response(i) for i in range(1, 4)]
            
            # 执行请求
            result = self.crawler.run()
            
            # 验证结果
            self.assertEqual(result['status'], 'success')
            self.assertEqual(len(result['data']), 3)  # 3页数据
            
            # 验证分页参数
            calls = mock_get.call_args_list
            self.assertEqual(len(calls), 3)  # 应该发起3次请求
            
            for i, call in enumerate(calls, start=1):
                params = call.kwargs['params']
                self.assertEqual(params['page'], i)  # 页码正确
                self.assertEqual(params['size'], 10)  # 每页大小正确
                
            # 验证数据内容
            for i, article in enumerate(result['data'], start=1):
                self.assertEqual(article['title'], f'文章{i}')
                self.assertEqual(article['url'], f'https://test.com/article/{i}')
                self.assertTrue(len(article['content']) >= 10)

    @patch('requests.Session.get')
    def test_custom_headers_per_request(self, mock_get):
        """测试每次请求的自定义头部"""
        # 配置动态头部
        current_time = str(int(time.time()))
        current_token = f"token_{current_time}"
        
        self.config.config_data['dynamic_headers'] = {
            'X-Request-Time': current_time,
            'X-Custom-Token': current_token
        }
        self.config.config_data['validation'] = {
            'required_fields': ['title', 'url'],
            'min_content_length': 10
        }
        self.config.save()
        
        # Mock响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {
                'data': {
                    'items': [
                        {
                            'title': '测试文章',
                            'url': 'https://test.com/article/1',
                            'content': '测试内容' * 10
                        }
                    ]
                }
            }
        }
        mock_get.return_value = mock_response
        
        # 执行请求
        result = self.crawler.fetch_data()
        
        # 验证结果
        self.assertEqual(result['status'], 'success')
        
        # 验证请求头
        actual_headers = mock_get.call_args.kwargs['headers']
        self.assertEqual(actual_headers['X-Request-Time'], current_time)
        self.assertEqual(actual_headers['X-Custom-Token'], current_token)

    def test_response_caching(self):
        """测试响应缓存"""
        # 配置缓存
        self.config.config_data['cache'] = {
            'enabled': True,
            'ttl': 300  # 5分钟
        }
        self.config.config_data['validation'] = {
            'required_fields': ['title', 'url'],
            'min_content_length': 10
        }
        self.config.save()
        
        with patch('requests.Session.get') as mock_get:
            # Mock响应
            mock_response = MagicMock(
                status_code=200,
                json=lambda: {
                    'data': {
                        'data': {
                            'items': [{
                                'title': '测试文章',
                                'url': 'https://test.com/article/1',
                                'content': '测试内容' * 10
                            }]
                        }
                    }
                }
            )
            mock_get.return_value = mock_response
            
            # 第一次请求
            result1 = self.crawler.fetch_data()
            self.assertEqual(result1['status'], 'success')
            self.assertEqual(mock_get.call_count, 1)
            
            # 第二次请求应该使用缓存
            result2 = self.crawler.fetch_data()
            self.assertEqual(result2['status'], 'success')
            self.assertEqual(mock_get.call_count, 1)  # 请求次数不变
            
            # 验证两次结果相同
            self.assertEqual(
                result1['data']['data']['items'][0]['title'],
                result2['data']['data']['items'][0]['title']
            )

    def test_retry_mechanism(self):
        """测试重试机制"""
        # 配置重试
        self.config.config_data['retry'] = {
            'max_attempts': 3,
            'delay': 1
        }
        self.config.save()
        
        with patch('time.sleep') as mock_sleep, \
             patch.object(APICrawler, 'fetch_data') as mock_fetch:
            # 模拟前两次失败，第三次成功
            mock_fetch.side_effect = [
                {'status': 'error', 'message': '第一次失败', 'data': []},
                {'status': 'error', 'message': '第二次失败', 'data': []},
                {
                    'status': 'success',
                    'data': {
                        'data': {
                            'items': [
                                {
                                    'title': '测试文章',
                                    'url': 'https://test.com/article/1',
                                    'content': '测试内容' * 10
                                }
                            ]
                        }
                    }
                }
            ]
            
            # 执行测试
            result = self.crawler.run()
            
            # 验证结果
            self.assertEqual(result['status'], 'success')
            self.assertEqual(len(result['data']), 1)
            self.assertEqual(result['data'][0]['title'], '测试文章')
            
            # 验证重试次数
            self.assertEqual(mock_fetch.call_count, 3)
            
            # 验证延迟调用
            self.assertEqual(mock_sleep.call_count, 2)  # 第二次和第三次请求前应该有延迟
            mock_sleep.assert_called_with(1)  # 验证延迟时间
            
    def test_retry_all_failed(self):
        """测试所有重试都失败的情况"""
        # 配置重试
        self.config.config_data['retry'] = {
            'max_attempts': 3,
            'delay': 1
        }
        self.config.save()
        
        with patch('time.sleep') as mock_sleep, \
             patch.object(APICrawler, 'fetch_data') as mock_fetch:
            # 模拟所有请求都失败
            mock_fetch.side_effect = [
                {'status': 'error', 'message': f'第{i}次失败', 'data': []}
                for i in range(1, 4)
            ]
            
            # 执行测试
            result = self.crawler.run()
            
            # 验证结果
            self.assertEqual(result['status'], 'error')
            self.assertEqual(result['message'], '第3次失败')
            self.assertEqual(result['data'], [])
            
            # 验证重试次数
            self.assertEqual(mock_fetch.call_count, 3)
            
            # 验证延迟调用
            self.assertEqual(mock_sleep.call_count, 2)
            mock_sleep.assert_called_with(1)
            
    def test_retry_with_exception(self):
        """测试重试过程中发生异常的情况"""
        # 配置重试
        self.config.config_data['retry'] = {
            'max_attempts': 3,
            'delay': 1
        }
        self.config.save()
        
        with patch('time.sleep') as mock_sleep, \
             patch.object(APICrawler, 'fetch_data') as mock_fetch:
            # 模拟请求抛出异常
            mock_fetch.side_effect = [
                Exception('网络错误'),
                {'status': 'error', 'message': '请求失败', 'data': []},
                {
                    'status': 'success',
                    'data': {
                        'data': {
                            'items': [
                                {
                                    'title': '测试文章',
                                    'url': 'https://test.com/article/1',
                                    'content': '测试内容' * 10
                                }
                            ]
                        }
                    }
                }
            ]
            
            # 执行测试
            result = self.crawler.run()
            
            # 验证结果
            self.assertEqual(result['status'], 'success')
            self.assertEqual(len(result['data']), 1)
            
            # 验证重试次数
            self.assertEqual(mock_fetch.call_count, 3)
            
            # 验证延迟调用
            self.assertEqual(mock_sleep.call_count, 2)
            mock_sleep.assert_called_with(1)

    def test_concurrent_requests(self):
        """测试并发请求"""
        # 配置并发请求
        self.config.config_data['concurrency'] = {
            'enabled': True,
            'max_workers': 3
        }
        self.config.save()
        
        with patch('requests.Session.get') as mock_get:
            # Mock响应
            def get_worker_response(worker_id):
                return MagicMock(
                    status_code=200,
                    json=lambda: {
                        'data': {
                            'data': {
                                'items': [{
                                    'title': f'文章{worker_id}_{i}',
                                    'url': f'https://test.com/article/{worker_id}_{i}',
                                    'content': f'内容{worker_id}_{i}' * 10,
                                    'author': f'作者{worker_id}',
                                    'published_at': '2024-03-20T10:00:00Z'
                                } for i in range(2)]  # 每个worker返回2条数据
                            }
                        }
                    }
                )
                
            def mock_request(*args, **kwargs):
                worker_id = kwargs.get('params', {}).get('worker_id', 0)
                return get_worker_response(worker_id)
                
            mock_get.side_effect = mock_request
            
            # 执行并发请求
            result = self.crawler.run()
            
            # 验证基本结果
            self.assertEqual(result['status'], 'success')
            self.assertEqual(len(result['data']), 6)  # 3个worker各返回2条数据
            
            # 验证请求调用
            self.assertEqual(mock_get.call_count, 3)  # 应该有3个worker发起请求
            
            # 验证每个worker都使用了不同的worker_id
            worker_ids = set()
            for call in mock_get.call_args_list:
                worker_id = call.kwargs['params']['worker_id']
                worker_ids.add(worker_id)
            self.assertEqual(len(worker_ids), 3)
            
            # 验证数据内容
            titles = set(article['title'] for article in result['data'])
            self.assertEqual(len(titles), 6)  # 所有文章标题都应该不同
            
            # 验证每篇文章的完整性
            for article in result['data']:
                self.assertTrue(article['title'].startswith('文章'))
                self.assertTrue(article['url'].startswith('https://test.com/article/'))
                self.assertTrue(len(article['content']) >= 10)
                self.assertTrue(article['author'].startswith('作者'))
                self.assertIsNotNone(article['pub_time'])
                
            # 验证worker_id的分配
            for i in range(3):
                worker_articles = [a for a in result['data'] if f'作者{i}' == a['author']]
                self.assertEqual(len(worker_articles), 2)  # 每个worker应该有2篇文章

    def test_concurrent_requests_partial_failure(self):
        """测试部分并发请求失败的情况"""
        # 配置并发请求
        self.config.config_data['concurrency'] = {
            'enabled': True,
            'max_workers': 3
        }
        self.config.save()
        
        with patch('requests.Session.get') as mock_get:
            # Mock响应：第二个worker失败，其他成功
            def mock_request(*args, **kwargs):
                worker_id = kwargs.get('params', {}).get('worker_id', 0)
                if worker_id == 1:
                    response = MagicMock()
                    response.raise_for_status.side_effect = requests.exceptions.HTTPError('500 Server Error')
                    return response
                    
                return MagicMock(
                    status_code=200,
                    json=lambda: {
                        'data': {
                            'data': {
                                'items': [{
                                    'title': f'文章{worker_id}_{i}',
                                    'url': f'https://test.com/article/{worker_id}_{i}',
                                    'content': f'内容{worker_id}_{i}' * 10,
                                    'author': f'作者{worker_id}',
                                    'published_at': '2024-03-20T10:00:00Z'
                                } for i in range(2)]
                            }
                        }
                    }
                )
                
            mock_get.side_effect = mock_request
            
            # 执行并发请求
            result = self.crawler.run()
            
            # 验证基本结果
            self.assertEqual(result['status'], 'success')
            self.assertEqual(len(result['data']), 4)  # 2个成功的worker各返回2条数据
            
            # 验证请求调用
            self.assertEqual(mock_get.call_count, 3)  # 应该有3个worker发起请求
            
            # 验证成功的worker数据
            successful_worker_ids = [0, 2]  # worker_id 1失败
            for worker_id in successful_worker_ids:
                worker_articles = [a for a in result['data'] if f'作者{worker_id}' == a['author']]
                self.assertEqual(len(worker_articles), 2)  # 每个成功的worker应该有2篇文章
                
                # 验证文章内容
                for article in worker_articles:
                    self.assertTrue(article['title'].startswith(f'文章{worker_id}'))
                    self.assertTrue(article['url'].startswith('https://test.com/article/'))
                    self.assertTrue(len(article['content']) >= 10)
                    self.assertIsNotNone(article['pub_time'])
                    
            # 验证失败的worker数据
            failed_worker_articles = [a for a in result['data'] if '作者1' == a['author']]
            self.assertEqual(len(failed_worker_articles), 0)  # 失败的worker不应该有任何文章

    def test_concurrent_requests_all_failed(self):
        """测试所有并发请求都失败的情况"""
        # 配置并发请求
        self.config.config_data['concurrency'] = {
            'enabled': True,
            'max_workers': 3
        }
        self.config.save()
        
        with patch('requests.Session.get') as mock_get:
            # Mock响应：所有请求都失败，但失败原因不同
            def mock_request(*args, **kwargs):
                worker_id = kwargs.get('params', {}).get('worker_id', 0)
                response = MagicMock()
                if worker_id == 0:
                    response.raise_for_status.side_effect = requests.exceptions.HTTPError('500 Server Error')
                elif worker_id == 1:
                    response.raise_for_status.side_effect = requests.exceptions.ConnectionError('连接超时')
                else:
                    response.raise_for_status.side_effect = requests.exceptions.RequestException('未知错误')
                return response
                
            mock_get.side_effect = mock_request
            
            # 执行并发请求
            result = self.crawler.run()
            
            # 验证基本结果
            self.assertEqual(result['status'], 'error')
            self.assertEqual(len(result['data']), 0)
            self.assertIn('所有并发请求均失败', result['message'])
            
            # 验证请求调用
            self.assertEqual(mock_get.call_count, 3)  # 应该有3个worker发起请求
            
            # 验证每个worker都使用了不同的worker_id
            worker_ids = set()
            for call in mock_get.call_args_list:
                worker_id = call.kwargs['params']['worker_id']
                worker_ids.add(worker_id)
            self.assertEqual(len(worker_ids), 3)
            
            # 验证错误信息包含所有失败原因
            self.assertIn('500 Server Error', result['message'])
            self.assertIn('连接超时', result['message'])
            self.assertIn('未知错误', result['message'])

    def test_fetch_data_with_compression(self):
        """测试压缩支持"""
        # 配置压缩支持
        self.config.config_data['compression'] = True
        self.config.save()
        
        with patch('requests.Session.get') as mock_get:
            # Mock响应
            mock_response = MagicMock(
                status_code=200,
                json=lambda: {
                    'data': {
                        'data': {
                            'items': [{
                                'title': '测试文章',
                                'url': 'https://test.com/article/1',
                                'content': '测试内容' * 10
                            }]
                        }
                    }
                }
            )
            mock_get.return_value = mock_response
            
            # 执行请求
            result = self.crawler.fetch_data()
            
            # 验证结果
            self.assertEqual(result['status'], 'success')
            
            # 验证请求头
            actual_headers = mock_get.call_args.kwargs['headers']
            self.assertIn('Accept-Encoding', actual_headers)
            self.assertEqual(actual_headers['Accept-Encoding'], 'gzip, deflate')

    def test_fetch_data_with_invalid_dynamic_headers(self):
        """测试无效的动态请求头"""
        # 配置无效的动态请求头
        def invalid_header():
            raise Exception("生成请求头失败")
            
        self.config.config_data['dynamic_headers'] = {
            'X-Invalid-Header': invalid_header
        }
        self.config.save()
        
        with patch('requests.Session.get') as mock_get:
            # Mock响应
            mock_response = MagicMock(
                status_code=200,
                json=lambda: {
                    'data': {
                        'data': {
                            'items': [{
                                'title': '测试文章',
                                'url': 'https://test.com/article/1',
                                'content': '测试内容' * 10
                            }]
                        }
                    }
                }
            )
            mock_get.return_value = mock_response
            
            # 执行请求
            result = self.crawler.fetch_data()
            
            # 验证结果
            self.assertEqual(result['status'], 'success')  # 请求应该继续执行
            
            # 验证请求头
            actual_headers = mock_get.call_args.kwargs['headers']
            self.assertNotIn('X-Invalid-Header', actual_headers)  # 无效的头部不应该被添加 

    def test_concurrent_requests_invalid_config(self):
        """测试无效的并发配置"""
        test_cases = [
            (0, "max_workers为0"),
            (-1, "max_workers为负数"),
            (None, "max_workers为None"),
            ("invalid", "max_workers为非数字")
        ]
        
        for max_workers, case_desc in test_cases:
            # 配置并发请求
            self.config.config_data['concurrency'] = {
                'enabled': True,
                'max_workers': max_workers
            }
            self.config.save()
            
            with patch('requests.Session.get') as mock_get:
                mock_response = MagicMock(
                    status_code=200,
                    json=lambda: {
                        'data': {
                            'data': {
                                'items': [{
                                    'title': '测试文章',
                                    'url': 'https://test.com/article/1',
                                    'content': '测试内容' * 10,
                                    'author': '测试作者',
                                    'published_at': '2024-03-20T10:00:00Z'
                                }]
                            }
                        }
                    }
                )
                mock_get.return_value = mock_response
                
                # 执行请求
                result = self.crawler.run()
                
                # 验证结果：应该使用默认的单线程模式
                self.assertEqual(result['status'], 'success', f"测试失败: {case_desc}")
                self.assertEqual(mock_get.call_count, 1, f"测试失败: {case_desc}")
                
                # 验证请求参数
                call_args = mock_get.call_args
                self.assertNotIn('worker_id', call_args.kwargs.get('params', {}), 
                               f"测试失败: {case_desc}, 不应该有worker_id参数")
                
                # 验证数据内容
                self.assertEqual(len(result['data']), 1, f"测试失败: {case_desc}")
                article = result['data'][0]
                self.assertEqual(article['title'], '测试文章', f"测试失败: {case_desc}")
                self.assertEqual(article['url'], 'https://test.com/article/1', f"测试失败: {case_desc}")
                self.assertTrue(len(article['content']) >= 10, f"测试失败: {case_desc}")
                
        # 测试禁用并发
        self.config.config_data['concurrency']['enabled'] = False
        self.config.save()
        
        with patch('requests.Session.get') as mock_get:
            mock_get.return_value = mock_response
            result = self.crawler.run()
            
            # 验证结果：应该使用单线程模式
            self.assertEqual(result['status'], 'success')
            self.assertEqual(mock_get.call_count, 1)
            self.assertEqual(len(result['data']), 1)

    def test_concurrent_requests_timeout(self):
        """测试并发请求超时"""
        self.config.config_data['concurrency'] = {
            'enabled': True,
            'max_workers': 3
        }
        self.config.config_data['timeout'] = {
            'connect': 5,
            'read': 10
        }
        self.config.save()
        
        with patch('requests.Session.get') as mock_get:
            def mock_request(*args, **kwargs):
                worker_id = kwargs.get('params', {}).get('worker_id', 0)
                if worker_id == 1:
                    raise requests.exceptions.Timeout('请求超时')
                return MagicMock(
                    status_code=200,
                    json=lambda: {
                        'data': {
                            'data': {
                                'items': [{
                                    'title': f'文章{worker_id}_{i}',
                                    'url': f'https://test.com/article/{worker_id}_{i}',
                                    'content': f'内容{worker_id}_{i}' * 10,
                                    'author': f'作者{worker_id}',
                                    'published_at': '2024-03-20T10:00:00Z'
                                } for i in range(2)]
                            }
                        }
                    }
                )
                
            mock_get.side_effect = mock_request
            
            # 执行请求
            result = self.crawler.run()
            
            # 验证基本结果
            self.assertEqual(result['status'], 'success')
            self.assertEqual(len(result['data']), 4)  # 2个成功的worker各返回2条数据
            
            # 验证请求参数
            for call in mock_get.call_args_list:
                self.assertEqual(call.kwargs['timeout'], (5, 10))  # 验证超时设置正确
            
            # 验证成功的worker数据
            successful_worker_ids = [0, 2]  # worker_id 1超时
            for worker_id in successful_worker_ids:
                worker_articles = [a for a in result['data'] if f'作者{worker_id}' == a['author']]
                self.assertEqual(len(worker_articles), 2)  # 每个成功的worker应该有2篇文章
                
                # 验证文章内容
                for article in worker_articles:
                    self.assertTrue(article['title'].startswith(f'文章{worker_id}'))
                    self.assertTrue(article['url'].startswith('https://test.com/article/'))
                    self.assertTrue(len(article['content']) >= 10)
                    self.assertIsNotNone(article['pub_time'])
            
            # 验证超时的worker数据
            timeout_worker_articles = [a for a in result['data'] if f'作者1' == a['author']]
            self.assertEqual(len(timeout_worker_articles), 0)  # 超时的worker不应该有任何文章

    def test_concurrent_requests_data_validation(self):
        """测试并发请求的数据验证"""
        self.config.config_data['concurrency'] = {
            'enabled': True,
            'max_workers': 3
        }
        self.config.config_data['validation'] = {
            'required_fields': ['title', 'url', 'content'],
            'min_content_length': 50
        }
        self.config.save()
        
        with patch('requests.Session.get') as mock_get:
            def mock_request(*args, **kwargs):
                worker_id = kwargs.get('params', {}).get('worker_id', 0)
                if worker_id == 1:
                    # 返回无效数据
                    return MagicMock(
                        status_code=200,
                        json=lambda: {
                            'data': {
                                'data': {
                                    'items': [{
                                        'title': '',  # 空标题
                                        'url': 'invalid_url',  # 无效URL
                                        'content': '内容太短'  # 内容长度不足
                                    }]
                                }
                            }
                        }
                    )
                return MagicMock(
                    status_code=200,
                    json=lambda: {
                        'data': {
                            'data': {
                                'items': [{
                                    'title': f'文章{worker_id}_{i}',
                                    'url': f'https://test.com/article/{worker_id}_{i}',
                                    'content': f'内容{worker_id}_{i}' * 10,
                                    'author': f'作者{worker_id}',
                                    'published_at': '2024-03-20T10:00:00Z'
                                } for i in range(2)]
                            }
                        }
                    }
                )
                
            mock_get.side_effect = mock_request
            
            # 执行请求
            result = self.crawler.run()
            
            # 验证结果：无效数据被过滤
            self.assertEqual(result['status'], 'success')
            self.assertEqual(len(result['data']), 4)  # 只有2个worker的数据有效
            
            # 验证所有数据都符合验证规则
            for article in result['data']:
                self.assertTrue(article['title'])  # 标题不为空
                self.assertTrue(article['url'].startswith('https://'))  # URL格式正确
                self.assertTrue(len(article['content']) >= 50)  # 内容长度符合要求 