from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.products.models import Category, Product

User = get_user_model()


class ProductAPITestCase(APITestCase):
  def setUp(self):
    self.admin = User.objects.create_user(
      username='admin', password='admin123', role=User.Role.ADMIN
    )
    self.category = Category.objects.create(name='Test')
    self.client.force_authenticate(user=self.admin)

  def test_create_product(self):
    url = reverse('product-list')
    data = {
      'name': 'Produit Test',
      'category': self.category.pk,
      'purchase_price': '10.00',
      'selling_price': '15.00',
      'stock_quantity': 50,
      'alert_threshold': 5,
    }
    response = self.client.post(url, data, format='json')
    self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    self.assertEqual(Product.objects.count(), 1)

  def test_list_products_with_search(self):
    Product.objects.create(
      name='Stylo Bleu',
      category=self.category,
      purchase_price=Decimal('1'),
      selling_price=Decimal('2'),
    )
    url = reverse('product-list')
    response = self.client.get(url, {'search': 'Stylo'})
    self.assertEqual(response.status_code, status.HTTP_200_OK)
    self.assertEqual(response.data['count'], 1)
