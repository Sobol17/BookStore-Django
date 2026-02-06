import json
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from main.models import Category, Product
from orders.models import Order, OrderItem


@override_settings(INTERNET_SHOP_API_KEY='test-key')
class InternetShopApiTests(TestCase):
    def setUp(self):
        self.headers = {'HTTP_AUTHORIZATION': 'Bearer test-key'}
        self.category = Category.objects.create(name='Фантастика', slug='fantastika')
        self.product = Product.objects.create(
            name='Старинная книга',
            slug='starinnaya-kniga',
            price=Decimal('990'),
            currency='RUB',
            sku='SKU-1',
            stock_qty=5,
            category=self.category,
            in_stock=True,
            description='Описание',
        )
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            phone='+70000000000',
            first_name='Тест',
            last_name='Покупатель',
            password='secret123',
        )
        self.order = Order.objects.create(
            user=self.user,
            first_name='Тест',
            last_name='Покупатель',
            phone='+70000000000',
            total_price=Decimal('990.00'),
            status='pending',
        )
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
            price=Decimal('990.00'),
        )


    def test_products_bulk_upsert_creates_product(self):
        url = reverse('api:products-bulk-upsert')
        payload = {
            'products': [
                {
                    'sku': 'SKU-NEW',
                    'name': 'Новая книга',
                    'price': 1200,
                    'category': 'Книги',
                    'description': 'Аннотация',
                    'images': [
                        {'url': 'https://cdn.example.com/book.jpg', 'position': 1}
                    ],
                    'vat': 10,
                }
            ]
        }
        response = self.client.post(url, data=json.dumps(payload), content_type='application/json', **self.headers)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(len(body['results']), 1)
        self.assertEqual(body['results'][0]['status'], 'created')
        created = Product.objects.get(sku='SKU-NEW')
        self.assertEqual(created.name, 'Новая книга')
        self.assertEqual(created.category.name, 'Книги')
        self.assertEqual(created.external_image_url, 'https://cdn.example.com/book.jpg')
        self.assertEqual(created.vat_rate, 10)

    def test_products_bulk_upsert_updates_existing_by_sku(self):
        url = reverse('api:products-bulk-upsert')
        payload = {
            'products': [
                {
                    'sku': 'SKU-1',
                    'name': 'Обновленное название',
                    'price': 1500,
                    'attributes': {'author': 'Автор'},
                }
            ]
        }
        response = self.client.post(url, data=json.dumps(payload), content_type='application/json', **self.headers)
        self.assertEqual(response.status_code, 200)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Обновленное название')
        self.assertEqual(self.product.price, Decimal('1500'))
        self.assertEqual(self.product.attributes.get('author'), 'Автор')

    def test_stocks_bulk_update_changes_stock(self):
        url = reverse('api:stocks-bulk-update')
        payload = {
            'warehouse_code': 'main',
            'items': [
                {'sku': 'SKU-1', 'quantity': 3}
            ]
        }
        response = self.client.post(url, data=json.dumps(payload), content_type='application/json', **self.headers)
        self.assertEqual(response.status_code, 200)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_qty, 3)
        self.assertTrue(self.product.in_stock)

    def test_orders_list_returns_pending_orders(self):
        url = reverse('api:orders-list')
        response = self.client.get(f"{url}?status=new", **self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['orders']), 1)
        order_data = data['orders'][0]
        self.assertEqual(order_data['shop_order_id'], str(self.order.pk))
        self.assertEqual(order_data['items'][0]['sku'], 'SKU-1')

    def test_order_acknowledge_sets_ack_fields(self):
        url = reverse('api:orders-acknowledge', args=[self.order.pk])
        payload = {'status': 'accepted', 'external_id': 'ERP-42'}
        response = self.client.post(url, data=json.dumps(payload), content_type='application/json', **self.headers)
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertIsNotNone(self.order.erp_acknowledged_at)
        self.assertEqual(self.order.erp_external_id, 'ERP-42')
        self.assertEqual(self.order.erp_status, 'accepted')

    def test_order_status_update_changes_status(self):
        url = reverse('api:orders-status-update', args=[self.order.pk])
        payload = {'status': 'processing', 'comment': 'В пути'}
        response = self.client.post(url, data=json.dumps(payload), content_type='application/json', **self.headers)
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'processing')
        self.assertEqual(self.order.erp_status_comment, 'В пути')
        self.assertEqual(self.order.erp_status, 'processing')
