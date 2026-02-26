from django.test import TestCase
from django.urls import reverse

from integrations.erp import upsert_product_from_erp
from main.models import Category, Genre, Product


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


class ErpPostcardMappingTests(TestCase):
    def test_postcard_details_set_postcard_category(self):
        payload = {
            'id': 10125,
            'name': 'Набор открыток «СССР, космос»',
            'description': 'Коллекционный набор, 12 шт.',
            'prices': [
                {
                    'price': '990.00',
                    'old_price': '1290.00',
                }
            ],
            'postcard_details': {
                'id': 777,
                'theme': 'История / Космос',
                'collection_type': 'Филокартия',
                'release_year': '1978',
                'publisher': 'Изобразительное искусство',
            },
        }

        _, status, _ = upsert_product_from_erp(payload)

        self.assertEqual(status, 'created')
        product = Product.objects.get(erp_product_id='10125')
        self.assertEqual(product.category.name, 'Открытки, марки, значки')
        self.assertEqual(product.category.slug, 'otkrytki-marki-znachki')
        self.assertIsNotNone(product.genre)
        self.assertEqual(product.genre.name, 'История / Космос')
        self.assertEqual(product.year, 1978)
        self.assertEqual(product.publisher, 'Изобразительное искусство')

    def test_empty_postcard_details_still_set_postcard_category(self):
        payload = {
            'id': 10126,
            'name': 'Набор марок',
            'prices': [
                {
                    'price': '1990.00',
                }
            ],
            'postcard_details': {},
        }

        _, status, _ = upsert_product_from_erp(payload)

        self.assertEqual(status, 'created')
        product = Product.objects.get(erp_product_id='10126')
        self.assertEqual(product.category.name, 'Открытки, марки, значки')


class ErpBookMappingTests(TestCase):
    def test_book_details_set_book_author(self):
        payload = {
            'id': 20101,
            'name': 'Пикник на обочине',
            'prices': [
                {
                    'price': 780,
                    'currency_code': 'RUB',
                }
            ],
            'book_details': {
                'author': 'Аркадий и Борис Стругацкие',
            },
        }

        _, status, _ = upsert_product_from_erp(payload)

        self.assertEqual(status, 'created')
        product = Product.objects.get(erp_product_id='20101')
        self.assertEqual(product.authors, 'Аркадий и Борис Стругацкие')

    def test_book_genre_maps_from_zhanry_tovara_parameter(self):
        payload = {
            'id': 20102,
            'name': 'Туманность Андромеды',
            'prices': [
                {
                    'price': 560,
                    'currency_code': 'RUB',
                }
            ],
            'categories': [
                {'id': 1, 'name': 'Книги', 'parent_id': None},
                {'id': 2, 'name': 'Фантастика', 'parent_id': 1},
            ],
            'additional_parameters': [
                {
                    'name': 'Жанры товара',
                    'values': ['Научная фантастика', 'Классика'],
                    'genre': 'Научная фантастика',
                },
            ],
        }

        _, status, _ = upsert_product_from_erp(payload)

        self.assertEqual(status, 'created')
        product = Product.objects.get(erp_product_id='20102')
        self.assertIsNotNone(product.genre)
        self.assertEqual(product.genre.name, 'Научная фантастика')

    def test_book_genre_ignores_napravlenie(self):
        payload = {
            'id': 20103,
            'name': 'Обитаемый остров',
            'prices': [
                {
                    'price': 420,
                    'currency_code': 'RUB',
                }
            ],
            'additional_parameters': [
                {
                    'name': 'Направление',
                    'value': 'Фантастика',
                },
            ],
            'book_details': {
                'direction': 'Научпоп',
            },
        }

        _, status, _ = upsert_product_from_erp(payload)

        self.assertEqual(status, 'created')
        product = Product.objects.get(erp_product_id='20103')
        self.assertIsNone(product.genre)


class CatalogViewGenreTests(TestCase):
    def test_category_pages_hide_genres_cards_block(self):
        books = Category.objects.create(name='Книги')
        vinyl = Category.objects.create(name='Винил')
        books_genre = Genre.objects.create(category=books, name='Роман', slug='roman')
        vinyl_genre = Genre.objects.create(category=vinyl, name='Jazz', slug='jazz')

        Product.objects.create(
            erp_product_id='cat-101',
            name='Книга 1',
            slug='kniga-1',
            category=books,
            genre=books_genre,
            price=490,
        )
        Product.objects.create(
            erp_product_id='cat-102',
            name='Пластинка 1',
            slug='plastinka-1',
            category=vinyl,
            genre=vinyl_genre,
            price=990,
        )

        response = self.client.get(reverse('main:catalog', kwargs={'category_slug': books.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['show_all_genres_cards'])
        self.assertTrue(response.context['all_genres'])
        self.assertTrue(all(genre.category_id == books.id for genre in response.context['all_genres']))

        content = response.content.decode('utf-8')
        self.assertNotIn('Жанры категории', content)
        self.assertEqual(content.count('Все жанры'), 1)

        response = self.client.get(reverse('main:catalog', kwargs={'category_slug': vinyl.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['show_all_genres_cards'])
        self.assertTrue(response.context['all_genres'])

        content = response.content.decode('utf-8')
        self.assertNotIn('Жанры категории', content)
        self.assertEqual(content.count('Все жанры'), 1)

    def test_category_genre_buttons_collapsed_to_eight(self):
        books = Category.objects.create(name='Книги')
        for index in range(1, 11):
            Genre.objects.create(category=books, name=f'Жанр {index}', slug=f'zhanr-{index}')

        Product.objects.create(
            erp_product_id='cat-201',
            name='Книга 2',
            slug='kniga-2',
            category=books,
            genre=Genre.objects.filter(category=books).first(),
            price=390,
        )

        response = self.client.get(reverse('main:catalog', kwargs={'category_slug': books.slug}))

        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('Показать все', content)
        self.assertEqual(content.count('data-genre-extra="true"'), 2)
