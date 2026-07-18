from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.sales.filters import SaleFilter
from apps.sales.models import Sale
from apps.sales.serializers import SaleCreateSerializer, SaleSerializer
from apps.shops.utils import resolve_shop_scope


class SaleViewSet(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.CreateModelMixin,
                  viewsets.GenericViewSet):
  permission_classes = (IsAuthenticated,)
  filterset_class = SaleFilter
  search_fields = ('notes', 'items__product__name', 'shop__name')
  ordering_fields = ('date', 'total_amount')

  def get_serializer_class(self):
    if self.action == 'create':
      return SaleCreateSerializer
    return SaleSerializer

  def get_queryset(self):
    shops, _ = resolve_shop_scope(
      self.request.user,
      self.request.query_params.get('shop'),
    )
    qs = Sale.objects.select_related('user', 'shop').prefetch_related('items__product').filter(shop__in=shops)
    if not self.request.user.is_admin:
      qs = qs.filter(user=self.request.user)
    return qs

  def create(self, request, *args, **kwargs):
    serializer = self.get_serializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    sale = serializer.save()
    return Response(SaleSerializer(sale).data, status=status.HTTP_201_CREATED)

  @action(detail=True, methods=['get'])
  def invoice(self, request, pk=None):
    sale = self.get_object()
    items = [
      {
        'product': item.product.name,
        'quantity': item.quantity,
        'price': str(item.price),
        'subtotal': str(item.subtotal),
      }
      for item in sale.items.select_related('product').all()
    ]
    return Response({
      'sale_id': sale.pk,
      'shop': sale.shop.name,
      'date': sale.date.isoformat(),
      'user': sale.user.get_full_name() or sale.user.username,
      'total_amount': str(sale.total_amount),
      'notes': sale.notes,
      'items': items,
    })
