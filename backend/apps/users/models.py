"""Modèle utilisateur étendu avec rôles."""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
  class Role(models.TextChoices):
    ADMIN = 'admin', 'Administrateur'
    VENDEUR = 'vendeur', 'Vendeur'

  role = models.CharField(
    max_length=20,
    choices=Role.choices,
    default=Role.VENDEUR,
  )
  phone = models.CharField(max_length=20, blank=True)
  shops = models.ManyToManyField(
    'shops.Shop',
    blank=True,
    related_name='users',
    verbose_name='Boutiques assignées',
  )

  class Meta:
    verbose_name = 'Utilisateur'
    verbose_name_plural = 'Utilisateurs'

  @property
  def is_admin(self):
    return self.role == self.Role.ADMIN or self.is_superuser

  @property
  def is_vendeur(self):
    return self.role == self.Role.VENDEUR
