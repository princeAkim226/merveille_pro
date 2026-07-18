from django.db import migrations


def create_default_shop(apps, schema_editor):
  Shop = apps.get_model('shops', 'Shop')
  Product = apps.get_model('products', 'Product')
  Sale = apps.get_model('sales', 'Sale')
  Expense = apps.get_model('finance', 'Expense')

  shop_a, _ = Shop.objects.get_or_create(
    code='BOUTIQUE-A',
    defaults={'name': 'Boutique A — Centre-ville', 'address': 'Avenue principale'},
  )
  Shop.objects.get_or_create(
    code='BOUTIQUE-B',
    defaults={'name': 'Boutique B — Marché', 'address': 'Marché central'},
  )

  for product in Product.objects.filter(shop__isnull=True).iterator():
    base_name = product.name
    candidate = base_name
    n = 1
    while Product.objects.filter(shop=shop_a, name=candidate).exclude(pk=product.pk).exists():
      candidate = f'{base_name} ({n})'
      n += 1
    product.name = candidate
    product.shop_id = shop_a.pk
    product.save(update_fields=['shop', 'name'])

  Sale.objects.filter(shop__isnull=True).update(shop=shop_a)
  Expense.objects.filter(shop__isnull=True).update(shop=shop_a)


class Migration(migrations.Migration):
  atomic = False

  dependencies = [
    ('shops', '0001_multi_boutiques'),
    ('products', '0002_multi_boutiques'),
    ('sales', '0003_multi_boutiques'),
    ('finance', '0003_multi_boutiques'),
  ]

  operations = [
    migrations.RunPython(create_default_shop, migrations.RunPython.noop),
  ]
