from rest_framework import serializers

from apps.shops.models import Shop


class ShopSerializer(serializers.ModelSerializer):
  class Meta:
    model = Shop
    fields = ('id', 'name', 'code', 'address', 'phone', 'is_active', 'created_at')
    read_only_fields = ('id', 'created_at')
