from django.utils import timezone

from rest_framework import mixins, status, viewsets

from rest_framework.decorators import action

from rest_framework.permissions import IsAuthenticated

from rest_framework.response import Response



from apps.core.services import log_action

from apps.inventory.filters import StockMovementFilter

from apps.inventory.models import InventoryLine, InventorySession, StockMovement

from apps.inventory.serializers import (

  InventoryLineUpdateSerializer,

  InventorySessionCreateSerializer,

  InventorySessionDetailSerializer,

  InventorySessionListSerializer,

  InventoryValidateSerializer,

  StockEntrySerializer,

  StockMovementSerializer,

)

from apps.products.models import Product

from apps.products.serializers import ProductSerializer

from apps.shops.utils import resolve_shop_scope

from apps.users.permissions import IsAdminOrReadOnly

from django.db import models





def _session_queryset():

  return InventorySession.objects.select_related('shop', 'created_by').prefetch_related(

    'lines__product__category',

    'lines__product__subcategory',

  )





class StockMovementViewSet(mixins.ListModelMixin,

                           mixins.RetrieveModelMixin,

                           viewsets.GenericViewSet):

  serializer_class = StockMovementSerializer

  permission_classes = (IsAuthenticated,)

  filterset_class = StockMovementFilter

  ordering_fields = ('date', 'quantity')



  def get_queryset(self):

    shops, _ = resolve_shop_scope(

      self.request.user,

      self.request.query_params.get('shop'),

    )

    return StockMovement.objects.select_related('product', 'user', 'product__shop').filter(

      product__shop__in=shops,

    )



  @action(detail=False, methods=['post'], permission_classes=[IsAdminOrReadOnly])

  def entry(self, request):

    serializer = StockEntrySerializer(data=request.data, context={'request': request})

    serializer.is_valid(raise_exception=True)

    movement = serializer.save()

    return Response(StockMovementSerializer(movement).data, status=status.HTTP_201_CREATED)



  @action(detail=False, methods=['get'])

  def low_stock(self, request):

    shops, _ = resolve_shop_scope(

      request.user,

      request.query_params.get('shop'),

    )

    products = Product.objects.filter(

      is_active=True,

      shop__in=shops,

      stock_quantity__lte=models.F('alert_threshold'),

    ).select_related('category', 'subcategory', 'shop')

    return Response(ProductSerializer(products, many=True, context={'request': request}).data)





class InventoryViewSet(mixins.ListModelMixin,

                       mixins.RetrieveModelMixin,

                       mixins.CreateModelMixin,

                       viewsets.GenericViewSet):

  permission_classes = (IsAuthenticated,)

  ordering_fields = ('created_at', 'status')



  def get_serializer_class(self):

    if self.action == 'create':

      return InventorySessionCreateSerializer

    if self.action == 'retrieve':

      return InventorySessionDetailSerializer

    return InventorySessionListSerializer



  def get_queryset(self):

    shops, _ = resolve_shop_scope(

      self.request.user,

      self.request.query_params.get('shop'),

    )

    return InventorySession.objects.filter(shop__in=shops).select_related('shop', 'created_by')



  def get_permissions(self):

    if self.action in ('create', 'validate', 'cancel', 'update_line'):

      return [IsAdminOrReadOnly()]

    return super().get_permissions()



  def create(self, request, *args, **kwargs):

    serializer = InventorySessionCreateSerializer(data=request.data, context={'request': request})

    serializer.is_valid(raise_exception=True)

    session = serializer.save()

    session = _session_queryset().get(pk=session.pk)

    data = InventorySessionDetailSerializer(session).data

    return Response(data, status=status.HTTP_201_CREATED)



  @action(detail=True, methods=['patch'], url_path='lines/(?P<line_id>[^/.]+)')

  def update_line(self, request, pk=None, line_id=None):

    session = self.get_object()

    if session.status != InventorySession.Status.OPEN:

      return Response({'detail': 'Inventaire non modifiable.'}, status=status.HTTP_400_BAD_REQUEST)



    line = InventoryLine.objects.filter(session=session, pk=line_id).first()

    if not line:

      return Response({'detail': 'Ligne introuvable.'}, status=status.HTTP_404_NOT_FOUND)



    serializer = InventoryLineUpdateSerializer(line, data=request.data, partial=True)

    serializer.is_valid(raise_exception=True)

    serializer.save()

    session = _session_queryset().get(pk=session.pk)

    return Response(InventorySessionDetailSerializer(session).data)



  @action(detail=True, methods=['post'])

  def validate(self, request, pk=None):

    session = self.get_object()

    serializer = InventoryValidateSerializer(
      data={},
      context={'request': request, 'session': session},
    )
    serializer.is_valid(raise_exception=True)

    serializer.save()

    session = _session_queryset().get(pk=session.pk)

    return Response(InventorySessionDetailSerializer(session).data)



  @action(detail=True, methods=['post'])

  def cancel(self, request, pk=None):

    session = self.get_object()

    if session.status != InventorySession.Status.OPEN:

      return Response({'detail': 'Inventaire non annulable.'}, status=status.HTTP_400_BAD_REQUEST)

    session.status = InventorySession.Status.CANCELLED

    session.save(update_fields=['status'])

    log_action(request.user, 'inventory_cancel', f'Inventaire #{session.pk} annulé')

    session = _session_queryset().get(pk=session.pk)

    return Response(InventorySessionDetailSerializer(session).data)



  @action(detail=True, methods=['post'], url_path='fill-uncounted')

  def fill_uncounted(self, request, pk=None):

    """Remplit les lignes non comptées avec la quantité théorique."""

    session = self.get_object()

    if session.status != InventorySession.Status.OPEN:

      return Response({'detail': 'Inventaire non modifiable.'}, status=status.HTTP_400_BAD_REQUEST)

    now = timezone.now()

    session.lines.filter(counted_quantity__isnull=True).update(

      counted_quantity=models.F('expected_quantity'),

      counted_at=now,

    )

    session = _session_queryset().get(pk=session.pk)

    return Response(InventorySessionDetailSerializer(session).data)



  def retrieve(self, request, *args, **kwargs):
    session = _session_queryset().get(pk=self.get_object().pk)
    serializer = InventorySessionDetailSerializer(session)
    return Response(serializer.data)


