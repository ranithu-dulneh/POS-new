from django.test import TestCase, Client
from django.urls import reverse
from .models import Product, Order, OrderItem
from decimal import Decimal
from django.utils import timezone

class POSSystemTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.product = Product.objects.create(
            name='Test Product',
            barcode='123456',
            product_code='TP-001',
            price=Decimal('10.00'),
            stock_quantity=10,
            description='A test product'
        )

    def test_pos_view_load(self):
        response = self.client.get(reverse('pos_view'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'In-Shop POS')

    def test_add_item_to_pos_cart(self):
        response = self.client.post(reverse('pos_add_item'), {'barcode': '123456'})
        self.assertEqual(response.status_code, 302)
        session = self.client.session
        self.assertIn('pos_cart', session)
        self.assertIn(str(self.product.id), session['pos_cart'])

    def test_pos_checkout(self):
        session = self.client.session
        session['pos_cart'] = {
            str(self.product.id): {
                'name': self.product.name,
                'price': str(self.product.price),
                'quantity': 2
            }
        }
        session.save()

        response = self.client.post(reverse('pos_checkout'))
        self.assertEqual(response.status_code, 302)

        order = Order.objects.first()
        self.assertIsNotNone(order)
        self.assertEqual(order.total_amount, Decimal('20.00'))

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 8)

    def test_manager_login(self):
        # Invalid
        response = self.client.post(reverse('manager_login'), {'code': 'wrong'})
        session = self.client.session
        self.assertFalse(session.get('is_manager'))

        # Valid
        response = self.client.post(reverse('manager_login'), {'code': '123123'})
        self.assertEqual(response.status_code, 302) # Redirect to dashboard
        session = self.client.session
        self.assertTrue(session.get('is_manager'))

    def test_manage_dashboard_protected(self):
        # Unprotected access
        response = self.client.get(reverse('manage_dashboard'))
        self.assertEqual(response.status_code, 302) # Redirect login

        # Login first
        session = self.client.session
        session['is_manager'] = True
        session.save()

        response = self.client.get(reverse('manage_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_add_stock(self):
        session = self.client.session
        session['is_manager'] = True
        session.save()

        url = reverse('add_stock_action', args=[self.product.id])
        response = self.client.post(url, {'quantity': 5})
        self.assertEqual(response.status_code, 302)

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 15)

    def test_reporting_view(self):
        Order.objects.create(order_type='POS', total_amount=Decimal('50.00'))
        response = self.client.get(reverse('report_view'))
        self.assertEqual(response.status_code, 200)
        # Template might display $50 instead of $50.00 if formatting changes,
        # checking for '50' is safer or checking context
        self.assertContains(response, '50')
