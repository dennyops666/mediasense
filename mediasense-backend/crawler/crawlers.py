import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import feedparser
import requests
from bs4 import BeautifulSoup

from .cleaning import DataCleaningService

logger = logging.getLogger(__name__)


class BaseCrawler:
    """爬虫基类"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.headers = config.get("headers", {})
        self.source_url = config["source_url"]
        self.data_cleaner = DataCleaningService()

    def crawl(self) -> List[Dict[str, Any]]:
        """执行爬虫任务"""
        raise NotImplementedError

    def clean_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """清洗数据"""
        return self.data_cleaner.clean_article(data)


class RSSCrawler(BaseCrawler):
    """RSS爬虫实现"""

    def crawl(self) -> List[Dict[str, Any]]:
        """
        抓取RSS源内容
        :return: 文章列表
        """
        try:
            # 获取RSS内容
            response = requests.get(self.source_url, headers=self.headers, timeout=30)
            response.raise_for_status()

            # 解析RSS
            feed = feedparser.parse(response.content)
            if feed.bozo:  # RSS解析错误
                logger.error(f"RSS解析错误: {feed.bozo_exception}")
                return []

            # 提取文章
            articles = []
            for entry in feed.entries:
                try:
                    article = self.clean_data(entry)
                    if article:
                        articles.append(article)
                except Exception as e:
                    logger.error(f"处理RSS条目时出错: {str(e)}")
                    continue

            return articles

        except Exception as e:
            logger.error(f"抓取RSS源 {self.source_url} 失败: {str(e)}")
            return []

    def clean_data(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        清洗RSS条目数据
        :param entry: RSS条目
        :return: 清洗后的文章数据
        """
        # 提取发布时间
        published = entry.get("published_parsed") or entry.get("updated_parsed")
        if published:
            published = datetime(*published[:6])
        else:
            published = datetime.now()

        # 提取来源
        source = self.config.get("source_name")
        if not source:
            feed_link = entry.get("feed", {}).get("link") or self.source_url
            source = urlparse(feed_link).netloc

        # 构建文章数据
        return {
            "title": entry.get("title", "").strip(),
            "content": entry.get("content", [{"value": ""}])[0]["value"],
            "summary": entry.get("summary", "").strip(),
            "url": entry.get("link", "").strip(),
            "source": source,
            "author": entry.get("author", "").strip(),
            "publish_time": published,
            "tags": [tag.term for tag in entry.get("tags", [])],
            "raw_data": entry,
        }


class APICrawler(BaseCrawler):
    """API爬虫实现"""

    def crawl(self) -> List[Dict[str, Any]]:
        """
        调用API获取内容
        :return: 文章列表
        """
        try:
            # 获取API配置
            method = self.config.get("method", "GET")
            params = self.config.get("params", {})
            data = self.config.get("data", {})
            timeout = self.config.get("timeout", 30)

            # 发送请求
            response = requests.request(
                method=method,
                url=self.source_url,
                headers=self.headers,
                params=params,
                json=data if method in ["POST", "PUT", "PATCH"] else None,
                timeout=timeout,
            )
            response.raise_for_status()

            # 解析响应
            result = response.json()

            # 提取文章列表
            articles_path = self.config.get("articles_path", "")
            articles_data = result
            if articles_path:
                for key in articles_path.split("."):
                    articles_data = articles_data.get(key, [])

            if not isinstance(articles_data, list):
                logger.error(f"API响应格式错误: articles_path={articles_path}")
                return []

            # 处理文章数据
            articles = []
            for item in articles_data:
                try:
                    article = self.clean_data(item)
                    if article:
                        articles.append(article)
                except Exception as e:
                    logger.error(f"处理API响应条目时出错: {str(e)}")
                    continue

            return articles

        except Exception as e:
            logger.error(f"调用API {self.source_url} 失败: {str(e)}")
            return []

    def clean_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        清洗API响应数据
        :param data: API响应条目
        :return: 清洗后的文章数据
        """
        # 获取字段映射配置
        field_mapping = self.config.get("field_mapping", {})

        # 提取发布时间
        publish_time_field = field_mapping.get("publish_time", "publishTime")
        publish_time_format = self.config.get("publish_time_format")
        publish_time = data.get(publish_time_field)

        if publish_time:
            try:
                if publish_time_format:
                    publish_time = datetime.strptime(publish_time, publish_time_format)
                else:
                    # 尝试自动解析时间格式
                    publish_time = datetime.fromisoformat(publish_time.replace("Z", "+00:00"))
            except Exception:
                publish_time = datetime.now()
        else:
            publish_time = datetime.now()

        # 提取来源
        source = self.config.get("source_name")
        if not source:
            source = data.get(field_mapping.get("source", "source"), "")

        # 提取标签
        tags_field = field_mapping.get("tags", "tags")
        tags = data.get(tags_field, [])
        if isinstance(tags, str):
            tags = [tag.strip() for tag in tags.split(",") if tag.strip()]

        # 构建文章数据
        return {
            "title": data.get(field_mapping.get("title", "title"), "").strip(),
            "content": data.get(field_mapping.get("content", "content"), "").strip(),
            "summary": data.get(field_mapping.get("summary", "summary"), "").strip(),
            "url": data.get(field_mapping.get("url", "url"), "").strip(),
            "source": source,
            "author": data.get(field_mapping.get("author", "author"), "").strip(),
            "publish_time": publish_time,
            "tags": tags,
            "raw_data": data,
        }


class WebCrawler(BaseCrawler):
    """网页爬虫实现"""

    def crawl(self) -> List[Dict[str, Any]]:
        """
        抓取网页内容
        :return: 文章列表
        """
        try:
            # 获取网页配置
            selectors = self.config.get("selectors", {})
            if not selectors:
                logger.error("未配置选择器")
                return []

            # 发送请求
            response = requests.get(self.source_url, headers=self.headers, timeout=30)
            response.raise_for_status()

            # 解析网页
            soup = BeautifulSoup(response.text, "html.parser")

            # 提取文章列表
            articles_selector = selectors.get("articles", "")
            if not articles_selector:
                logger.error("未配置文章列表选择器")
                return []

            article_elements = soup.select(articles_selector)
            if not article_elements:
                logger.warning(f"未找到文章列表: {articles_selector}")
                return []

            # 处理文章数据
            articles = []
            for element in article_elements:
                try:
                    article = self.clean_data(element, selectors)
                    if article:
                        articles.append(article)
                except Exception as e:
                    logger.error(f"处理文章元素时出错: {str(e)}")
                    continue

            return articles

        except Exception as e:
            logger.error(f"抓取网页 {self.source_url} 失败: {str(e)}")
            return []

    def clean_data(self, element: BeautifulSoup, selectors: Dict[str, str]) -> Dict[str, Any]:
        """
        清洗网页数据
        :param element: 文章元素
        :param selectors: 选择器配置
        :return: 清洗后的文章数据
        """
        # 提取文章URL
        url_selector = selectors.get("url", "a")
        url_element = element.select_one(url_selector)
        if not url_element:
            raise ValueError("未找到文章URL")

        url = url_element.get("href", "").strip()
        if not url:
            raise ValueError("文章URL为空")

        # 处理相对URL
        if not url.startswith(("http://", "https://")):
            url = urljoin(self.source_url, url)

        # 获取文章详情页
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            detail_soup = BeautifulSoup(response.text, "html.parser")
        except Exception as e:
            logger.error(f"获取文章详情页失败: {str(e)}")
            raise

        # 提取文章内容
        title = self._extract_text(detail_soup, selectors.get("title", ""))
        content = self._extract_text(detail_soup, selectors.get("content", ""))
        summary = self._extract_text(detail_soup, selectors.get("summary", ""))
        author = self._extract_text(detail_soup, selectors.get("author", ""))
        publish_time = self._extract_datetime(detail_soup, selectors.get("publish_time", ""))
        tags = self._extract_tags(detail_soup, selectors.get("tags", ""))

        # 提取来源
        source = self.config.get("source_name")
        if not source:
            source = urlparse(self.source_url).netloc

        return {
            "title": title,
            "content": content,
            "summary": summary or content[:200],
            "url": url,
            "source": source,
            "author": author,
            "publish_time": publish_time or datetime.now(),
            "tags": tags,
            "raw_data": {"url": url, "html": response.text},
        }

    def _extract_text(self, soup: BeautifulSoup, selector: str) -> str:
        """提取文本内容"""
        if not selector:
            return ""
        element = soup.select_one(selector)
        return element.get_text().strip() if element else ""

    def _extract_datetime(self, soup: BeautifulSoup, selector: str) -> Optional[datetime]:
        """提取日期时间"""
        if not selector:
            return None

        element = soup.select_one(selector)
        if not element:
            return None

        text = element.get_text().strip()
        if not text:
            return None

        # 尝试多种时间格式解析
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%Y年%m月%d日 %H:%M:%S",
            "%Y年%m月%d日 %H:%M",
            "%Y年%m月%d日",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue

        return None

    def _extract_tags(self, soup: BeautifulSoup, selector: str) -> List[str]:
        """提取标签列表"""
        if not selector:
            return []

        elements = soup.select(selector)
        return [element.get_text().strip() for element in elements if element.get_text().strip()]
