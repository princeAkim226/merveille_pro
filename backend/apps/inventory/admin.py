from django.contrib import admin

from apps.inventory.models import StockMovement


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
  list_display = ('product', 'type', 'quantity', 'date', 'user')
  list_filter = ('type', 'date')
