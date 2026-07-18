from django.contrib import admin

from apps.shops.models import Shop


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
  list_display = ('name', 'code', 'phone', 'is_active')
  search_fields = ('name', 'code')
