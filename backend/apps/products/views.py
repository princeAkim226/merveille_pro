from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.products.csv_import import import_products_from_csv
from apps.products.filters import ProductFilter
from apps.products.models import Category, Product, SubCategory
from apps.products.serializers import CategorySerializer, ProductSerializer, SubCategorySerializer
from apps.shops.utils import require_shop_for_write, resolve_shop_scope
from apps.users.permissions import IsAdminOrReadOnly


class CategoryViewSet(viewsets.ModelViewSet):
  queryset = Category.objects.prefetch_related('subcategories').all()
  serializer_class = CategorySerializer
  permission_classes = (IsAdminOrReadOnly,)
  search_fields = ('name',)
  ordering_fields = ('name', 'created_at')


class SubCategoryViewSet(viewsets.ModelViewSet):
  serializer_class = SubCategorySerializer
  permission_classes = (IsAdminOrReadOnly,)
  search_fields = ('name', 'category__name')
  ordering_fields = ('name', 'created_at')

  def get_queryset(self):
    qs = SubCategory.objects.select_related('category')
    category_id = self.request.query_params.get('category')
    if category_id:
      qs = qs.filter(category_id=category_id)
    return qs


class ProductViewSet(viewsets.ModelViewSet):
  serializer_class = ProductSerializer
  permission_classes = (IsAuthenticated,)
  filterset_class = ProductFilter
  search_fields = ('name', 'brand', 'category__name', 'subcategory__name', 'shop__name', 'variant', 'shelf_location', 'spec_unit')
  ordering_fields = ('name', 'selling_price', 'stock_quantity', 'created_at')

  def get_queryset(self):
    shops, shop = resolve_shop_scope(
      self.request.user,
      self.request.query_params.get('shop'),
    )
    qs = Product.objects.select_related('category', 'subcategory', 'shop').filter(is_active=True, shop__in=shops)
    return qs

  def get_permissions(self):
    if self.action in ('create', 'update', 'partial_update', 'destroy', 'import_csv'):
      return [IsAdminOrReadOnly()]
    return super().get_permissions()

  def perform_destroy(self, instance):
    instance.is_active = False
    instance.save()

  @action(detail=False, methods=['post'], url_path='import-csv')
  def import_csv(self, request):
    """
    Importe des produits depuis un CSV.
    Body JSON : { "shop": <id>, "csv": "<contenu>", "update_existing": true }
    ou multipart : fichier `file` + champ `shop`.
    """
    shop_id = request.data.get('shop') or request.query_params.get('shop')
    shop = require_shop_for_write(request.user, shop_id)

    csv_text = request.data.get('csv')
    upload = request.FILES.get('file')
    if upload is not None:
      raw = upload.read()
      for encoding in ('utf-8-sig', 'utf-8', 'cp1252', 'latin-1'):
        try:
          csv_text = raw.decode(encoding)
          break
        except UnicodeDecodeError:
          continue
      else:
        return Response(
          {'detail': 'Impossible de lire le fichier (encodage non supporté).'},
          status=status.HTTP_400_BAD_REQUEST,
        )

    if not csv_text:
      return Response(
        {'detail': 'Fournissez un champ « csv » ou un fichier « file ».'},
        status=status.HTTP_400_BAD_REQUEST,
      )

    update_existing = request.data.get('update_existing', True)
    if isinstance(update_existing, str):
      update_existing = update_existing.strip().lower() in ('1', 'true', 'oui', 'yes')

    try:
      result = import_products_from_csv(
        shop=shop,
        csv_text=csv_text,
        update_existing=bool(update_existing),
      )
    except ValueError as exc:
      return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return Response({
      'shop': shop.id,
      'shop_name': shop.name,
      **result,
    })
