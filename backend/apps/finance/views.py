from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.finance.filters import ExpenseFilter
from apps.finance.models import Expense
from apps.finance.serializers import ExpenseSerializer
from apps.shops.utils import resolve_shop_scope
from apps.users.permissions import IsAdminOrReadOnly


class ExpenseViewSet(viewsets.ModelViewSet):
  serializer_class = ExpenseSerializer
  permission_classes = (IsAuthenticated,)
  filterset_class = ExpenseFilter
  search_fields = ('label', 'notes', 'shop__name')
  ordering_fields = ('date', 'amount', 'created_at')

  def get_queryset(self):
    shops, _ = resolve_shop_scope(
      self.request.user,
      self.request.query_params.get('shop'),
    )
    return Expense.objects.select_related('user', 'shop').filter(shop__in=shops)

  def get_permissions(self):
    if self.action in ('create', 'update', 'partial_update', 'destroy'):
      return [IsAdminOrReadOnly()]
    return super().get_permissions()
