from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from integrations.erp import build_order_payload
from main.models import Category, Product
from orders.models import Order, OrderItem


@override_settings(ERP_DEFAULT_CURRENCY='RUB', ERP_DEFAULT_COUNTRY='Россия')
class OrderErpPayloadTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Категория', slug='kategoriya')
        self.product = Product.objects.create(
            name='Книга',
            slug='kniga',
            price=Decimal('1000'),
            currency='RUB',
            sku='SKU-1',
            erp_product_id='123',
            stock_qty=5,
            in_stock=True,
            category=self.category,
        )
        user_model = get_user_model()
        self.user = user_model(
            phone='+79990001122',
            first_name='Иван',
            last_name='Петров',
        )
        self.user.set_password('secret123')
        self.user.save()
        self.order = Order.objects.create(
            user=self.user,
            first_name='Иван',
            last_name='Петров',
            email='user@example.com',
            phone='+79990001122',
            address1='ул. Пример, 1',
            city='Москва',
            postal_code='101000',
            total_price=Decimal('200.00'),
            status='pending',
        )
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            price=Decimal('100.00'),
        )

    def test_build_order_payload_matches_new_contract(self):
        payload = build_order_payload(self.order)

        self.assertEqual(payload['external_order_id'], str(self.order.pk))
        self.assertEqual(payload['currency'], 'RUB')
        self.assertEqual(
            payload['customer'],
            {
                'name': 'Иван Петров',
                'phone': '+79990001122',
                'email': 'user@example.com',
            },
        )
        self.assertEqual(
            payload['shipping_address'],
            {
                'address': 'ул. Пример, 1, Москва, 101000',
                'city': 'Москва',
                'region': 'Москва',
                'postal_code': '101000',
                'country': 'Россия',
            },
        )
        self.assertEqual(
            payload['items'],
            [
                {'product_id': 123, 'quantity': 2, 'price': '100.00'},
            ],
        )

    def test_build_order_payload_uses_sku_when_product_id_missing(self):
        self.product.erp_product_id = ''
        self.product.save(update_fields=['erp_product_id'])

        payload = build_order_payload(self.order)

        self.assertNotIn('product_id', payload['items'][0])
        self.assertEqual(payload['items'][0]['sku'], 'SKU-1')
