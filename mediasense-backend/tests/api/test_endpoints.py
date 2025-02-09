"""
API 端点测试模块
"""
import os
import sys
import django
import requests
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# API基础配置
BASE_URL = "http://backend.mediasense.com/api"  # 使用本地开发服务器
ADMIN_USERNAME = "admin"  # 超级管理员用户名
ADMIN_PASSWORD = "admin@123456"  # 超级管理员密码

# 设置 Django 环境
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediasense.settings')
django.setup()

# 加载初始数据
from django.core.management import call_command
try:
    call_command('loaddata', 'news/fixtures/initial_news.json')
    call_command('loaddata', 'crawler/fixtures/initial_data.json')
    logging.info("成功加载初始数据")
except Exception as e:
    logging.error(f"加载初始数据失败: {str(e)}")

class APITester:
    def __init__(self):
        self.token = None
        self.refresh_token = None
        self.session = requests.Session()
        self.test_results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0
        }

    def log_test_result(self, test_name, passed, error=None):
        """记录测试结果"""
        status = "✅ PASSED" if passed else "❌ FAILED"
        self.test_results["total"] += 1
        if passed:
            self.test_results["passed"] += 1
            logging.info(f"{test_name}: {status}")
        else:
            self.test_results["failed"] += 1
            logging.error(f"{test_name}: {status}")
            if error:
                logging.error(f"错误详情: {error}")

    def authenticate(self):
        """获取认证token"""
        try:
            logging.info(f"尝试使用超级管理员账号登录: {ADMIN_USERNAME}")
            
            response = self.session.post(
                f"{BASE_URL}/auth/token/",
                json={
                    "username": ADMIN_USERNAME,
                    "password": ADMIN_PASSWORD
                }
            )
            
            logging.info(f"认证响应状态码: {response.status_code}")
            logging.info(f"认证响应内容: {response.text}")
            
            response.raise_for_status()
            data = response.json()
            
            # 直接从响应中获取token
            if "access" in data and "refresh" in data:
                self.token = data["access"]
                self.refresh_token = data["refresh"]
            else:
                raise ValueError("响应格式错误: 未找到access token")
            
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            self.log_test_result("认证测试", True)
            return True
        except Exception as e:
            self.log_test_result("认证测试", False, str(e))
            return False

    def test_auth_endpoints(self):
        """测试认证相关接口"""
        if not self.token:
            logging.error("未获取到token，无法测试认证接口")
            return
            
        # 测试获取当前用户信息
        try:
            response = self.session.get(f"{BASE_URL}/auth/me/")
            response.raise_for_status()
            self.log_test_result("获取用户信息", True)
        except Exception as e:
            self.log_test_result("获取用户信息", False, str(e))

        # 测试刷新token
        try:
            response = self.session.post(
                f"{BASE_URL}/auth/token/refresh/",
                json={"refresh": self.refresh_token}
            )
            response.raise_for_status()
            self.log_test_result("刷新Token", True)
        except Exception as e:
            self.log_test_result("刷新Token", False, str(e))

    def test_news_endpoints(self):
        """测试新闻相关接口"""
        # 测试获取文章列表
        try:
            response = self.session.get(
                f"{BASE_URL}/news/news-articles/",
                params={
                    "page": 1,
                    "size": 10
                }
            )
            response.raise_for_status()
            self.log_test_result("获取文章列表", True)
        except Exception as e:
            self.log_test_result("获取文章列表", False, str(e))

    def test_monitoring_endpoints(self):
        """测试监控相关接口"""
        try:
            response = self.session.get(f"{BASE_URL}/monitoring/system-status/overview/")
            response.raise_for_status()
            self.log_test_result("系统状态概览", True)
        except Exception as e:
            self.log_test_result("系统状态概览", False, str(e))

    def test_crawler_endpoints(self):
        """测试爬虫相关接口"""
        try:
            response = self.session.get(f"{BASE_URL}/crawler/configs/")
            response.raise_for_status()
            self.log_test_result("获取爬虫配置", True)
        except Exception as e:
            self.log_test_result("获取爬虫配置", False, str(e))

    def test_search_endpoints(self):
        """测试搜索相关接口"""
        try:
            response = self.session.get(
                f"{BASE_URL}/search/search/",
                params={
                    "q": "test",
                    "page": 1,
                    "size": 10
                }
            )
            response.raise_for_status()
            self.log_test_result("搜索文章", True)
        except Exception as e:
            self.log_test_result("搜索文章", False, str(e))

    def test_ai_endpoints(self):
        """测试AI服务相关接口"""
        # 测试情感分析
        try:
            response = self.session.post(
                f"{BASE_URL}/ai/services/sentiment-analysis/",
                json={"text": "这是一个测试文本，用于情感分析。"}
            )
            response.raise_for_status()
            self.log_test_result("情感分析", True)
        except Exception as e:
            self.log_test_result("情感分析", False, str(e))

    def print_summary(self):
        """打印测试总结"""
        logging.info("\n=== 测试结果总结 ===")
        logging.info(f"总测试数: {self.test_results['total']}")
        logging.info(f"通过: {self.test_results['passed']} ✅")
        logging.info(f"失败: {self.test_results['failed']} ❌")
        if self.test_results['total'] > 0:
            success_rate = (self.test_results['passed'] / self.test_results['total'] * 100)
            logging.info(f"成功率: {success_rate:.2f}%")
        else:
            logging.info("成功率: N/A (未执行测试)")

def main():
    """主测试函数"""
    tester = APITester()
    
    # 认证测试
    if not tester.authenticate():
        logging.error("认证失败，停止测试")
        return

    # 执行各模块测试
    test_functions = [
        tester.test_auth_endpoints,
        tester.test_news_endpoints,
        tester.test_monitoring_endpoints,
        tester.test_crawler_endpoints,
        tester.test_search_endpoints,
        tester.test_ai_endpoints,
    ]

    for test_func in test_functions:
        try:
            test_func()
        except Exception as e:
            logging.error(f"执行 {test_func.__name__} 时发生错误: {str(e)}")

    # 打印测试总结
    tester.print_summary()

if __name__ == "__main__":
    main() 