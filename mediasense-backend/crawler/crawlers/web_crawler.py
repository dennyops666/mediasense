from .base import BaseCrawler
import logging
import requests
from typing import Dict, List
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

    def fetch_data(self) -> Dict:
        """获取网页数据"""
        try:
            logger.info(f"开始获取网页数据: {self.config.source_url}")
            response = self.session.get(self.config.source_url, timeout=30)
            response.raise_for_status()
            return {'html': response.text}
        except Exception as e:
            logger.error(f"获取网页数据失败: {str(e)}")
            raise

    def parse_response(self, data: Dict) -> List[Dict]:
        """解析网页数据"""
        try:
            logger.info("开始解析网页数据")
            articles = []
            
            html = data.get('html', '')
            if not html:
                logger.error("网页内容为空")
                return []
                
            # 解析HTML
            soup = BeautifulSoup(html, 'html.parser')
            
            # 获取配置
            selectors = self.config.config_data
            if not selectors:
                logger.error("未配置选择器")
                return []
                
            # 获取文章列表
            list_selector = selectors.get('list_selector')
            if not list_selector:
                logger.error("未配置文章列表选择器")
                return []
                
            article_elements = soup.select(list_selector)
            logger.info(f"找到{len(article_elements)}个文章元素")
            
            for element in article_elements:
                try:
                    # 提取标题
                    title = ''
                    if selectors.get('title_selector'):
                        title_elem = element.select_one(selectors['title_selector'])
                        if title_elem:
                            title = title_elem.get_text().strip()
                            
                    # 提取链接
                    url = ''
                    if selectors.get('url_selector'):
                        url_elem = element.select_one(selectors['url_selector'])
                        if url_elem and url_elem.has_attr('href'):
                            url = url_elem['href']
                            if not url.startswith(('http://', 'https://')):
                                url = urljoin(self.config.source_url, url)
                                
                    # 提取内容
                    content = ''
                    if selectors.get('content_selector'):
                        content_elem = element.select_one(selectors['content_selector'])
                        if content_elem:
                            content = content_elem.get_text(separator='\n').strip()
                            
                    # 提取描述
                    description = ''
                    if selectors.get('description_selector'):
                        desc_elem = element.select_one(selectors['description_selector'])
                        if desc_elem:
                            description = desc_elem.get_text().strip()
                            
                    # 提取作者
                    author = ''
                    if selectors.get('author_selector'):
                        author_elem = element.select_one(selectors['author_selector'])
                        if author_elem:
                            author = author_elem.get_text().strip()
                            
                    # 提取发布时间
                    pub_time = None
                    if selectors.get('pub_time_selector'):
                        time_elem = element.select_one(selectors['pub_time_selector'])
                        if time_elem:
                            pub_time = time_elem.get_text().strip()
                            
                    # 提取标签
                    tags = []
                    if selectors.get('tags_selector'):
                        tag_elems = element.select(selectors['tags_selector'])
                        tags = [tag.get_text().strip() for tag in tag_elems]
                        
                    # 提取图片
                    images = []
                    if selectors.get('images_selector'):
                        img_elems = element.select(selectors['images_selector'])
                        for img in img_elems:
                            if img.has_attr('src'):
                                img_url = img['src']
                                if not img_url.startswith(('http://', 'https://')):
                                    img_url = urljoin(self.config.source_url, img_url)
                                images.append(img_url)
                                
                    # 获取详情页内容
                    if url and not content and selectors.get('detail_content_selector'):
                        try:
                            detail_response = self.session.get(url, timeout=30)
                            detail_response.raise_for_status()
                            detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
                            
                            content_elem = detail_soup.select_one(selectors['detail_content_selector'])
                            if content_elem:
                                content = content_elem.get_text(separator='\n').strip()
                                
                        except Exception as e:
                            logger.error(f"获取详情页失败: {str(e)}")
                            
                    # 构建文章数据
                    article = {
                        'title': title,
                        'url': url,
                        'content': content or description or '',
                        'description': description or '',
                        'author': author or '',
                        'source': self.config.name,
                        'pub_time': pub_time or timezone.now(),
                        'tags': tags,
                        'images': images,
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
                    
            logger.info(f"网页解析完成，共获取{len(articles)}篇文章")
            return articles
            
        except Exception as e:
            logger.error(f"网页解析失败: {str(e)}")
            return []

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