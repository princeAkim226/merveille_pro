"""Commande pour initialiser les données de démonstration multi-secteurs."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.products.models import Category, Product, SubCategory
from apps.shops.models import Shop

User = get_user_model()

DEMO_SUBCATEGORIES = {
  'Cahiers & copies': ['Double ligne', 'Quadrillé', 'Grand format'],
  'Manuels scolaires': ['Primaire', 'Collège'],
  'Stylos & crayons': ['Bille', 'Gel', 'Feutre'],
  'Soins visage': ['Hydratation', 'Nettoyage'],
  'Maquillage': ['Lèvres', 'Yeux'],
  'Cheveux': ['Soins', 'Coiffants'],
  'Parfums': ['Femme', 'Homme'],
  'Hygiène': ['Corps', 'Mains'],
}

DEMO_PRODUCTS = [
  {
    'name': 'Cahier 200 pages — double ligne',
    'category': 'Cahiers & copies',
    'subcategory': 'Double ligne',
    'spec_quantity': 200,
    'spec_unit': 'pages',
    'purchase_price': '200',
    'selling_price': '300',
    'pack_price': '1000',
    'units_per_pack': 4,
    'stock_quantity': 80,
    'shelf_location': 'Rayon A — 1',
  },
  {
    'name': 'Manuel CM2 — Exercices corrigés',
    'category': 'Manuels scolaires',
    'subcategory': 'Primaire',
    'variant': 'CM2',
    'purchase_price': '900',
    'selling_price': '1200',
    'stock_quantity': 25,
  },
  {
    'name': 'Stylo bille bleu',
    'category': 'Stylos & crayons',
    'subcategory': 'Bille',
    'brand': 'Schneider',
    'purchase_price': '150',
    'selling_price': '250',
    'pack_price': '100',
    'units_per_pack': 2,
    'stock_quantity': 200,
  },
  {
    'name': 'Crème hydratante visage',
    'category': 'Soins visage',
    'subcategory': 'Hydratation',
    'brand': 'Nivea',
    'variant': 'Peaux normales',
    'spec_quantity': 50,
    'spec_unit': 'ml',
    'purchase_price': '1200',
    'selling_price': '1800',
    'stock_quantity': 30,
    'shelf_location': 'Rayon beauté — 1',
  },
  {
    'name': 'Rouge à lèvres mat',
    'category': 'Maquillage',
    'subcategory': 'Lèvres',
    'brand': 'Maybelline',
    'variant': 'Teinte 03',
    'spec_quantity': 4,
    'spec_unit': 'g',
    'purchase_price': '1500',
    'selling_price': '2500',
    'stock_quantity': 18,
  },
  {
    'name': 'Huile capillaire',
    'category': 'Cheveux',
    'subcategory': 'Soins',
    'brand': 'L\'Oréal',
    'variant': 'Nutrition',
    'spec_quantity': 100,
    'spec_unit': 'ml',
    'purchase_price': '2200',
    'selling_price': '3500',
    'stock_quantity': 15,
  },
  {
    'name': 'Parfum eau de toilette',
    'category': 'Parfums',
    'subcategory': 'Femme',
    'variant': 'Vanille',
    'spec_quantity': 50,
    'spec_unit': 'ml',
    'purchase_price': '4500',
    'selling_price': '7000',
    'stock_quantity': 10,
  },
  {
    'name': 'Gel douche',
    'category': 'Hygiène',
    'subcategory': 'Corps',
    'spec_quantity': 250,
    'spec_unit': 'ml',
    'purchase_price': '800',
    'selling_price': '1200',
    'pack_price': '2000',
    'units_per_pack': 2,
    'stock_quantity': 40,
  },
]

ALL_CATEGORIES = [
  'Cahiers & copies',
  'Manuels scolaires',
  'Stylos & crayons',
  'Soins visage',
  'Maquillage',
  'Cheveux',
  'Parfums',
  'Hygiène',
]


class Command(BaseCommand):
  help = 'Crée admin, vendeur, boutiques et produits de démonstration'

  def handle(self, *args, **options):
    shop_a, _ = Shop.objects.get_or_create(
      code='SHOP-A',
      defaults={
        'name': 'Boutique principale',
        'address': 'Centre-ville',
        'phone': '+226 00 00 00 00',
      },
    )
    shop_b, _ = Shop.objects.get_or_create(
      code='SHOP-B',
      defaults={
        'name': 'Boutique secondaire',
        'address': 'Marché central',
        'phone': '+226 00 00 00 01',
      },
    )

    admin, created = User.objects.get_or_create(
      username='admin',
      defaults={
        'email': 'admin@merveille.local',
        'role': User.Role.ADMIN,
        'is_staff': True,
        'is_superuser': True,
      },
    )
    if created:
      admin.set_password('admin123')
      admin.save()
      self.stdout.write(self.style.SUCCESS('Admin créé (admin / admin123)'))
    else:
      self.stdout.write('Admin existe déjà')

    vendeur, created = User.objects.get_or_create(
      username='vendeur',
      defaults={'email': 'vendeur@merveille.local', 'role': User.Role.VENDEUR},
    )
    if created:
      vendeur.set_password('vendeur123')
      vendeur.save()
      self.stdout.write(self.style.SUCCESS('Vendeur créé (vendeur / vendeur123)'))
    vendeur.shops.set([shop_a])

    categories = {}
    subcategories = {}
    for cat_name in ALL_CATEGORIES:
      cat, _ = Category.objects.get_or_create(name=cat_name)
      categories[cat_name] = cat
      for sub_name in DEMO_SUBCATEGORIES.get(cat_name, []):
        sub, _ = SubCategory.objects.get_or_create(category=cat, name=sub_name)
        subcategories[(cat_name, sub_name)] = sub

    for shop in [shop_a, shop_b]:
      for item in DEMO_PRODUCTS:
        cat = categories[item['category']]
        sub = subcategories.get((item['category'], item.get('subcategory', '')))
        defaults = {
          'category': cat,
          'subcategory': sub,
          'brand': item.get('brand', ''),
          'variant': item.get('variant', ''),
          'spec_quantity': item.get('spec_quantity'),
          'spec_unit': item.get('spec_unit', ''),
          'shelf_location': item.get('shelf_location', ''),
          'purchase_price': Decimal(item['purchase_price']),
          'selling_price': Decimal(item['selling_price']),
          'pack_price': Decimal(item['pack_price']) if item.get('pack_price') else None,
          'units_per_pack': item.get('units_per_pack', 1),
          'stock_quantity': item['stock_quantity'],
          'alert_threshold': 5,
        }
        Product.objects.get_or_create(name=item['name'], shop=shop, defaults=defaults)

    self.stdout.write(self.style.SUCCESS(f'Boutiques : {shop_a.name}, {shop_b.name}'))
    self.stdout.write(self.style.SUCCESS('Données de démonstration prêtes.'))
