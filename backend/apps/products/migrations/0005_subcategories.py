from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

  dependencies = [
    ('products', '0004_generalize_product_fields'),
  ]

  operations = [
    migrations.CreateModel(
      name='SubCategory',
      fields=[
        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        ('name', models.CharField(max_length=100)),
        ('created_at', models.DateTimeField(auto_now_add=True)),
        ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subcategories', to='products.category')),
      ],
      options={
        'verbose_name': 'Sous-catégorie',
        'verbose_name_plural': 'Sous-catégories',
        'ordering': ['name'],
        'unique_together': {('category', 'name')},
      },
    ),
    migrations.AddField(
      model_name='product',
      name='subcategory',
      field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products', to='products.subcategory', verbose_name='Sous-catégorie'),
    ),
  ]
