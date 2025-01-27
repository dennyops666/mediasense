from .base import BaseCrawler
import logging
import requests
import json
import re
from typing import Dict, List
from bs4 import BeautifulSoup
from django.utils import timezone

logger = logging.getLogger(__name__)

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
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def fetch_data(self) -> Dict:
        """获取API数据"""
        try:
            logger.info(f"开始获取API数据: {self.config.source_url}")
            response = self.session.get(self.config.source_url, timeout=30)
            response.raise_for_status()
            
            try:
                return response.json()
            except json.JSONDecodeError:
                # 尝试从JavaScript中提取JSON
                pattern = r'({[^{]*?"newsstream":[^}]*?})'
                match = re.search(pattern, response.text)
                if match:
                    try:
                        return json.loads(match.group(1))
                    except json.JSONDecodeError as e:
                        logger.error(f"解析提取的JSON数据失败: {str(e)}")
                        raise
                else:
                    logger.error("未找到有效的JSON数据")
                    raise ValueError("未找到有效的JSON数据")
                    
        except Exception as e:
            logger.error(f"获取API数据失败: {str(e)}")
            raise

    def parse_response(self, data: Dict) -> List[Dict]:
        """解析API响应数据"""
        try:
            logger.info("开始解析API数据")
            articles = []
            
            # 获取数据路径
            data_path = self.config.config_data.get('data_path', '')
            if not data_path:
                logger.error(f'数据路径未配置: {self.config.name}')
                return []
                
            # 根据数据路径获取新闻列表
            news_list = data
            for key in data_path.split('.'):
                if key.startswith('[') and key.endswith(']'):
                    # 处理数组索引
                    index = int(key[1:-1])
                    if not isinstance(news_list, (list, tuple)) or index >= len(news_list):
                        logger.error(f'无效的数组索引: {key}, 当前值: {news_list}')
                        return []
                    news_list = news_list[index]
                else:
                    # 处理字典键
                    if not isinstance(news_list, dict):
                        logger.error(f'无效的数据路径: {data_path}, 当前值: {news_list}')
                        return []
                    news_list = news_list.get(key, {})
                    
            if not isinstance(news_list, list):
                logger.error(f'无效的新闻列表: {news_list}')
                return []
                
            # 解析每条新闻
            for item in news_list:
                try:
                    # 获取字段值
                    title = self._get_field_value(item, self.config.config_data.get('title_path'))
                    url = self._get_field_value(item, self.config.config_data.get('link_path'))
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
                            logger.error(f'获取新闻详情失败: {str(e)}')
                            
                    # 构建文章数据
                    article = {
                        'title': title,
                        'url': url,
                        'content': content or description or '',
                        'description': description or '',
                        'author': author or '',
                        'source': source or self.config.name,
                        'pub_time': pub_time or timezone.now(),
                        'config': self.config
                    }
                    
                    if article['title'] and article['url']:
                        articles.append(article)
                        logger.debug(f"成功解析文章: {article['title']}")
                    else:
                        logger.warning(f"文章缺少必要字段: {article}")
                        
                except Exception as e:
                    logger.error(f"解析文章失败: {str(e)}")
                    continue
                    
            logger.info(f"API解析完成，共获取{len(articles)}篇文章")
            return articles
            
        except Exception as e:
            logger.error(f"API解析失败: {str(e)}")
            return []
            
    def _get_field_value(self, data: Dict, path: str) -> str:
        """根据路径获取字段值"""
        if not path:
            return ''
            
        try:
            value = data
            for key in path.split('.'):
                if key.startswith('[') and key.endswith(']'):
                    # 处理数组索引
                    index = int(key[1:-1])
                    if not isinstance(value, (list, tuple)) or index >= len(value):
                        return ''
                    value = value[index]
                else:
                    # 处理字典键
                    if not isinstance(value, dict):
                        return ''
                    value = value.get(key, '')
                    
            return str(value).strip()
            
        except Exception as e:
            logger.error(f"获取字段值失败: {str(e)}")
            return '' 