from rest_framework import serializers

from apps.core.services import log_action
from apps.finance.models import Expense
from apps.shops.utils import require_shop_for_write


class ExpenseSerializer(serializers.ModelSerializer):
  user_name = serializers.CharField(source='user.username', read_only=True, default='')
  shop_name = serializers.CharField(source='shop.name', read_only=True)

  class Meta:
    model = Expense
    fields = ('id', 'shop', 'shop_name', 'label', 'amount', 'date', 'user', 'user_name', 'notes', 'created_at')
    read_only_fields = ('id', 'user', 'created_at')

  def validate(self, attrs):
    if self.instance is None:
      shop_id = attrs.get('shop')
      shop_pk = shop_id.pk if hasattr(shop_id, 'pk') else shop_id
      require_shop_for_write(self.context['request'].user, shop_pk)
    return attrs

  def create(self, validated_data):
    user = self.context['request'].user
    expense = Expense.objects.create(user=user, **validated_data)
    log_action(user, 'expense_created', f'Dépense {expense.label} ({expense.shop.name}) — {expense.amount}')
    return expense
