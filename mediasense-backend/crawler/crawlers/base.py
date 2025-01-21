import datetime

class BaseCrawler:
    def __init__(self):
        self.source_name = None
        self.api_url = None
        self.enabled = True

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

    def run(self):
        """运行爬虫"""
        if not self.enabled:
            print(f"INFO {self.source_name} 爬虫已禁用")
            return 0, 0, 0, 0
        
        try:
            response = self.fetch_data()
            if not response:
                return 0, 0, 0, 0
            
            news_list = self.parse_response(response)
            if not news_list:
                return 0, 0, 0, 0
            
            return self.save_news(news_list)
            
        except Exception as e:
            print(f"ERROR {self.source_name} 爬虫运行失败: {str(e)}")
            return 0, 0, 0, 0 