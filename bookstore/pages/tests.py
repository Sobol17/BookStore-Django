from django.test import TestCase

from .models import Page


class CustomPagesTests(TestCase):
    def test_about_page_available(self):
        response = self.client.get('/about')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/about_page.html')
        self.assertEqual(response.context['seo_title'], 'О магазине Dombb')

    def test_contacts_page_available(self):
        response = self.client.get('/contacts')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/custom_page.html')
        self.assertEqual(response.context['seo_title'], 'Контакты Dombb')

    def test_dynamic_page_still_works(self):
        page = Page.objects.create(
            title='Тестовая страница',
            slug='test-page',
            is_published=True,
            content='<p>Контент страницы</p>',
        )
        response = self.client.get(f'/{page.slug}/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/page_detail.html')
