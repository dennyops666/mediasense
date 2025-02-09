from django.core.management.base import BaseCommand
from news_search.models import SearchSuggestion

class Command(BaseCommand):
    help = '添加搜索建议测试数据'

    def handle(self, *args, **options):
        suggestions = [
            {'keyword': 'AI', 'search_count': 100, 'is_hot': True},
            {'keyword': '人工智能', 'search_count': 90, 'is_hot': True},
            {'keyword': 'ChatGPT', 'search_count': 85, 'is_hot': True},
            {'keyword': '机器学习', 'search_count': 80, 'is_hot': True},
            {'keyword': '深度学习', 'search_count': 75, 'is_hot': True}
        ]

        for suggestion in suggestions:
            SearchSuggestion.objects.get_or_create(
                keyword=suggestion['keyword'],
                defaults={
                    'search_count': suggestion['search_count'],
                    'is_hot': suggestion['is_hot']
                }
            )
        
        self.stdout.write(self.style.SUCCESS('成功添加搜索建议测试数据')) 