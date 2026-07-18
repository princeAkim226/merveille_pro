from django.db import migrations, models





class Migration(migrations.Migration):



  dependencies = [

    ('products', '0002_multi_boutiques'),

  ]



  operations = [

    migrations.AlterModelOptions(

      name='product',

      options={'ordering': ['name'], 'verbose_name': 'Article', 'verbose_name_plural': 'Articles'},

    ),

    migrations.AddField(

      model_name='product',

      name='brand',

      field=models.CharField(blank=True, max_length=80, verbose_name='Marque'),

    ),

    migrations.AddField(

      model_name='product',

      name='page_count',

      field=models.PositiveIntegerField(blank=True, null=True, verbose_name='Nombre de pages'),

    ),

    migrations.AddField(

      model_name='product',

      name='pack_price',

      field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='Prix du paquet'),

    ),

    migrations.AddField(

      model_name='product',

      name='school_level',

      field=models.CharField(blank=True, choices=[('', '—'), ('CP', 'CP'), ('CE1', 'CE1'), ('CE2', 'CE2'), ('CM1', 'CM1'), ('CM2', 'CM2'), ('COLLEGE', 'Collège'), ('LYCEE', 'Lycée'), ('UNIVERSITE', 'Université')], default='', max_length=20, verbose_name='Niveau scolaire'),

    ),

    migrations.AddField(

      model_name='product',

      name='shelf_location',

      field=models.CharField(blank=True, help_text='Ex : Étagère A — case 3', max_length=60, verbose_name='Emplacement étagère'),

    ),

    migrations.AddField(

      model_name='product',

      name='units_per_pack',

      field=models.PositiveIntegerField(default=1, verbose_name='Unités par paquet'),

    ),

    migrations.AlterField(

      model_name='product',

      name='selling_price',

      field=models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Prix unitaire'),

    ),

  ]


