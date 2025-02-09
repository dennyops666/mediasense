from .base import BaseCrawler
import logging
import requests
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
from django.utils import timezone
from urllib.parse import urljoin
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from ..exceptions import FetchError, ParseError

logger = logging.getLogger(__name__)

class WebCrawler(BaseCrawler):
    """Web爬虫基类"""

    def __init__(self, config):
        """初始化Web爬虫"""
        super().__init__(config)
        self.headers = config.headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def fetch_data(self) -> Dict[str, Any]:
        """
        获取网页数据
        :return: 包含状态和数据的字典
        :raises: FetchError 当获取数据失败时
        """
        try:
            logger.info(f"开始获取网页数据: {self.source_url}")
            response = self.session.get(self.source_url, timeout=30)
            response.raise_for_status()
            return {
                'status': 'success',
                'message': '成功获取网页数据',
                'data': response.text
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
            error_msg = f"获取网页数据失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'status': 'error',
                'message': error_msg,
                'data': None
            }

    def parse_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        解析网页数据
        :param data: fetch_data返回的数据字典
        :return: 解析后的文章列表
        :raises: ParseError 当解析数据失败时
        """
        try:
            logger.info("开始解析网页数据")
            
            if data.get('status') != 'success' or not data.get('data'):
                logger.error(f"获取网页数据失败: {data.get('message')}")
                return []
                
            # 解析HTML
            soup = BeautifulSoup(data['data'], 'html.parser')
            
            # 获取文章列表选择器
            list_selector = self.config.config_data.get('list_selector')
            if not list_selector:
                logger.error("未配置文章列表选择器")
                return []
                
            # 获取文章列表
            articles = []
            items = soup.select(list_selector)
            logger.info(f"找到{len(items)}个文章元素")
            
            for item in items:
                try:
                    # 提取标题
                    title_selector = self.config.config_data.get('title_selector')
                    title_elem = item.select_one(title_selector) if title_selector else None
                    title = title_elem.get_text().strip() if title_elem else None
                    
                    if not title:
                        logger.warning("跳过无标题文章")
                        continue
                            
                    # 提取链接
                    link_selector = self.config.config_data.get('link_selector')
                    link_elem = item.select_one(link_selector) if link_selector else None
                    url = link_elem.get('href') if link_elem else None
                    
                    if url:
                        url = urljoin(self.source_url, url)
                    
                    if not url or not url.startswith(('http://', 'https://')):
                        logger.warning(f"跳过无效URL: {url}")
                        continue
                            
                    # 提取作者
                    author_selector = self.config.config_data.get('author_selector')
                    author_elem = item.select_one(author_selector) if author_selector else None
                    author = author_elem.get_text().strip() if author_elem else ''
                            
                    # 提取发布时间
                    time_selector = self.config.config_data.get('time_selector')
                    time_elem = item.select_one(time_selector) if time_selector else None
                    pub_time = time_elem.get_text().strip() if time_elem else None
                    
                    if pub_time:
                        try:
                            pub_time = self.parse_datetime(pub_time)
                        except Exception:
                            pub_time = timezone.now()
                    else:
                        pub_time = timezone.now()
                        
                    # 提取摘要
                    summary_selector = self.config.config_data.get('summary_selector')
                    summary_elem = item.select_one(summary_selector) if summary_selector else None
                    description = summary_elem.get_text().strip() if summary_elem else ''
                    
                    # 提取内容
                    content = ''
                    if self.config.config_data.get('need_content', False):
                        try:
                            content = self._get_article_content(url)
                        except Exception as e:
                            logger.error(f"获取文章内容失败: {str(e)}", exc_info=True)
                            
                    # 提取标签
                    tags = []
                    tags_selector = self.config.config_data.get('tags_selector')
                    if tags_selector:
                        tag_elems = item.select(tags_selector)
                        tags = [tag.get_text().strip() for tag in tag_elems if tag.get_text().strip()]
                        
                    # 提取图片
                    images = []
                    image_selector = self.config.config_data.get('image_selector')
                    if image_selector:
                        img_elems = item.select(image_selector)
                        for img in img_elems:
                            src = img.get('src') or img.get('data-src')
                            if src:
                                src = urljoin(self.source_url, src)
                                if src.startswith(('http://', 'https://')):
                                    images.append(src)
                            
                    # 构建文章数据
                    article = {
                        'title': title,
                        'url': url,
                        'content': content or description,
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
                    logger.error(f"解析文章元素失败: {str(e)}", exc_info=True)
                    continue
                    
            logger.info(f"网页解析完成，共获取{len(articles)}篇文章")
            return articles
            
        except Exception as e:
            error_msg = f"网页解析失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return []

    def _get_article_content(self, url: str) -> str:
        """
        获取文章详细内容
        :param url: 文章URL
        :return: 文章内容
        """
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            content_selector = self.config.config_data.get('content_selector')
            if not content_selector:
                return ''
                
            content_elem = soup.select_one(content_selector)
            if not content_elem:
                return ''
                
            return content_elem.get_text(separator='\n').strip()
            
        except Exception as e:
            logger.error(f"获取文章内容失败: {str(e)}", exc_info=True)
            return ''

    def run(self) -> Dict[str, Any]:
        """
        运行爬虫
        :return: 包含状态和数据的字典
        """
        try:
            # 获取网页数据
            result = self.fetch_data()
            if result['status'] != 'success':
                return result
                
            # 解析数据
            articles = self.parse_response(result)
            
            # 返回结果
            return {
                'status': 'success',
                'message': '成功获取并解析网页数据',
                'data': articles
            }
            
        except Exception as e:
            error_msg = f"Web爬虫运行失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'status': 'error',
                'message': error_msg,
                'data': []
            }

class InfoQCrawler(BaseCrawler):
    """InfoQ中文站爬虫"""
    
    def __init__(self, config):
        super().__init__(config)
        self.news_url = "https://www.infoq.cn/public/v1/my/recommond"
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Content-Type": "application/json",
            "Origin": "https://www.infoq.cn",
            "Referer": "https://www.infoq.cn/news",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        }
            
    def fetch_data(self):
        """获取文章列表数据"""
        try:
            payload = {
                "size": 30,
                "score": None,
                "type": 1
            }
            
            response = requests.post(self.news_url, headers=self.headers, json=payload)
            logger.info(f"API响应状态码: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"API请求失败: {response.text}")
                return None
                
            data = response.json()
            if not data or "data" not in data:
                logger.error("API响应数据格式错误")
                return None
                
            articles = []
            for item in data["data"]:
                try:
                    article = {
                        "title": item.get("article_title", ""),
                        "url": f"https://www.infoq.cn/article/{item.get('uuid', '')}",
                        "description": item.get("article_summary", ""),
                        "author": item.get("author", {}).get("nickname", ""),
                        "pub_time": item.get("publish_time", ""),
                        "images": [item.get("article_cover", "")],
                        "tags": [tag.get("name", "") for tag in item.get("topic", [])]
                    }
                    articles.append(article)
                    logger.info(f"成功解析文章: {article['title']}")
                except Exception as e:
                    logger.error(f"解析文章数据失败: {str(e)}")
                    continue
                    
            return articles
        except Exception as e:
            logger.error(f"获取数据失败: {str(e)}")
            return None
            
    def parse_response(self, data):
        """解析响应数据"""
        if not data:
            return None
            
        try:
            items = []
            for article in data:
                item = {
                    "title": article["title"],
                    "url": article["url"],
                    "description": article["description"],
                    "author": article["author"],
                    "pub_time": self.parse_datetime(article["pub_time"]),
                    "images": article["images"],
                    "tags": article["tags"],
                    "source": self.config.name
                }
                items.append(item)
            return {"items": items, "total": len(items)}
        except Exception as e:
            logger.error(f"解析数据失败: {str(e)}")
            return None 