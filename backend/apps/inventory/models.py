from django.conf import settings
from django.db import models

from apps.products.models import Product


class StockMovement(models.Model):
  class MovementType(models.TextChoices):
    IN = 'IN', 'Entrée'
    OUT = 'OUT', 'Sortie'
    ADJ = 'ADJ', 'Ajustement inventaire'

  product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='stock_movements')
  type = models.CharField(max_length=4, choices=MovementType.choices)
  quantity = models.PositiveIntegerField()
  date = models.DateTimeField(auto_now_add=True)
  user = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='stock_movements',
  )
  reference = models.CharField(max_length=100, blank=True)
  notes = models.TextField(blank=True)

  class Meta:
    verbose_name = 'Mouvement de stock'
    verbose_name_plural = 'Mouvements de stock'
    ordering = ['-date']

  def __str__(self):
    return f'{self.get_type_display()} — {self.product.name} x{self.quantity}'


class InventorySession(models.Model):
  class Status(models.TextChoices):
    OPEN = 'OPEN', 'En cours'
    VALIDATED = 'VALIDATED', 'Validé'
    CANCELLED = 'CANCELLED', 'Annulé'

  shop = models.ForeignKey('shops.Shop', on_delete=models.PROTECT, related_name='inventory_sessions')
  title = models.CharField(max_length=120, blank=True)
  status = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN)
  notes = models.TextField(blank=True)
  created_by = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.SET_NULL,
    null=True,
    related_name='inventory_sessions',
  )
  created_at = models.DateTimeField(auto_now_add=True)
  validated_at = models.DateTimeField(null=True, blank=True)

  class Meta:
    verbose_name = 'Inventaire'
    verbose_name_plural = 'Inventaires'
    ordering = ['-created_at']

  def __str__(self):
    return self.title or f'Inventaire #{self.pk}'


class InventoryLine(models.Model):
  session = models.ForeignKey(InventorySession, on_delete=models.CASCADE, related_name='lines')
  product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='inventory_lines')
  expected_quantity = models.PositiveIntegerField()
  counted_quantity = models.PositiveIntegerField(null=True, blank=True)
  counted_at = models.DateTimeField(null=True, blank=True, verbose_name='Date du comptage')
  notes = models.CharField(max_length=200, blank=True)

  class Meta:
    verbose_name = 'Ligne inventaire'
    verbose_name_plural = 'Lignes inventaire'
    unique_together = ('session', 'product')
    ordering = ['product__category__name', 'product__subcategory__name', 'product__name']

  def __str__(self):
    return f'{self.product.name} — {self.expected_quantity} → {self.counted_quantity}'

  @property
  def difference(self):
    if self.counted_quantity is None:
      return None
    return self.counted_quantity - self.expected_quantity

  @property
  def product_name(self):
    return self.product.name
