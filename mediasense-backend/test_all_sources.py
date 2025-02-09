import os
import django
import requests
import json
import time

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediasense.settings')
django.setup()

from crawler.models import CrawlerConfig

def get_access_token():
    """获取访问令牌"""
    response = requests.post(
        'http://localhost:8000/api/auth/token/',
        json={
            'username': 'admin',
            'password': 'admin@123456'
        }
    )
    return response.json()['access']

def test_crawler_config(config_id, access_token):
    """测试单个爬虫配置"""
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.post(
        f'http://localhost:8000/api/crawler/configs/{config_id}/test/',
        headers=headers
    )
    return response.json()

def main():
    """主函数"""
    print("获取访问令牌...")
    access_token = get_access_token()

    print("\n开始测试所有数据源...")
    configs = CrawlerConfig.objects.all()
    
    for config in configs:
        print(f"\n测试配置: {config.name}")
        print(f"URL: {config.source_url}")
        try:
            result = test_crawler_config(config.id, access_token)
            print("测试结果:", json.dumps(result, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"测试失败: {str(e)}")
        
        # 等待5秒再测试下一个
        time.sleep(5)

    print("\n所有测试完成!")

if __name__ == "__main__":
    main() 