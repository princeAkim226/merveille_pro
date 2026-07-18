from django.db import transaction
from rest_framework import serializers

from apps.core.services import log_action
from apps.inventory.models import StockMovement
from apps.products.models import Product
from apps.sales.models import Sale, SaleItem
from apps.shops.utils import require_shop_for_write


class SaleItemSerializer(serializers.ModelSerializer):
  product_name = serializers.CharField(source='product.name', read_only=True)
  subtotal = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
  profit = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

  class Meta:
    model = SaleItem
    fields = ('id', 'product', 'product_name', 'quantity', 'price', 'subtotal', 'profit')
    read_only_fields = ('id',)


class SaleItemCreateSerializer(serializers.Serializer):
  product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_active=True))
  quantity = serializers.IntegerField(min_value=1)
  price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)

  def validate(self, attrs):
    product = attrs['product']
    quantity = attrs['quantity']
    if product.stock_quantity < quantity:
      raise serializers.ValidationError(
        {'quantity': f'Stock insuffisant pour {product.name} (disponible: {product.stock_quantity}).'}
      )
    if 'price' not in attrs:
      attrs['price'] = product.selling_price
    return attrs


class SaleSerializer(serializers.ModelSerializer):
  items = SaleItemSerializer(many=True, read_only=True)
  user_name = serializers.CharField(source='user.username', read_only=True)
  shop_name = serializers.CharField(source='shop.name', read_only=True)

  class Meta:
    model = Sale
    fields = ('id', 'shop', 'shop_name', 'date', 'total_amount', 'user', 'user_name', 'notes', 'items')
    read_only_fields = ('id', 'date', 'total_amount', 'user', 'shop')


class SaleCreateSerializer(serializers.Serializer):
  shop = serializers.IntegerField()
  notes = serializers.CharField(required=False, allow_blank=True)
  items = SaleItemCreateSerializer(many=True)

  def validate_items(self, value):
    if not value:
      raise serializers.ValidationError('Au moins un article est requis.')
    return value

  def validate(self, attrs):
    shop = require_shop_for_write(self.context['request'].user, attrs.get('shop'))
    attrs['_shop'] = shop
    for item in attrs.get('items', []):
      if item['product'].shop_id != shop.pk:
        raise serializers.ValidationError(
          {'items': f'Le produit « {item["product"].name} » n\'appartient pas à {shop.name}.'}
        )
    return attrs

  @transaction.atomic
  def create(self, validated_data):
    user = self.context['request'].user
    shop = validated_data.pop('_shop')
    validated_data.pop('shop', None)
    items_data = validated_data['items']
    notes = validated_data.get('notes', '')

    sale = Sale.objects.create(user=user, shop=shop, notes=notes)

    for item_data in items_data:
      product = item_data['product']
      quantity = item_data['quantity']
      price = item_data['price']

      product.stock_quantity -= quantity
      product.save(update_fields=['stock_quantity', 'updated_at'])

      SaleItem.objects.create(
        sale=sale,
        product=product,
        quantity=quantity,
        price=price,
      )

      StockMovement.objects.create(
        product=product,
        type=StockMovement.MovementType.OUT,
        quantity=quantity,
        user=user,
        reference=f'VENTE-{sale.pk}',
        notes=f'Vente #{sale.pk} — {shop.name}',
      )

    sale.recalculate_total()
    log_action(user, 'sale_created', f'Vente #{sale.pk} ({shop.name}) — {sale.total_amount}')
    return sale
