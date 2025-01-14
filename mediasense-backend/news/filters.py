import django_filters
from .models import NewsArticle

class NewsFilter(django_filters.FilterSet):
    """新闻过滤器."""
    
    title = django_filters.CharFilter(lookup_expr='icontains')
    content = django_filters.CharFilter(lookup_expr='icontains')
    category = django_filters.NumberFilter(field_name='category')
    start_date = django_filters.DateTimeFilter(field_name='publish_time', lookup_expr='gte')
    end_date = django_filters.DateTimeFilter(field_name='publish_time', lookup_expr='lte')
    status = django_filters.ChoiceFilter(choices=NewsArticle.Status.choices)

    class Meta:
        model = NewsArticle
        fields = ['title', 'content', 'category', 'status', 'start_date', 'end_date'] 