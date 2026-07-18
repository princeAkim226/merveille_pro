from django.db import models, transaction
from django.utils import timezone
from rest_framework import serializers

from apps.core.services import log_action
from apps.inventory.models import InventoryLine, InventorySession, StockMovement
from apps.products.models import Product
from apps.shops.utils import require_shop_for_write


class StockMovementSerializer(serializers.ModelSerializer):
  product_name = serializers.CharField(source='product.name', read_only=True)
  user_name = serializers.CharField(source='user.username', read_only=True, default='')

  class Meta:
    model = StockMovement
    fields = (
      'id', 'product', 'product_name', 'type', 'quantity',
      'date', 'user', 'user_name', 'reference', 'notes',
    )
    read_only_fields = ('id', 'date', 'user')


class StockEntrySerializer(serializers.Serializer):
  product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_active=True))
  quantity = serializers.IntegerField(min_value=1)
  notes = serializers.CharField(required=False, allow_blank=True)

  @transaction.atomic
  def create(self, validated_data):
    user = self.context['request'].user
    product = validated_data['product']
    quantity = validated_data['quantity']
    notes = validated_data.get('notes', '')

    product.stock_quantity += quantity
    product.save(update_fields=['stock_quantity', 'updated_at'])

    movement = StockMovement.objects.create(
      product=product,
      type=StockMovement.MovementType.IN,
      quantity=quantity,
      user=user,
      reference='ENTREE-MANUELLE',
      notes=notes,
    )
    log_action(user, 'stock_in', f'Entrée stock {product.name} +{quantity}')
    return movement


class InventoryLineSerializer(serializers.ModelSerializer):
  product_name = serializers.CharField(source='product.name', read_only=True)
  category_name = serializers.CharField(source='product.category.name', read_only=True)
  subcategory_name = serializers.CharField(source='product.subcategory.name', read_only=True, default='')
  difference = serializers.IntegerField(read_only=True)

  class Meta:
    model = InventoryLine
    fields = (
      'id', 'product', 'product_name', 'category_name', 'subcategory_name',
      'expected_quantity', 'counted_quantity', 'counted_at', 'difference', 'notes',
    )
    read_only_fields = ('id', 'product', 'expected_quantity', 'counted_at')


class InventoryLineUpdateSerializer(serializers.ModelSerializer):
  class Meta:
    model = InventoryLine
    fields = ('counted_quantity', 'notes')

  def validate_counted_quantity(self, value):
    if value is not None and value < 0:
      raise serializers.ValidationError('La quantité comptée ne peut pas être négative.')
    return value

  def update(self, instance, validated_data):
    if 'counted_quantity' in validated_data and validated_data['counted_quantity'] is not None:
      validated_data['counted_at'] = timezone.now()
    return super().update(instance, validated_data)


class InventorySessionListSerializer(serializers.ModelSerializer):
  shop_name = serializers.CharField(source='shop.name', read_only=True)
  created_by_name = serializers.CharField(source='created_by.username', read_only=True, default='')
  lines_count = serializers.SerializerMethodField()
  counted_lines_count = serializers.SerializerMethodField()
  discrepancy_count = serializers.SerializerMethodField()

  class Meta:
    model = InventorySession
    fields = (
      'id', 'shop', 'shop_name', 'title', 'status', 'notes',
      'created_by', 'created_by_name', 'created_at', 'validated_at',
      'lines_count', 'counted_lines_count', 'discrepancy_count',
    )
    read_only_fields = fields

  def get_lines_count(self, obj):
    if hasattr(obj, '_lines_count'):
      return obj._lines_count
    return obj.lines.count()

  def get_counted_lines_count(self, obj):
    if hasattr(obj, '_counted_lines_count'):
      return obj._counted_lines_count
    return obj.lines.filter(counted_quantity__isnull=False).count()

  def get_discrepancy_count(self, obj):
    if hasattr(obj, '_discrepancy_count'):
      return obj._discrepancy_count
    return obj.lines.exclude(counted_quantity__isnull=True).exclude(
      counted_quantity=models.F('expected_quantity'),
    ).count()


class InventorySessionDetailSerializer(InventorySessionListSerializer):
  lines = InventoryLineSerializer(many=True, read_only=True)

  class Meta(InventorySessionListSerializer.Meta):
    fields = InventorySessionListSerializer.Meta.fields + ('lines',)


class InventorySessionCreateSerializer(serializers.Serializer):
  shop = serializers.IntegerField()
  title = serializers.CharField(required=False, allow_blank=True, max_length=120)
  notes = serializers.CharField(required=False, allow_blank=True)

  @transaction.atomic
  def create(self, validated_data):
    user = self.context['request'].user
    shop = require_shop_for_write(user, validated_data['shop'])

    open_exists = InventorySession.objects.filter(
      shop=shop,
      status=InventorySession.Status.OPEN,
    ).exists()
    if open_exists:
      raise serializers.ValidationError(
        {'shop': 'Un inventaire est déjà en cours pour cette boutique. Validez-le ou annulez-le avant d\'en créer un nouveau.'}
      )

    title = validated_data.get('title', '').strip()
    if not title:
      title = f'Inventaire {timezone.localdate().strftime("%d/%m/%Y")}'

    session = InventorySession.objects.create(
      shop=shop,
      title=title,
      notes=validated_data.get('notes', ''),
      created_by=user,
    )

    products = Product.objects.filter(is_active=True, shop=shop).select_related('category', 'subcategory')
    InventoryLine.objects.bulk_create([
      InventoryLine(
        session=session,
        product=product,
        expected_quantity=product.stock_quantity,
      )
      for product in products
    ])

    log_action(user, 'inventory_start', f'Inventaire #{session.pk} — {shop.name} ({products.count()} produits)')
    return session


class InventoryValidateSerializer(serializers.Serializer):
  @transaction.atomic
  def save(self):
    session: InventorySession = self.context['session']
    user = self.context['request'].user

    if session.status != InventorySession.Status.OPEN:
      raise serializers.ValidationError('Cet inventaire n\'est plus modifiable.')

    uncounted = session.lines.filter(counted_quantity__isnull=True).count()
    if uncounted > 0:
      raise serializers.ValidationError(
        f'{uncounted} produit(s) n\'ont pas encore été comptés. Complétez le comptage avant validation.'
      )

    adjusted = 0
    for line in session.lines.select_related('product'):
      diff = line.counted_quantity - line.expected_quantity
      if diff == 0:
        continue

      product = line.product
      product.stock_quantity = line.counted_quantity
      product.save(update_fields=['stock_quantity', 'updated_at'])

      movement_type = StockMovement.MovementType.IN if diff > 0 else StockMovement.MovementType.OUT
      StockMovement.objects.create(
        product=product,
        type=movement_type,
        quantity=abs(diff),
        user=user,
        reference=f'INVENTAIRE-{session.pk}',
        notes=f'Ajustement inventaire : {line.expected_quantity} → {line.counted_quantity}',
      )
      adjusted += 1

    session.status = InventorySession.Status.VALIDATED
    session.validated_at = timezone.now()
    session.save(update_fields=['status', 'validated_at'])

    log_action(user, 'inventory_validate', f'Inventaire #{session.pk} validé — {adjusted} ajustement(s)')
    return session
