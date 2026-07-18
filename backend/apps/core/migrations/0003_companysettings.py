from django.db import migrations, models


def create_default_settings(apps, schema_editor):
  CompanySettings = apps.get_model('core', 'CompanySettings')
  CompanySettings.objects.get_or_create(
    pk=1,
    defaults={
      'company_name': 'Merveille Pro',
      'tagline': 'Gestion commerciale intelligente',
      'invoice_footer': 'Merci pour votre confiance !',
      'currency_label': 'F CFA',
    },
  )


class Migration(migrations.Migration):

  dependencies = [
    ('core', '0002_initial'),
  ]

  operations = [
    migrations.CreateModel(
      name='CompanySettings',
      fields=[
        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        ('company_name', models.CharField(default='Merveille Pro', max_length=120)),
        ('tagline', models.CharField(blank=True, default='Gestion commerciale intelligente', max_length=200)),
        ('address', models.TextField(blank=True)),
        ('phone', models.CharField(blank=True, max_length=30)),
        ('email', models.EmailField(blank=True, max_length=254)),
        ('website', models.CharField(blank=True, max_length=200)),
        ('tax_id', models.CharField(blank=True, max_length=80, verbose_name='N° fiscal / RCCM')),
        ('currency_label', models.CharField(default='F CFA', max_length=20)),
        ('invoice_footer', models.CharField(blank=True, default='Merci pour votre confiance !', max_length=300)),
        ('logo_base64', models.TextField(blank=True, help_text='Image PNG/JPEG encodée en base64')),
        ('updated_at', models.DateTimeField(auto_now=True)),
      ],
      options={
        'verbose_name': 'Paramètres entreprise',
        'verbose_name_plural': 'Paramètres entreprise',
      },
    ),
    migrations.RunPython(create_default_settings, migrations.RunPython.noop),
  ]
