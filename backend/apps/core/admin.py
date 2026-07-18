from django.contrib import admin

from apps.core.models import ActionLog, CompanySettings


@admin.register(CompanySettings)
class CompanySettingsAdmin(admin.ModelAdmin):
  list_display = ('company_name', 'phone', 'email', 'updated_at')

  def has_add_permission(self, request):
    return not CompanySettings.objects.exists()

  def has_delete_permission(self, request, obj=None):
    return False


@admin.register(ActionLog)
class ActionLogAdmin(admin.ModelAdmin):
  list_display = ('action', 'user', 'created_at')
  list_filter = ('action', 'created_at')
  readonly_fields = ('user', 'action', 'details', 'created_at')
