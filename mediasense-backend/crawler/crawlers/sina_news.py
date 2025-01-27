from typing import Dict, List, Optional
from .base import BaseCrawler
from ..exceptions import CrawlerError
import logging

logger = logging.getLogger(__name__)

class SinaNewsCrawler(BaseCrawler):
    """新浪新闻爬虫"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.base_url = config['source_url']
        self.headers = config.get('headers', {})
        
    def fetch_data(self) -> Dict:
        """获取新闻数据"""
        params = {
            'pageid': '153',
            'lid': '2509',  # 新闻分类ID
            'num': '50',    # 每页数量
            'page': '1'     # 页码
        }
        
        try:
            response = self.session.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code != 200:
                raise CrawlerError(f'API请求失败: {response.status_code}')
                
            return response.json()
            
        except Exception as e:
            logger.error(f'获取新浪新闻数据失败: {str(e)}')
            raise CrawlerError(f'获取新闻数据失败: {str(e)}')
            
    def parse_response(self, response: Dict) -> List[Dict]:
        """解析响应数据"""
        try:
            articles = []
            items = response.get('result', {}).get('data', [])
            
            for item in items:
                try:
                    article = {
                        'title': item.get('title', ''),
                        'content': item.get('content', ''),
                        'url': item.get('url', ''),
                        'source_url': item.get('url', ''),
                        'pub_date': item.get('ctime', ''),
                        'description': item.get('intro', ''),
                        'source': item.get('media_name', '新浪新闻'),
                        'author': item.get('author', ''),
                        'tags': item.get('keywords', '').split(',') if item.get('keywords') else [],
                        'images': [item.get('img', {}).get('u', '')] if item.get('img') else []
                    }
                    
                    if article['title'] and article['url']:
                        articles.append(article)
                        
                except Exception as e:
                    logger.error(f'解析新闻文章失败: {str(e)}')
                    continue
                    
            return articles
            
        except Exception as e:
            logger.error(f'解析新浪新闻数据失败: {str(e)}')
            return [] 