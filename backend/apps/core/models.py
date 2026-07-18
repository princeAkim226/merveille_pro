from django.conf import settings
from django.db import models


class ActionLog(models.Model):
  user = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.SET_NULL,
    null=True,
    related_name='action_logs',
  )
  action = models.CharField(max_length=100)
  details = models.TextField(blank=True)
  created_at = models.DateTimeField(auto_now_add=True)

  class Meta:
    verbose_name = 'Journal d\'actions'
    verbose_name_plural = 'Journaux d\'actions'
    ordering = ['-created_at']

  def __str__(self):
    return f'{self.action} — {self.created_at}'


class CompanySettings(models.Model):
  """Configuration unique de l'entreprise (branding, coordonnées)."""
  company_name = models.CharField(max_length=120, default='Merveille Pro')
  tagline = models.CharField(max_length=200, default='Gestion commerciale multi-secteurs', blank=True)
  address = models.TextField(blank=True)
  phone = models.CharField(max_length=30, blank=True)
  email = models.EmailField(blank=True)
  website = models.CharField(max_length=200, blank=True)
  tax_id = models.CharField(max_length=80, blank=True, verbose_name='N° fiscal / RCCM')
  currency_label = models.CharField(max_length=20, default='F CFA')
  invoice_footer = models.CharField(
    max_length=300,
    default='Merci pour votre confiance !',
    blank=True,
  )
  logo_base64 = models.TextField(blank=True, help_text='Image PNG/JPEG encodée en base64')
  updated_at = models.DateTimeField(auto_now=True)

  class Meta:
    verbose_name = 'Paramètres entreprise'
    verbose_name_plural = 'Paramètres entreprise'

  def __str__(self):
    return self.company_name

  @classmethod
  def get_solo(cls):
    obj, _ = cls.objects.get_or_create(pk=1)
    return obj

  def save(self, *args, **kwargs):
    self.pk = 1
    super().save(*args, **kwargs)

  def delete(self, *args, **kwargs):
    pass
