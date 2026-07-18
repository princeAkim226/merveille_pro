from django.urls import path

from apps.core.views import ActionLogListView, CompanySettingsView, DashboardView

urlpatterns = [
  path('dashboard/', DashboardView.as_view(), name='dashboard'),
  path('settings/', CompanySettingsView.as_view(), name='company-settings'),
  path('logs/', ActionLogListView.as_view(), name='action-logs'),
]
