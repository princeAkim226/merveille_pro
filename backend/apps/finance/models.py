from django.conf import settings
from django.db import models


class Expense(models.Model):
  shop = models.ForeignKey(
    'shops.Shop',
    on_delete=models.PROTECT,
    related_name='expenses',
    null=True,
    blank=True,
  )
  label = models.CharField(max_length=200)
  amount = models.DecimalField(max_digits=14, decimal_places=2)
  date = models.DateField()
  user = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='expenses',
  )
  notes = models.TextField(blank=True)
  created_at = models.DateTimeField(auto_now_add=True)

  class Meta:
    verbose_name = 'Dépense'
    verbose_name_plural = 'Dépenses'
    ordering = ['-date', '-created_at']

  def __str__(self):
    return f'{self.label} — {self.amount}'
