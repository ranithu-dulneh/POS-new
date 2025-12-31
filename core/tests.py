from django.test import TestCase, Client
from django.urls import reverse
from .models import Product, Order, OrderItem
from decimal import Decimal

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
        # Initial POST to add item
        response = self.client.post(reverse('pos_add_item'), {'barcode': '123456'})
        self.assertEqual(response.status_code, 302) # Redirects back to POS

        # Check session cart
        session = self.client.session
        self.assertIn('pos_cart', session)
        self.assertIn(str(self.product.id), session['pos_cart'])
        self.assertEqual(session['pos_cart'][str(self.product.id)]['quantity'], 1)

    def test_pos_checkout(self):
        # Add item to cart session directly
        session = self.client.session
        session['pos_cart'] = {
            str(self.product.id): {
                'name': self.product.name,
                'price': str(self.product.price),
                'quantity': 2
            }
        }
        session.save()

        # Checkout
        response = self.client.post(reverse('pos_checkout'))
        self.assertEqual(response.status_code, 302)

        # Verify Order created
        order = Order.objects.first()
        self.assertIsNotNone(order)
        self.assertEqual(order.order_type, 'POS')
        self.assertEqual(order.total_amount, Decimal('20.00'))

        # Verify Stock deducted
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 8) # 10 - 2

    def test_online_store_list(self):
        response = self.client.get(reverse('product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Product')

    def test_online_checkout(self):
        # Add item to online cart session
        session = self.client.session
        session['online_cart'] = {
            str(self.product.id): {
                'name': self.product.name,
                'price': str(self.product.price),
                'quantity': 1
            }
        }
        session.save()

        # Checkout
        response = self.client.post(reverse('checkout'))
        self.assertEqual(response.status_code, 302)

        # Verify Order
        order = Order.objects.filter(order_type='ONLINE').first()
        self.assertIsNotNone(order)

        # Verify Stock
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 9)

    def test_reporting_view(self):
        # Create some orders
        Order.objects.create(order_type='ONLINE', total_amount=Decimal('100.00'))
        Order.objects.create(order_type='POS', total_amount=Decimal('50.00'))

        response = self.client.get(reverse('report_view'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '100.00')
        self.assertContains(response, '50.00')
