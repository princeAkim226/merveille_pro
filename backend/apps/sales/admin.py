from django.contrib import admin

from apps.sales.models import Sale, SaleItem


class SaleItemInline(admin.TabularInline):
  model = SaleItem
  extra = 0
  readonly_fields = ('product', 'quantity', 'price')


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
  list_display = ('id', 'date', 'total_amount', 'user')
  list_filter = ('date', 'user')
  inlines = [SaleItemInline]
