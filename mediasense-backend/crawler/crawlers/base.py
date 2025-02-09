import datetime
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class BaseCrawler:
    """爬虫基类"""

    def __init__(self, config):
        """
        初始化爬虫
        :param config: 爬虫配置
        """
        self.config = config
        self.source_url = config.source_url
        self.source_name = config.name
        self.headers = config.headers or {}
        self.enabled = config.status == 1 and config.is_active
        
    def fetch_data(self) -> Dict:
        """
        获取数据
        :return: 获取的数据
        """
        raise NotImplementedError("子类必须实现fetch_data方法")
        
    def parse_response(self, response: Dict) -> List[Dict]:
        """
        解析响应数据
        :param response: API响应数据
        :return: 解析后的文章列表
        """
        raise NotImplementedError("子类必须实现parse_response方法")
        
    def run(self):
        """运行爬虫"""
        if not self.enabled:
            logger.info(f"{self.source_name} 爬虫已禁用")
            return {
                'status': 'disabled',
                'message': f'{self.source_name} 爬虫已禁用',
                'data': []
            }
        
        try:
            response = self.fetch_data()
            if not response:
                return {
                    'status': 'error',
                    'message': '获取数据失败',
                    'data': []
                }
            
            articles = self.parse_response(response)
            return {
                'status': 'success',
                'message': f'成功获取{len(articles)}篇文章',
                'data': articles
            }
            
        except Exception as e:
            logger.error(f"{self.source_name} 爬虫运行失败: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e),
                'data': []
            }

    def get_current_time(self):
        """获取当前时间"""
        return datetime.datetime.now().replace(tzinfo=None)

    def parse_datetime(self, timestamp):
        """解析时间戳为 datetime 对象"""
        if not timestamp:
            return self.get_current_time()
        
        try:
            if isinstance(timestamp, (int, float)):
                return datetime.datetime.fromtimestamp(timestamp).replace(tzinfo=None)
            elif isinstance(timestamp, str):
                # 尝试直接解析
                try:
                    dt = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                    return dt.replace(tzinfo=None)
                except ValueError:
                    # 尝试解析时间戳字符串
                    try:
                        ts = float(timestamp)
                        return datetime.datetime.fromtimestamp(ts).replace(tzinfo=None)
                    except ValueError:
                        return self.get_current_time()
            else:
                return self.get_current_time()
        except Exception as e:
            logger.error(f"解析时间戳失败: {timestamp}, 错误: {str(e)}")
            return self.get_current_time()

    def save_news(self, news_list):
        """保存新闻列表"""
        if not news_list:
            logger.info("没有新闻需要保存")
            return 0, 0, 0, 0

        total = len(news_list)
        saved = 0
        duplicates = 0
        invalid_time = 0
        errors = 0

        for news in news_list:
            try:
                # 确保时间字段是非时区感知的
                current_time = self.get_current_time()
                if not news.get('pub_time'):
                    news['pub_time'] = current_time
                    invalid_time += 1
                news['created_at'] = current_time
                news['updated_at'] = current_time

                # 检查是否已存在相同的新闻
                if NewsArticle.objects.filter(url=news['url']).exists():
                    logger.info(f"新闻已存在: {news['title']}")
                    duplicates += 1
                    continue

                # 创建新闻对象
                article = NewsArticle(**news)
                article.save()
                saved += 1
                logger.info(f"保存新闻成功: {news['title']}")

            except Exception as e:
                logger.error(f"保存新闻失败: {news['title']}, 错误: {str(e)}")
                errors += 1

        logger.info(f"新闻处理完成: 总数={total}, 成功保存={saved}, 重复={duplicates}, 时间无效={invalid_time}, 错误={errors}")
        return saved, duplicates, invalid_time, errors 