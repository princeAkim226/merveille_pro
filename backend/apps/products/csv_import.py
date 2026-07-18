"""Import de produits depuis un CSV (séparateur ; ou ,)."""
from __future__ import annotations

import csv
import io
from decimal import Decimal, InvalidOperation

from django.db import transaction

from apps.products.models import Category, Product, SubCategory


REQUIRED_COLUMNS = {'name', 'category', 'selling_price'}

OPTIONAL_DEFAULTS = {
  'subcategory': '',
  'brand': '',
  'variant': '',
  'spec_quantity': '',
  'spec_unit': '',
  'shelf_location': '',
  'purchase_price': '0',
  'pack_price': '',
  'units_per_pack': '1',
  'stock_quantity': '0',
  'alert_threshold': '5',
}


def _detect_dialect(sample: str) -> csv.Dialect:
  try:
    return csv.Sniffer().sniff(sample, delimiters=';,')
  except csv.Error:
    class Fallback(csv.Dialect):
      delimiter = ';'
      quotechar = '"'
      escapechar = None
      doublequote = True
      skipinitialspace = True
      lineterminator = '\n'
      quoting = csv.QUOTE_MINIMAL

    return Fallback()


def _parse_decimal(value, default='0') -> Decimal:
  raw = (value if value is not None else default)
  text = str(raw).strip().replace(' ', '').replace(',', '.')
  if text == '':
    text = default
  try:
    return Decimal(text)
  except (InvalidOperation, TypeError):
    return Decimal(default)


def _parse_int(value, default=0) -> int:
  raw = (value if value is not None else default)
  text = str(raw).strip().replace(' ', '')
  if text == '':
    return default
  try:
    return int(float(text.replace(',', '.')))
  except (ValueError, TypeError):
    return default


def _normalize_header(name: str) -> str:
  return (name or '').strip().lower().replace(' ', '_')


def import_products_from_csv(
  *,
  shop,
  csv_text: str,
  update_existing: bool = True,
) -> dict:
  """
  Importe des produits pour une boutique.
  Colonnes attendues (séparateur ; ou ,) :
  name;category;subcategory;brand;variant;spec_quantity;spec_unit;shelf_location;
  purchase_price;selling_price;pack_price;units_per_pack;stock_quantity;alert_threshold
  """
  if not csv_text or not csv_text.strip():
    raise ValueError('Fichier CSV vide.')

  # Enlever BOM UTF-8
  if csv_text.startswith('\ufeff'):
    csv_text = csv_text[1:]

  sample = csv_text[:4096]
  dialect = _detect_dialect(sample)
  reader = csv.DictReader(io.StringIO(csv_text), dialect=dialect)
  if not reader.fieldnames:
    raise ValueError('En-têtes CSV introuvables.')

  field_map = {_normalize_header(h): h for h in reader.fieldnames if h}
  missing = REQUIRED_COLUMNS - set(field_map)
  if missing:
    raise ValueError(
      f'Colonnes obligatoires manquantes : {", ".join(sorted(missing))}. '
      f'Trouvé : {", ".join(reader.fieldnames)}'
    )

  created = 0
  updated = 0
  skipped = 0
  errors: list[str] = []

  with transaction.atomic():
    for index, raw in enumerate(reader, start=2):
      try:
        def col(key: str, default=''):
          header = field_map.get(key)
          if header is None:
            return OPTIONAL_DEFAULTS.get(key, default)
          value = raw.get(header)
          if value is None or str(value).strip() == '':
            return OPTIONAL_DEFAULTS.get(key, default)
          return str(value).strip()

        name = col('name')
        category_name = col('category')
        if not name or not category_name:
          skipped += 1
          continue

        selling_price = _parse_decimal(col('selling_price'), '0')
        purchase_price = _parse_decimal(col('purchase_price'), '0')
        if selling_price <= 0 and purchase_price > 0:
          selling_price = purchase_price
        if purchase_price <= 0 and selling_price > 0:
          purchase_price = selling_price

        category, _ = Category.objects.get_or_create(name=category_name)

        subcategory = None
        subcategory_name = col('subcategory')
        if subcategory_name:
          subcategory, _ = SubCategory.objects.get_or_create(
            category=category,
            name=subcategory_name,
          )

        pack_raw = col('pack_price')
        pack_price = _parse_decimal(pack_raw, '0') if pack_raw else None
        if pack_price is not None and pack_price <= 0:
          pack_price = None

        spec_qty_raw = col('spec_quantity')
        spec_quantity = _parse_int(spec_qty_raw, 0) if spec_qty_raw else None
        if spec_quantity == 0:
          spec_quantity = None

        defaults = {
          'category': category,
          'subcategory': subcategory,
          'brand': col('brand'),
          'variant': col('variant'),
          'spec_quantity': spec_quantity,
          'spec_unit': col('spec_unit'),
          'shelf_location': col('shelf_location'),
          'purchase_price': purchase_price,
          'selling_price': selling_price,
          'pack_price': pack_price,
          'units_per_pack': max(1, _parse_int(col('units_per_pack'), 1)),
          'stock_quantity': max(0, _parse_int(col('stock_quantity'), 0)),
          'alert_threshold': max(0, _parse_int(col('alert_threshold'), 5)),
          'is_active': True,
        }

        existing = Product.objects.filter(shop=shop, name=name).first()
        if existing:
          if update_existing:
            for key, value in defaults.items():
              setattr(existing, key, value)
            existing.save()
            updated += 1
          else:
            skipped += 1
        else:
          Product.objects.create(shop=shop, name=name, **defaults)
          created += 1
      except Exception as exc:  # noqa: BLE001 — collecter les erreurs ligne par ligne
        errors.append(f'Ligne {index}: {exc}')
        if len(errors) >= 50:
          errors.append('… trop d’erreurs, import interrompu.')
          break

  return {
    'created': created,
    'updated': updated,
    'skipped': skipped,
    'errors': errors,
    'total_processed': created + updated + skipped,
  }
