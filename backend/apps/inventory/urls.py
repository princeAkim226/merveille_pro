from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.inventory.views import InventoryViewSet, StockMovementViewSet

router = DefaultRouter()
router.register('stock', StockMovementViewSet, basename='stock')
router.register('inventory', InventoryViewSet, basename='inventory')

urlpatterns = [
  path('', include(router.urls)),
]
