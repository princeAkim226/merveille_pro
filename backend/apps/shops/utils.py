from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.shops.models import Shop


def get_user_shops(user):
  if user.is_admin:
    return Shop.objects.filter(is_active=True)
  return user.shops.filter(is_active=True)


def resolve_shop_scope(user, shop_param=None):
  """
  Retourne (queryset_shops, shop_unique ou None).
  shop_param: id boutique, 'all' ou None → toutes les boutiques accessibles.
  """
  shops = get_user_shops(user)
  if shop_param in (None, '', 'all'):
    return shops, None
  try:
    shop_id = int(shop_param)
  except (TypeError, ValueError):
    raise ValidationError({'shop': 'Identifiant de boutique invalide.'})
  shop = shops.filter(pk=shop_id).first()
  if not shop:
    raise PermissionDenied('Accès refusé à cette boutique.')
  return shops.filter(pk=shop_id), shop


def require_shop_for_write(user, shop_id):
  """Boutique obligatoire pour créer vente/produit/dépense."""
  if shop_id is None:
    raise ValidationError({'shop': 'La boutique est obligatoire.'})
  shops, shop = resolve_shop_scope(user, str(shop_id))
  return shop
