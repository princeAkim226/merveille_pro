from django.db import migrations, models


class Migration(migrations.Migration):

  dependencies = [
    ('inventory', '0003_inventory'),
  ]

  operations = [
    migrations.AddField(
      model_name='inventoryline',
      name='counted_at',
      field=models.DateTimeField(blank=True, null=True, verbose_name='Date du comptage'),
    ),
    migrations.AlterModelOptions(
      name='inventoryline',
      options={'ordering': ['product__category__name', 'product__subcategory__name', 'product__name'], 'verbose_name': 'Ligne inventaire', 'verbose_name_plural': 'Lignes inventaire'},
    ),
  ]
