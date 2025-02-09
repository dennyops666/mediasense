import json
import requests

# 示例新闻数据
sample_news = [
    {
        "_id": "1",
        "title": "人工智能技术在医疗领域取得重大突破",
        "content": "近日，多家医疗机构报告利用人工智能技术在疾病诊断方面取得显著进展。AI系统在肺部CT影像分析中的准确率达到95%以上，大大提高了早期筛查效率。",
        "summary": "AI技术在医疗诊断领域展现出巨大潜力",
        "author": "张三",
        "source": "科技日报",
        "publish_time": "2025-01-30T10:00:00",
        "status": "published",
        "category": {"id": 1, "name": "科技"},
        "tags": ["AI", "医疗", "科技创新"],
        "sentiment_score": 0.8
    },
    {
        "_id": "2",
        "title": "全球气候变化加剧，各国加强环保合作",
        "content": "联合国最新报告显示，全球平均气温继续上升，极端天气事件频发。各国政府承诺加强合作，共同应对气候变化挑战。",
        "summary": "全球气候问题日益严峻，国际社会携手应对",
        "author": "李四",
        "source": "环球时报",
        "publish_time": "2025-01-30T11:00:00",
        "status": "published",
        "category": {"id": 2, "name": "环境"},
        "tags": ["气候变化", "环保", "国际合作"],
        "sentiment_score": 0.3
    },
    {
        "_id": "3",
        "title": "新一代大语言模型发布，性能大幅提升",
        "content": "OpenAI发布最新版GPT-5模型，在多个领域展现出超越人类的能力。新模型在逻辑推理、创意写作等方面都有显著提升。",
        "summary": "GPT-5模型发布，AI能力再上新台阶",
        "author": "王五",
        "source": "科技周刊",
        "publish_time": "2025-01-30T12:00:00",
        "status": "published",
        "category": {"id": 1, "name": "科技"},
        "tags": ["AI", "GPT", "深度学习"],
        "sentiment_score": 0.9
    },
    {
        "_id": "4",
        "title": "数字经济发展迅速，传统企业加速转型",
        "content": "在数字化浪潮下，越来越多的传统企业开始拥抱新技术。云计算、大数据、人工智能等技术正在重塑各个行业。",
        "summary": "数字化转型成为企业发展必由之路",
        "author": "赵六",
        "source": "经济日报",
        "publish_time": "2025-01-30T13:00:00",
        "status": "published",
        "category": {"id": 3, "name": "经济"},
        "tags": ["数字经济", "企业转型", "创新"],
        "sentiment_score": 0.7
    },
    {
        "_id": "5",
        "title": "量子计算研究获突破，商业应用进入倒计时",
        "content": "科学家们在量子计算领域取得重要进展，成功实现了100量子比特的稳定控制。这一突破为量子计算的商业化应用铺平道路。",
        "summary": "量子计算技术取得重大突破",
        "author": "钱七",
        "source": "科学时报",
        "publish_time": "2025-01-30T14:00:00",
        "status": "published",
        "category": {"id": 1, "name": "科技"},
        "tags": ["量子计算", "科技创新", "前沿科技"],
        "sentiment_score": 0.85
    }
]

# 生成批量索引数据
bulk_data = []
for news in sample_news:
    bulk_data.append(json.dumps({"index": {"_id": news["_id"]}}))
    news_data = news.copy()
    news_data.pop("_id")  # 移除_id字段
    bulk_data.append(json.dumps(news_data))

# 将数据写入文件
with open("sample_news.json", "w", encoding="utf-8") as f:
    f.write("\n".join(bulk_data) + "\n")

print("示例数据已生成到 sample_news.json") 