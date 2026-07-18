from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

  dependencies = [
    ('shops', '0002_populate_default_shop'),
    ('products', '0004_generalize_product_fields'),
    ('inventory', '0002_initial'),
  ]

  operations = [
    migrations.AlterField(
      model_name='stockmovement',
      name='type',
      field=models.CharField(
        choices=[('IN', 'Entrée'), ('OUT', 'Sortie'), ('ADJ', 'Ajustement inventaire')],
        max_length=4,
      ),
    ),
    migrations.CreateModel(
      name='InventorySession',
      fields=[
        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        ('title', models.CharField(blank=True, max_length=120)),
        ('status', models.CharField(choices=[('OPEN', 'En cours'), ('VALIDATED', 'Validé'), ('CANCELLED', 'Annulé')], default='OPEN', max_length=12)),
        ('notes', models.TextField(blank=True)),
        ('created_at', models.DateTimeField(auto_now_add=True)),
        ('validated_at', models.DateTimeField(blank=True, null=True)),
        ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='inventory_sessions', to=settings.AUTH_USER_MODEL)),
        ('shop', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='inventory_sessions', to='shops.shop')),
      ],
      options={
        'verbose_name': 'Inventaire',
        'verbose_name_plural': 'Inventaires',
        'ordering': ['-created_at'],
      },
    ),
    migrations.CreateModel(
      name='InventoryLine',
      fields=[
        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        ('expected_quantity', models.PositiveIntegerField()),
        ('counted_quantity', models.PositiveIntegerField(blank=True, null=True)),
        ('notes', models.CharField(blank=True, max_length=200)),
        ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='inventory_lines', to='products.product')),
        ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lines', to='inventory.inventorysession')),
      ],
      options={
        'verbose_name': 'Ligne inventaire',
        'verbose_name_plural': 'Lignes inventaire',
        'ordering': ['product__name'],
        'unique_together': {('session', 'product')},
      },
    ),
  ]
