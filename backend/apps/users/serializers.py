from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.shops.models import Shop
from apps.shops.serializers import ShopSerializer
from apps.shops.utils import get_user_shops

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
  shops = ShopSerializer(many=True, read_only=True)

  class Meta:
    model = User
    fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'phone', 'shops')
    read_only_fields = ('id',)


class UserMeSerializer(serializers.ModelSerializer):
  shops = serializers.SerializerMethodField()

  class Meta:
    model = User
    fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'phone', 'shops')
    read_only_fields = fields

  def get_shops(self, obj):
    return ShopSerializer(get_user_shops(obj), many=True).data


class UserCreateSerializer(serializers.ModelSerializer):
  password = serializers.CharField(write_only=True, min_length=8)
  shop_ids = serializers.ListField(
    child=serializers.IntegerField(),
    required=False,
    write_only=True,
    default=list,
  )

  class Meta:
    model = User
    fields = (
      'id', 'username', 'email', 'password', 'first_name', 'last_name', 'role', 'phone', 'shop_ids',
    )

  def validate_shop_ids(self, value):
    if not value:
      return value
    found = Shop.objects.filter(pk__in=value, is_active=True).count()
    if found != len(set(value)):
      raise serializers.ValidationError('Une ou plusieurs boutiques sont invalides.')
    return value

  def validate(self, attrs):
    role = attrs.get('role', User.Role.VENDEUR)
    shop_ids = attrs.get('shop_ids', [])
    if role == User.Role.VENDEUR and not shop_ids:
      raise serializers.ValidationError(
        {'shop_ids': 'Un vendeur doit être assigné à au moins une boutique.'}
      )
    return attrs

  def create(self, validated_data):
    shop_ids = validated_data.pop('shop_ids', [])
    password = validated_data.pop('password')
    user = User(**validated_data)
    user.set_password(password)
    user.save()
    if shop_ids:
      user.shops.set(Shop.objects.filter(pk__in=shop_ids))
    return user

  def to_representation(self, instance):
    return UserSerializer(instance, context=self.context).data


class UserUpdateSerializer(serializers.ModelSerializer):
  password = serializers.CharField(write_only=True, min_length=8, required=False, allow_blank=True)
  shop_ids = serializers.ListField(
    child=serializers.IntegerField(),
    required=False,
    write_only=True,
  )

  class Meta:
    model = User
    fields = ('email', 'first_name', 'last_name', 'role', 'phone', 'password', 'shop_ids')

  def validate_shop_ids(self, value):
    if value is None:
      return value
    found = Shop.objects.filter(pk__in=value, is_active=True).count()
    if found != len(set(value)):
      raise serializers.ValidationError('Une ou plusieurs boutiques sont invalides.')
    return value

  def validate(self, attrs):
    role = attrs.get('role', self.instance.role if self.instance else User.Role.VENDEUR)
    shop_ids = attrs.get('shop_ids')
    if shop_ids is not None and role == User.Role.VENDEUR and not shop_ids:
      raise serializers.ValidationError(
        {'shop_ids': 'Un vendeur doit être assigné à au moins une boutique.'}
      )
    return attrs

  def update(self, instance, validated_data):
    shop_ids = validated_data.pop('shop_ids', None)
    password = validated_data.pop('password', None)
    for attr, value in validated_data.items():
      setattr(instance, attr, value)
    if password:
      instance.set_password(password)
    instance.save()
    if shop_ids is not None:
      instance.shops.set(Shop.objects.filter(pk__in=shop_ids))
    return instance

  def to_representation(self, instance):
    return UserSerializer(instance, context=self.context).data
