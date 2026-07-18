from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.users.permissions import IsAdmin
from apps.users.serializers import (
  UserCreateSerializer,
  UserMeSerializer,
  UserSerializer,
  UserUpdateSerializer,
)

User = get_user_model()


class LoginView(TokenObtainPairView):
  """POST /api/auth/login — Authentification JWT."""
  permission_classes = (permissions.AllowAny,)


class MeView(APIView):
  """GET /api/auth/me — Profil de l'utilisateur connecté."""

  def get(self, request):
    return Response(UserMeSerializer(request.user).data)


class UserListCreateView(generics.ListCreateAPIView):
  """Liste et création d'utilisateurs (admin uniquement)."""
  queryset = User.objects.prefetch_related('shops').all().order_by('username')
  permission_classes = (IsAdmin,)

  def get_serializer_class(self):
    if self.request.method == 'POST':
      return UserCreateSerializer
    return UserSerializer


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
  queryset = User.objects.prefetch_related('shops').all()
  permission_classes = (IsAdmin,)

  def get_serializer_class(self):
    if self.request.method in ('PUT', 'PATCH'):
      return UserUpdateSerializer
    return UserSerializer

  def destroy(self, request, *args, **kwargs):
    user = self.get_object()
    if user == request.user:
      return Response(
        {'detail': 'Vous ne pouvez pas supprimer votre propre compte.'},
        status=status.HTTP_400_BAD_REQUEST,
      )
    return super().destroy(request, *args, **kwargs)
