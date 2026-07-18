from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.products.models import Category, Product
from apps.sales.models import Sale

User = get_user_model()


class SaleAPITestCase(APITestCase):
  def setUp(self):
    self.user = User.objects.create_user(
      username='vendeur', password='vendeur123', role=User.Role.VENDEUR
    )
    cat = Category.objects.create(name='Test')
    self.product = Product.objects.create(
      name='Article',
      category=cat,
      purchase_price=Decimal('10'),
      selling_price=Decimal('15'),
      stock_quantity=10,
    )
    self.client.force_authenticate(user=self.user)

  def test_create_sale_reduces_stock(self):
    url = reverse('sale-list')
    data = {
      'items': [{'product': self.product.pk, 'quantity': 2}],
    }
    response = self.client.post(url, data, format='json')
    self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    self.product.refresh_from_db()
    self.assertEqual(self.product.stock_quantity, 8)
    self.assertEqual(Sale.objects.count(), 1)

  def test_sale_insufficient_stock(self):
    url = reverse('sale-list')
    data = {
      'items': [{'product': self.product.pk, 'quantity': 100}],
    }
    response = self.client.post(url, data, format='json')
    self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
