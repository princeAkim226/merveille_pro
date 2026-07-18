from django.db import migrations, models


def copy_specs(apps, schema_editor):
  Product = apps.get_model('products', 'Product')
  for p in Product.objects.exclude(spec_quantity__isnull=True):
    if not p.spec_unit:
      p.spec_unit = 'pages'
      p.save(update_fields=['spec_unit'])


class Migration(migrations.Migration):

  dependencies = [
    ('products', '0003_librairie_fields'),
  ]

  operations = [
    migrations.RenameField(
      model_name='product',
      old_name='school_level',
      new_name='variant',
    ),
    migrations.RenameField(
      model_name='product',
      old_name='page_count',
      new_name='spec_quantity',
    ),
    migrations.AlterField(
      model_name='product',
      name='variant',
      field=models.CharField(
        blank=True,
        default='',
        max_length=80,
        verbose_name='Variante',
        help_text='Niveau scolaire, teinte, volume, taille…',
      ),
    ),
    migrations.AlterField(
      model_name='product',
      name='spec_quantity',
      field=models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='Quantité spécification',
        help_text='Ex : 200 (pages), 50 (ml), 250 (g)',
      ),
    ),
    migrations.AddField(
      model_name='product',
      name='spec_unit',
      field=models.CharField(
        blank=True,
        default='',
        max_length=20,
        verbose_name='Unité spécification',
        help_text='pages, ml, g, cl, unités…',
      ),
    ),
    migrations.AlterField(
      model_name='product',
      name='shelf_location',
      field=models.CharField(
        blank=True,
        help_text='Ex : Rayon A — étagère 3',
        max_length=60,
        verbose_name='Emplacement',
      ),
    ),
    migrations.AlterModelOptions(
      name='product',
      options={'ordering': ['name'], 'verbose_name': 'Produit', 'verbose_name_plural': 'Produits'},
    ),
    migrations.RunPython(copy_specs, migrations.RunPython.noop),
  ]
