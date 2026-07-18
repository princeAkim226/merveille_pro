import django_filters

from apps.inventory.models import StockMovement


class StockMovementFilter(django_filters.FilterSet):
  product = django_filters.NumberFilter(field_name='product_id')
  type = django_filters.ChoiceFilter(choices=StockMovement.MovementType.choices)
  date_from = django_filters.DateTimeFilter(field_name='date', lookup_expr='gte')
  date_to = django_filters.DateTimeFilter(field_name='date', lookup_expr='lte')

  class Meta:
    model = StockMovement
    fields = ('product', 'type')
