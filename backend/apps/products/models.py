from django.db import models


class Category(models.Model):
  name = models.CharField(max_length=100, unique=True)
  created_at = models.DateTimeField(auto_now_add=True)

  class Meta:
    verbose_name = 'Catégorie'
    verbose_name_plural = 'Catégories'
    ordering = ['name']

  def __str__(self):
    return self.name


class SubCategory(models.Model):
  category = models.ForeignKey(
    Category,
    on_delete=models.CASCADE,
    related_name='subcategories',
  )
  name = models.CharField(max_length=100)
  created_at = models.DateTimeField(auto_now_add=True)

  class Meta:
    verbose_name = 'Sous-catégorie'
    verbose_name_plural = 'Sous-catégories'
    ordering = ['name']
    unique_together = ('category', 'name')

  def __str__(self):
    return f'{self.category.name} — {self.name}'


class Product(models.Model):
  shop = models.ForeignKey(
    'shops.Shop',
    on_delete=models.PROTECT,
    related_name='products',
    null=True,
    blank=True,
  )
  name = models.CharField(max_length=200)
  category = models.ForeignKey(
    Category,
    on_delete=models.PROTECT,
    related_name='products',
  )
  subcategory = models.ForeignKey(
    SubCategory,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='products',
    verbose_name='Sous-catégorie',
  )
  brand = models.CharField(max_length=80, blank=True, verbose_name='Marque')
  variant = models.CharField(
    max_length=80,
    blank=True,
    default='',
    verbose_name='Variante',
    help_text='Niveau scolaire, teinte, volume, taille…',
  )
  spec_quantity = models.PositiveIntegerField(
    null=True,
    blank=True,
    verbose_name='Quantité spécification',
    help_text='Ex : 200 (pages), 50 (ml), 250 (g)',
  )
  spec_unit = models.CharField(
    max_length=20,
    blank=True,
    default='',
    verbose_name='Unité spécification',
    help_text='pages, ml, g, cl, unités…',
  )
  shelf_location = models.CharField(
    max_length=60,
    blank=True,
    verbose_name='Emplacement',
    help_text='Ex : Rayon A — étagère 3',
  )
  purchase_price = models.DecimalField(max_digits=12, decimal_places=2)
  selling_price = models.DecimalField(
    max_digits=12,
    decimal_places=2,
    verbose_name='Prix unitaire',
  )
  pack_price = models.DecimalField(
    max_digits=12,
    decimal_places=2,
    null=True,
    blank=True,
    verbose_name='Prix du paquet',
  )
  units_per_pack = models.PositiveIntegerField(
    default=1,
    verbose_name='Unités par paquet',
  )
  stock_quantity = models.PositiveIntegerField(default=0)
  alert_threshold = models.PositiveIntegerField(default=5)
  is_active = models.BooleanField(default=True)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  class Meta:
    verbose_name = 'Produit'
    verbose_name_plural = 'Produits'
    ordering = ['name']
    unique_together = ('shop', 'name')

  def __str__(self):
    return self.name

  @property
  def is_low_stock(self):
    return self.stock_quantity <= self.alert_threshold

  @property
  def profit_margin(self):
    return self.selling_price - self.purchase_price

  @property
  def has_pack_pricing(self):
    return self.pack_price is not None and self.units_per_pack > 1

  @property
  def spec_label(self):
    if self.spec_quantity is None:
      return ''
    if self.spec_unit:
      return f'{self.spec_quantity} {self.spec_unit}'
    return str(self.spec_quantity)
