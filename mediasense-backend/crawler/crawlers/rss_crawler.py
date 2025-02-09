import logging
import feedparser
import requests
from datetime import datetime
from typing import Dict, List, Any
from django.utils import timezone
from .base import BaseCrawler
from bs4 import BeautifulSoup
from django.conf import settings

logger = logging.getLogger(__name__)

class RSSCrawler(BaseCrawler):
    """RSS爬虫"""

    def __init__(self, config):
        """初始化RSS爬虫"""
        super().__init__(config)
        self.headers = config.headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/rss+xml,application/xml;q=0.9',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def fetch_data(self) -> Dict[str, Any]:
        """
        获取RSS数据
        :return: 包含状态和数据的字典
        """
        try:
            logger.info(f"开始获取RSS数据: {self.source_url}")
            response = self.session.get(
                self.source_url,
                timeout=30,
                verify=not settings.DEBUG  # 在测试环境中禁用SSL验证
            )
            
            if response.status_code != 200:
                error_msg = f'请求失败: {response.status_code}'
                logger.error(error_msg)
                return {
                    'status': 'error',
                    'message': error_msg,
                    'data': None
                }

            return {
                'status': 'success',
                'message': '成功获取RSS数据',
                'data': response.content
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求失败: {str(e)}"
            logger.error(error_msg)
            return {
                'status': 'error',
                'message': error_msg,
                'data': None
            }
        except Exception as e:
            error_msg = f"获取RSS数据失败: {str(e)}"
            logger.error(error_msg)
            return {
                'status': 'error',
                'message': error_msg,
                'data': None
            }

    def parse_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        解析RSS数据
        :param data: fetch_data返回的数据字典
        :return: 解析后的文章列表
        """
        try:
            logger.info("开始解析RSS数据")
            
            if data.get('status') != 'success' or not data.get('data'):
                logger.error(f"获取RSS数据失败: {data.get('message')}")
                return []
                
            # 解析RSS
            feed = feedparser.parse(data['data'])
            
            # 检查解析结果
            if hasattr(feed, 'bozo_exception'):
                logger.error(f"RSS解析错误: {feed.bozo_exception}")
                return []
                
            # 获取文章列表
            entries = feed.entries
            logger.info(f"找到{len(entries)}个文章")
            
            articles = []
            for entry in entries:
                try:
                    # 提取标题
                    title = entry.get('title', '').strip()
                    if not title:
                        logger.warning("跳过无标题文章")
                        continue
                    
                    # 提取链接
                    url = entry.get('link', '').strip()
                    if not url or not url.startswith(('http://', 'https://')):
                        logger.warning(f"跳过无效URL: {url}")
                        continue
                    
                    # 提取内容
                    content = ''
                    if hasattr(entry, 'content'):
                        content = entry.content[0].value
                    elif hasattr(entry, 'summary'):
                        content = entry.summary
                    elif hasattr(entry, 'description'):
                        content = entry.description
                        
                    # 清理内容中的HTML标签
                    if content:
                        soup = BeautifulSoup(content, 'html.parser')
                        content = soup.get_text(separator='\n').strip()
                    
                    # 提取摘要
                    description = entry.get('summary', '').strip()
                    if not description:
                        description = content[:200] if content else ''
                        
                    # 提取作者
                    author = entry.get('author', '').strip()
                    
                    # 提取发布时间
                    pub_time = entry.get('published_parsed') or entry.get('updated_parsed')
                    if pub_time:
                        pub_time = datetime(*pub_time[:6])
                    else:
                        pub_time = timezone.now()
                        
                    # 提取标签
                    tags = []
                    if hasattr(entry, 'tags'):
                        tags = [tag.term for tag in entry.tags]
                        
                    # 提取图片
                    images = []
                    if hasattr(entry, 'media_content'):
                        images = [media['url'] for media in entry.media_content if 'url' in media]
                    elif hasattr(entry, 'enclosures'):
                        images = [enc['href'] for enc in entry.enclosures if enc.get('type', '').startswith('image/')]
                        
                    # 构建文章数据
                    article = {
                        'title': title,
                        'url': url,
                        'content': content,
                        'description': description,
                        'author': author,
                        'source': self.source_name,
                        'pub_time': pub_time,
                        'tags': tags,
                        'images': images
                    }
                    
                    articles.append(article)
                    logger.debug(f"成功解析文章: {article['title']}")
                        
                except Exception as e:
                    logger.error(f"解析文章失败: {str(e)}", exc_info=True)
                    continue
                    
            logger.info(f"RSS解析完成，共获取{len(articles)}篇文章")
            return articles
            
        except Exception as e:
            logger.error(f"RSS解析失败: {str(e)}", exc_info=True)
            return []

    def run(self) -> Dict[str, Any]:
        """
        运行爬虫
        :return: 包含状态和数据的字典
        """
        try:
            # 获取RSS数据
            result = self.fetch_data()
            if result['status'] != 'success':
                return result
                
            # 解析数据
            articles = self.parse_response(result)
            
            # 返回结果
            return {
                'status': 'success',
                'message': '成功获取并解析RSS数据',
                'data': articles
            }
            
        except Exception as e:
            error_msg = f"RSS爬虫运行失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'status': 'error',
                'message': error_msg,
                'data': []
            } 