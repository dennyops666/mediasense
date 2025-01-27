from .rss_crawler import RSSCrawler
import logging
import time

logger = logging.getLogger(__name__)

class HuxiuCrawler(RSSCrawler):
    """虎嗅网爬虫"""
    
    def __init__(self, config):
        """初始化爬虫
        
        Args:
            config: 爬虫配置对象
        """
        super().__init__(config)
        # 更新请求头
        self.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.huxiu.com'
        })
        
    def fetch_data(self):
        """获取RSS数据，添加重试机制"""
        retries = 3
        for i in range(retries):
            try:
                return super().fetch_data()
            except Exception as e:
                if i == retries - 1:
                    logger.error(f"虎嗅网RSS数据获取失败，已重试{retries}次: {str(e)}")
                    raise
                logger.warning(f"第{i+1}次获取RSS数据失败，准备重试: {str(e)}")
                time.sleep(2 ** i)  # 指数退避
                
    def parse_response(self, data):
        """解析RSS数据，添加额外的错误处理"""
        try:
            articles = super().parse_response(data)
            if not articles:
                logger.warning("未解析到任何文章，可能是RSS格式发生变化")
                return []
                
            # 添加额外的数据清理
            cleaned_articles = []
            for article in articles:
                try:
                    # 确保必要字段存在且有效
                    if not article.get('title') or not article.get('url'):
                        continue
                        
                    # 清理URL
                    article['url'] = article['url'].strip()
                    if not article['url'].startswith('http'):
                        continue
                        
                    # 确保内容不为空
                    if not article.get('content'):
                        article['content'] = article.get('description', '')
                        
                    cleaned_articles.append(article)
                    
                except Exception as e:
                    logger.error(f"文章清理失败: {str(e)}")
                    continue
                    
            return cleaned_articles
            
        except Exception as e:
            logger.error(f"RSS解析失败: {str(e)}")
            return []
    pass 
