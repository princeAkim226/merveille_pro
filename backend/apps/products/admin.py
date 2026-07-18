from django.contrib import admin

from apps.products.models import Category, Product, SubCategory


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
  search_fields = ('name',)


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
  list_display = ('name', 'category')
  list_filter = ('category',)
  search_fields = ('name', 'category__name')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
  list_display = ('name', 'category', 'subcategory', 'selling_price', 'stock_quantity', 'is_active')
  list_filter = ('category', 'subcategory', 'is_active')
  search_fields = ('name',)
