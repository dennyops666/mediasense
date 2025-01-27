from .rss_crawler import RSSCrawler

class IFanrCrawler(RSSCrawler):
    """爱范儿爬虫"""
    
    def __init__(self, config):
        """初始化爬虫
        
        Args:
            config: 爬虫配置对象
        """
        super().__init__(config)
        self.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }) 