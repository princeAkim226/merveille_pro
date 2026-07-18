from rest_framework import serializers

from apps.products.models import Category, Product, SubCategory
from apps.shops.utils import require_shop_for_write


class SubCategorySerializer(serializers.ModelSerializer):
  category_name = serializers.CharField(source='category.name', read_only=True)

  class Meta:
    model = SubCategory
    fields = ('id', 'category', 'category_name', 'name', 'created_at')
    read_only_fields = ('id', 'created_at')


class CategorySerializer(serializers.ModelSerializer):
  product_count = serializers.SerializerMethodField()
  subcategories = SubCategorySerializer(many=True, read_only=True)

  class Meta:
    model = Category
    fields = ('id', 'name', 'product_count', 'subcategories', 'created_at')
    read_only_fields = ('id', 'created_at')

  def get_product_count(self, obj):
    request = self.context.get('request')
    qs = obj.products.filter(is_active=True)
    if request:
      shop_param = request.query_params.get('shop')
      if shop_param and shop_param != 'all':
        qs = qs.filter(shop_id=shop_param)
    return qs.count()


class ProductSerializer(serializers.ModelSerializer):
  category_name = serializers.CharField(source='category.name', read_only=True)
  subcategory_name = serializers.CharField(source='subcategory.name', read_only=True, default='')
  shop_name = serializers.CharField(source='shop.name', read_only=True)
  spec_label = serializers.CharField(read_only=True)
  is_low_stock = serializers.BooleanField(read_only=True)
  has_pack_pricing = serializers.BooleanField(read_only=True)
  profit_margin = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

  class Meta:
    model = Product
    fields = (
      'id', 'shop', 'shop_name', 'name', 'category', 'category_name',
      'subcategory', 'subcategory_name',
      'brand', 'variant', 'spec_quantity', 'spec_unit', 'spec_label', 'shelf_location',
      'purchase_price', 'selling_price', 'pack_price', 'units_per_pack',
      'stock_quantity', 'alert_threshold', 'is_low_stock', 'has_pack_pricing',
      'profit_margin', 'is_active', 'created_at', 'updated_at',
    )
    read_only_fields = ('id', 'created_at', 'updated_at')

  def validate(self, attrs):
    purchase = attrs.get('purchase_price', getattr(self.instance, 'purchase_price', None))
    selling = attrs.get('selling_price', getattr(self.instance, 'selling_price', None))
    pack_price = attrs.get('pack_price', getattr(self.instance, 'pack_price', None))
    units_per_pack = attrs.get('units_per_pack', getattr(self.instance, 'units_per_pack', 1))
    category = attrs.get('category', getattr(self.instance, 'category', None))
    subcategory = attrs.get('subcategory', getattr(self.instance, 'subcategory', None))

    if purchase is not None and selling is not None and selling < purchase:
      raise serializers.ValidationError(
        {'selling_price': 'Le prix unitaire doit être supérieur ou égal au prix d\'achat.'}
      )
    if pack_price is not None and pack_price <= 0:
      attrs['pack_price'] = None
    if units_per_pack is not None and units_per_pack < 1:
      attrs['units_per_pack'] = 1

    if subcategory is not None and category is not None and subcategory.category_id != category.pk:
      raise serializers.ValidationError(
        {'subcategory': 'La sous-catégorie doit appartenir à la catégorie sélectionnée.'}
      )
    if subcategory is not None and category is None and self.instance is not None:
      if subcategory.category_id != self.instance.category_id:
        raise serializers.ValidationError(
          {'subcategory': 'La sous-catégorie doit appartenir à la catégorie du produit.'}
        )

    request = self.context.get('request')
    if request and self.instance is None:
      shop_id = attrs.get('shop')
      require_shop_for_write(request.user, shop_id.pk if hasattr(shop_id, 'pk') else shop_id)
    return attrs
