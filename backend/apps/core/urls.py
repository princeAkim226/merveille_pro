from django.urls import path

from apps.core.views import ActionLogListView, CompanySettingsView, DashboardView, HealthView

urlpatterns = [
  path('health/', HealthView.as_view(), name='health'),
  path('dashboard/', DashboardView.as_view(), name='dashboard'),
  path('settings/', CompanySettingsView.as_view(), name='company-settings'),
  path('logs/', ActionLogListView.as_view(), name='action-logs'),
]
