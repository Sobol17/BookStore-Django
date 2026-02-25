from django.test import TestCase

from integrations.erp import upsert_product_from_erp
from main.models import Product


class ErpVinylMappingTests(TestCase):
    def test_vinyl_details_set_vinyl_category_and_genre(self):
        payload = {
            'id': 96382,
            'offer_id': '162982369',
            'name': 'The Dark Side of the Moon',
            'prices': [
                {
                    'price': 240,
                    'currency_code': 'RUB',
                }
            ],
            'categories': [
                {'id': 1, 'name': 'Книги', 'parent_id': None},
                {'id': 2, 'name': 'Фантастика', 'parent_id': 1},
            ],
            'vinyl_details': {
                'id': 77,
                'article': 'LP-001',
                'title': 'The Dark Side of the Moon',
                'artist': 'Pink Floyd',
                'genre': 'Rock',
                'label': 'Harvest',
                'release_year': '1973',
                'barcode': '5099902987613',
            },
        }

        _, status, _ = upsert_product_from_erp(payload)

        self.assertEqual(status, 'created')
        product = Product.objects.get(erp_product_id='96382')
        self.assertEqual(product.category.name, 'vinyl')
        self.assertIsNotNone(product.genre)
        self.assertEqual(product.genre.name, 'Rock')
        self.assertEqual(product.authors, 'Pink Floyd')
        self.assertEqual(product.publisher, 'Harvest')
        self.assertEqual(product.year, 1973)
        self.assertEqual(product.barcode, '5099902987613')

    def test_empty_vinyl_details_still_set_vinyl_category(self):
        payload = {
            'id': 96383,
            'offer_id': '162982370',
            'name': 'Unknown Vinyl',
            'prices': [
                {
                    'price': 350,
                    'currency_code': 'RUB',
                }
            ],
            'vinyl_details': {},
        }

        _, status, _ = upsert_product_from_erp(payload)

        self.assertEqual(status, 'created')
        product = Product.objects.get(erp_product_id='96383')
        self.assertEqual(product.category.name, 'vinyl')
