from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.shops.views import ShopViewSet

router = DefaultRouter()
router.register('shops', ShopViewSet, basename='shop')

urlpatterns = [
  path('', include(router.urls)),
]
