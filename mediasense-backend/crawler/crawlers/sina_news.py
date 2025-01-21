import datetime
import json
import requests
from .base import BaseCrawler

class SinaNewsCrawler(BaseCrawler):
    def __init__(self):
        super().__init__()
        self.source_name = "新浪新闻"
        self.api_url = "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&num=50&versionNumber=1.2.8"
        self.enabled = True

    def fetch_data(self):
        """获取新闻数据"""
        try:
            print(f"\n检查 {self.source_name} API响应:")
            response = requests.get(self.api_url)
            print(f"状态码: {response.status_code}")
            print(f"响应内容: {response.text[:500]}")  # 只打印前500个字符
            
            if response.status_code == 200:
                data = response.json()
                print("JSON数据:", json.dumps(data, indent=2, ensure_ascii=False)[:1000])  # 只打印前1000个字符
                return data
            return None
        except Exception as e:
            print(f"ERROR 获取数据失败: {str(e)}")
            return None

    def parse_datetime(self, timestamp):
        """将时间戳转换为datetime对象"""
        try:
            # 将时间戳转换为本地时间
            dt = datetime.datetime.fromtimestamp(int(timestamp))
            return dt
        except (ValueError, TypeError):
            return None

    def parse_response(self, response):
        """解析API响应"""
        print(f"INFO 开始爬取网站: {self.source_name}")
        print(f"INFO 成功获取响应: {self.source_name}, status_code=200")
        print(f"INFO 使用API解析器: {self.source_name}")
        
        try:
            data = response.get('result', {}).get('data', [])
            current_time = self.get_current_time()
            print(f"系统时间: {current_time}")
            
            news_list = []
            for item in data:
                news = {
                    'title': item.get('title', ''),
                    'content': item.get('content', ''),
                    'url': item.get('url', ''),
                    'source': self.source_name,
                    'pub_time': self.parse_datetime(item.get('ctime', '')),
                    'created_at': current_time,
                    'updated_at': current_time,
                }
                news_list.append(news)
            
            print(f"INFO 解析完成: {self.source_name}, 获取{len(news_list)}条数据")
            print(f"INFO 数据清洗完成: 原始数据={len(data)}条, 清洗后={len(news_list)}条")
            return news_list
            
        except Exception as e:
            print(f"ERROR 解析数据失败: {str(e)}")
            return [] 