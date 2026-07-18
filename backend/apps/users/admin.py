from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.users.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
  list_display = ('username', 'email', 'role', 'is_active', 'is_staff')
  list_filter = ('role', 'is_active', 'is_staff')
  filter_horizontal = ('shops',)
  fieldsets = BaseUserAdmin.fieldsets + (
    ('Merveille Pro', {'fields': ('role', 'phone', 'shops')}),
  )
  add_fieldsets = BaseUserAdmin.add_fieldsets + (
    ('Merveille Pro', {'fields': ('role', 'phone')}),
  )
