"""URLs principales du projet Merveille Pro."""
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path


def root_redirect(_request):
  """Navigateur sur merveille.raaga-bf.com → page de téléchargement APK."""
  return redirect('https://dl.merveille.raaga-bf.com/', permanent=False)


urlpatterns = [
    path('', root_redirect, name='root'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.users.urls')),
    path('api/', include('apps.shops.urls')),
    path('api/', include('apps.products.urls')),
    path('api/', include('apps.sales.urls')),
    path('api/', include('apps.inventory.urls')),
    path('api/', include('apps.finance.urls')),
    path('api/', include('apps.core.urls')),
]
