from django.conf import settings
from django.db import models, transaction

from apps.products.models import Product


class Sale(models.Model):
  shop = models.ForeignKey(
    'shops.Shop',
    on_delete=models.PROTECT,
    related_name='sales',
    null=True,
    blank=True,
  )
  date = models.DateTimeField(auto_now_add=True)
  total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
  user = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.PROTECT,
    related_name='sales',
  )
  notes = models.TextField(blank=True)

  class Meta:
    verbose_name = 'Vente'
    verbose_name_plural = 'Ventes'
    ordering = ['-date']

  def __str__(self):
    return f'Vente #{self.pk} — {self.total_amount}'

  def recalculate_total(self):
    total = sum(item.subtotal for item in self.items.all())
    self.total_amount = total
    self.save(update_fields=['total_amount'])
    return total


class SaleItem(models.Model):
  sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
  product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='sale_items')
  quantity = models.PositiveIntegerField()
  price = models.DecimalField(max_digits=12, decimal_places=2)

  class Meta:
    verbose_name = 'Ligne de vente'
    verbose_name_plural = 'Lignes de vente'

  def __str__(self):
    return f'{self.product.name} x{self.quantity}'

  @property
  def subtotal(self):
    return self.price * self.quantity

  @property
  def profit(self):
    return (self.price - self.product.purchase_price) * self.quantity
