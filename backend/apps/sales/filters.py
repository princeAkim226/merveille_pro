import django_filters

from apps.sales.models import Sale


class SaleFilter(django_filters.FilterSet):
  date_from = django_filters.DateTimeFilter(field_name='date', lookup_expr='gte')
  date_to = django_filters.DateTimeFilter(field_name='date', lookup_expr='lte')
  user = django_filters.NumberFilter(field_name='user_id')

  class Meta:
    model = Sale
    fields = ('user',)
