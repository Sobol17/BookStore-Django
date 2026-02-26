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
                'directtion': 'Progressive Rock',
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
        self.assertEqual(product.attributes.get('vinyl_directtion'), 'Progressive Rock')

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
    def test_category_pages_show_genres_cards_block(self):
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
        self.assertTrue(response.context['show_all_genres_cards'])
        self.assertTrue(response.context['all_genres'])
        self.assertTrue(all(genre.category_id == books.id for genre in response.context['all_genres']))

        content = response.content.decode('utf-8')
        self.assertIn('Жанры категории', content)
        self.assertNotIn('data-genre-filter', content)

        response = self.client.get(reverse('main:catalog', kwargs={'category_slug': vinyl.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['show_all_genres_cards'])
        self.assertTrue(response.context['all_genres'])

        content = response.content.decode('utf-8')
        self.assertIn('Жанры категории', content)
        self.assertNotIn('data-genre-filter', content)

    def test_category_pages_hide_genre_buttons_block(self):
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
        self.assertNotIn('data-genre-filter', content)
        self.assertNotIn('data-genre-card-extra="true"', content)

    def test_category_genres_cards_collapsed_to_ten(self):
        books = Category.objects.create(name='Книги')
        for index in range(1, 13):
            Genre.objects.create(category=books, name=f'Жанр {index}', slug=f'zhanr-{index}')

        Product.objects.create(
            erp_product_id='cat-301',
            name='Книга 3',
            slug='kniga-3',
            category=books,
            genre=Genre.objects.filter(category=books).first(),
            price=390,
        )

        response = self.client.get(reverse('main:catalog', kwargs={'category_slug': books.slug}))

        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('Показать все', content)
        self.assertEqual(content.count('data-genre-card-extra="true"'), 2)


class CatalogViewVinylDirecttionFilterTests(TestCase):
    def test_vinyl_category_shows_directtion_filter_and_filters_products(self):
        vinyl = Category.objects.create(name='Винил')
        genre = Genre.objects.create(category=vinyl, name='Rock', slug='rock')

        Product.objects.create(
            erp_product_id='vinyl-101',
            name='Miles Davis - Kind of Blue',
            slug='miles-davis-kind-of-blue',
            category=vinyl,
            genre=genre,
            price=1200,
            attributes={'vinyl_directtion': 'Jazz'},
        )
        Product.objects.create(
            erp_product_id='vinyl-102',
            name='Pink Floyd - Wish You Were Here',
            slug='pink-floyd-wish-you-were-here',
            category=vinyl,
            genre=genre,
            price=1400,
            attributes={'vinyl_directtion': 'Rock'},
        )

        response = self.client.get(
            reverse('main:catalog', kwargs={'category_slug': vinyl.slug}),
            {'directtion': 'Jazz'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['show_vinyl_directtion_filter'])
        self.assertEqual(response.context['selected_vinyl_directtions'], ['Jazz'])
        self.assertIn('Jazz', response.context['vinyl_directtions'])
        self.assertIn('Rock', response.context['vinyl_directtions'])
        products = list(response.context['products'].object_list)
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].erp_product_id, 'vinyl-101')
        self.assertIn('Направление', response.content.decode('utf-8'))

    def test_non_vinyl_category_hides_directtion_filter(self):
        books = Category.objects.create(name='Книги')

        Product.objects.create(
            erp_product_id='book-101',
            name='Книга',
            slug='book-101',
            category=books,
            price=500,
            attributes={'vinyl_directtion': 'Jazz'},
        )

        response = self.client.get(reverse('main:catalog', kwargs={'category_slug': books.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['show_vinyl_directtion_filter'])
        self.assertNotIn('Направление', response.content.decode('utf-8'))


class HomeCategoriesOrderTests(TestCase):
    def test_home_categories_sorted_by_order(self):
        category_b = Category.objects.create(name='Категория B', order=20)
        category_a = Category.objects.create(name='Категория A', order=10)
        category_c = Category.objects.create(name='Категория C', order=30)
        Category.objects.create(name='Категория X', order=1)

        Product.objects.create(
            erp_product_id='home-101',
            name='Товар B',
            slug='tovar-b',
            category=category_b,
            price=100,
        )
        Product.objects.create(
            erp_product_id='home-102',
            name='Товар A',
            slug='tovar-a',
            category=category_a,
            price=100,
        )
        Product.objects.create(
            erp_product_id='home-103',
            name='Товар C',
            slug='tovar-c',
            category=category_c,
            price=100,
        )

        response = self.client.get(reverse('main:index'))

        self.assertEqual(response.status_code, 200)
        category_names = [category.name for category in response.context['categories']]
        self.assertEqual(category_names, ['Категория A', 'Категория B', 'Категория C'])


class CatalogAllPageTests(TestCase):
    def test_catalog_all_shows_categories_cards_and_bottom_text(self):
        books = Category.objects.create(name='Книги')
        vinyl = Category.objects.create(name='Винил')

        Product.objects.create(
            erp_product_id='all-101',
            name='Книга для каталога',
            slug='kniga-dlya-kataloga',
            category=books,
            price=100,
        )
        Product.objects.create(
            erp_product_id='all-102',
            name='Пластинка для каталога',
            slug='plastinka-dlya-kataloga',
            category=vinyl,
            price=100,
        )

        response = self.client.get(reverse('main:catalog_all'))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['show_categories_cards'])
        content = response.content.decode('utf-8')
        self.assertIn('Все категории', content)
        self.assertIn('Книги', content)
        self.assertIn('Винил', content)
        self.assertIn(response.context['catalog_categories_bottom_text'], content)
        self.assertNotIn('Фильтры', content)
        self.assertNotIn('data-product-card', content)
