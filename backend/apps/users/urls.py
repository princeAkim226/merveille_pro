from django.urls import path

from apps.users.views import LoginView, MeView, UserDetailView, UserListCreateView

urlpatterns = [
  path('login/', LoginView.as_view(), name='auth-login'),
  path('me/', MeView.as_view(), name='auth-me'),
  path('users/', UserListCreateView.as_view(), name='user-list'),
  path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
]
