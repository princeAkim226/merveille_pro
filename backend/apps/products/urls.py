from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.products.views import CategoryViewSet, ProductViewSet, SubCategoryViewSet

router = DefaultRouter()
router.register('categories', CategoryViewSet, basename='category')
router.register('subcategories', SubCategoryViewSet, basename='subcategory')
router.register('products', ProductViewSet, basename='product')

urlpatterns = [
  path('', include(router.urls)),
]
