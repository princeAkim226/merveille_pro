from django.http import Http404
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.shops.models import Shop
from apps.shops.serializers import ShopSerializer
from apps.shops.utils import get_user_shops
from apps.users.permissions import IsAdminOrReadOnly


class ShopViewSet(viewsets.ModelViewSet):
  serializer_class = ShopSerializer
  permission_classes = (IsAuthenticated,)
  search_fields = ('name', 'code')
  ordering_fields = ('name', 'created_at')

  def get_queryset(self):
    return get_user_shops(self.request.user)

  def get_permissions(self):
    if self.action in ('create', 'update', 'partial_update', 'destroy'):
      return [IsAdminOrReadOnly()]
    return super().get_permissions()

  def destroy(self, request, *args, **kwargs):
    try:
      instance = self.get_object()
    except Http404:
      return Response(
        {'detail': 'Cette boutique est introuvable ou déjà désactivée.'},
        status=status.HTTP_404_NOT_FOUND,
      )
    self.perform_destroy(instance)
    return Response(status=status.HTTP_204_NO_CONTENT)

  def perform_destroy(self, instance):
    instance.is_active = False
    instance.save(update_fields=['is_active'])
