from django.db import models


class Shop(models.Model):
  """Boutique / point de vente d'une même entreprise."""
  name = models.CharField(max_length=150)
  code = models.CharField(max_length=30, unique=True, help_text='Code court ex: BOUTIQUE-A')
  address = models.CharField(max_length=255, blank=True)
  phone = models.CharField(max_length=30, blank=True)
  is_active = models.BooleanField(default=True)
  created_at = models.DateTimeField(auto_now_add=True)

  class Meta:
    verbose_name = 'Boutique'
    verbose_name_plural = 'Boutiques'
    ordering = ['name']

  def __str__(self):
    return self.name
