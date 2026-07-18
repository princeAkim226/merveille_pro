import base64
import re

from rest_framework import serializers

from apps.core.models import CompanySettings


class CompanySettingsSerializer(serializers.ModelSerializer):
  has_logo = serializers.SerializerMethodField()

  class Meta:
    model = CompanySettings
    fields = (
      'company_name',
      'tagline',
      'address',
      'phone',
      'email',
      'website',
      'tax_id',
      'currency_label',
      'invoice_footer',
      'logo_base64',
      'has_logo',
      'updated_at',
    )
    read_only_fields = ('updated_at',)

  def get_has_logo(self, obj):
    return bool(obj.logo_base64)

  def validate_logo_base64(self, value):
    if not value:
      return ''
    raw = value
    if raw.startswith('data:'):
      raw = raw.split(',', 1)[-1]
    raw = raw.strip()
    if not re.fullmatch(r'[A-Za-z0-9+/=\s]+', raw):
      raise serializers.ValidationError('Logo invalide (base64 attendu).')
    try:
      data = base64.b64decode(raw, validate=True)
    except Exception as exc:
      raise serializers.ValidationError('Logo invalide.') from exc
    if len(data) > 2 * 1024 * 1024:
      raise serializers.ValidationError('Logo trop volumineux (max 2 Mo).')
    return raw
