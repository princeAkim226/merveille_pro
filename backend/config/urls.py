"""URLs principales du projet Merveille Pro."""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.users.urls')),
    path('api/', include('apps.shops.urls')),
    path('api/', include('apps.products.urls')),
    path('api/', include('apps.sales.urls')),
    path('api/', include('apps.inventory.urls')),
    path('api/', include('apps.finance.urls')),
    path('api/', include('apps.core.urls')),
]
