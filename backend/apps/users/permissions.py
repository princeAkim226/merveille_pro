from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
  def has_permission(self, request, view):
    return request.user.is_authenticated and request.user.is_admin


class IsAdminOrReadOnly(BasePermission):
  def has_permission(self, request, view):
    if request.method in ('GET', 'HEAD', 'OPTIONS'):
      return request.user.is_authenticated
    return request.user.is_authenticated and request.user.is_admin
