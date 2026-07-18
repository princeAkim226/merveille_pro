import django_filters
from django.db import models

from apps.products.models import Product


class ProductFilter(django_filters.FilterSet):
  shop = django_filters.NumberFilter(field_name='shop_id')
  category = django_filters.NumberFilter(field_name='category_id')
  subcategory = django_filters.NumberFilter(field_name='subcategory_id')
  variant = django_filters.CharFilter(field_name='variant', lookup_expr='icontains')
  low_stock = django_filters.BooleanFilter(method='filter_low_stock')
  min_price = django_filters.NumberFilter(field_name='selling_price', lookup_expr='gte')
  max_price = django_filters.NumberFilter(field_name='selling_price', lookup_expr='lte')

  class Meta:
    model = Product
    fields = ('category', 'is_active')

  def filter_low_stock(self, queryset, name, value):
    if value:
      return queryset.filter(stock_quantity__lte=models.F('alert_threshold'))
    return queryset
