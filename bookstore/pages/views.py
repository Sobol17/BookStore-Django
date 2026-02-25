from django.http import Http404
from django.utils.html import strip_tags
from django.views.generic import DetailView, TemplateView

from .models import Page


CUSTOM_PAGE_CONTEXT = {
    'about': {
        'page_kicker': 'О проекте',
        'page_title': 'О магазине Dombb',
        'page_lead': (
            'Dombb - букинистический проект для тех, кто ценит атмосферу старых изданий, '
            'редкие тиражи и коллекционные находки.'
        ),
        'seo_title': 'О магазине Dombb',
        'seo_description': 'О букинистическом магазине Dombb: редкие книги, винил и коллекционные издания.',
        'about_sections': [
            {
                'title': 'Как появился Dombb',
                'paragraphs': [
                    'Идея магазина появилась из личной любви к букинистике и к вещам с историей. '
                    'Мы начали с небольшой коллекции редких изданий и постепенно собрали вокруг себя '
                    'сообщество читателей и коллекционеров.',
                    'Сегодня Dombb объединяет книги, винил и редкие печатные материалы, которые сложно '
                    'найти в обычной рознице. Для нас важно не просто продать товар, а передать его '
                    'человеку, который действительно ищет именно этот экземпляр.',
                ],
            },
            {
                'title': 'Наш подход к отбору',
                'paragraphs': [
                    'Каждая позиция проходит ручную проверку состояния. Мы фиксируем особенности: '
                    'потертости, следы времени, подписи владельцев, состояние обложки и блоков.',
                    'Если экземпляр не соответствует нашим внутренним стандартам описания, '
                    'он не попадает в витрину. Поэтому карточки каталога максимально честные '
                    'и помогают принять решение до оформления заказа.',
                ],
            },
            {
                'title': 'Для кого мы работаем',
                'paragraphs': [
                    'Среди наших покупателей - частные коллекционеры, библиофилы, дизайнеры интерьеров, '
                    'которые ищут выразительные экземпляры, а также читатели, которые хотят купить '
                    '«ту самую» книгу из детства.',
                    'Мы стараемся поддерживать живой ассортимент: добавляем находки из частных коллекций, '
                    'комиссионных поступлений и профессиональных подборок.',
                ],
            },
            {
                'title': 'Почему нам доверяют',
                'paragraphs': [
                    'Прозрачные описания, стабильная коммуникация и аккуратная упаковка - базовые принципы '
                    'нашей работы. Мы ценим долгие отношения и часто подбираем позиции под индивидуальный запрос.',
                    'Если нужного экземпляра нет в каталоге, можно оставить заявку: мы проверим текущие поступления '
                    'и предложим релевантные варианты.',
                ],
            },
        ],
        'about_closing': (
            'Dombb - это проект про уважение к культурным артефактам и внимание к деталям. '
            'Мы продолжаем развивать каталог и сервис, чтобы покупка букинистики онлайн была '
            'понятной, безопасной и по-настоящему интересной.'
        ),
    },
    'contacts': {
        'page_kicker': 'Контакты',
        'page_title': 'Связаться с Dombb',
        'page_lead': 'Отвечаем на вопросы по заказам, наличию, подбору и выкупу книг.',
        'seo_title': 'Контакты Dombb',
        'seo_description': 'Контакты интернет-магазина Dombb: способы связи, адрес и информация для покупателей.',
        'contacts': [
            {
                'label': 'Телефон',
                'value': '+7 (999) 999-99-99',
                'href': 'tel:+79999999999',
                'note': 'Пн-Сб, 11:00-19:00',
            },
            {
                'label': 'Email',
                'value': 'mail@dombb.ru',
                'href': 'mailto:mail@dombb.ru',
                'note': 'Отвечаем в течение рабочего дня',
            },
            {
                'label': 'Telegram',
                'value': '@dombb',
                'href': 'https://t.me/dombb',
                'note': 'Быстрые ответы в чате',
            },
        ],
        'address': 'Россия, Москва',
        'schedule': 'Пн-Сб, 11:00-19:00',
    },
}


def _content_description(content: str, max_length: int = 170) -> str:
    text = strip_tags(content or '')
    compact = ' '.join(text.split())
    return compact[:max_length].rstrip() if compact else ''


class CustomPageView(TemplateView):
    template_name = 'pages/custom_page.html'
    page_key = ''

    def _get_page_context(self):
        page_context = CUSTOM_PAGE_CONTEXT.get(self.page_key)
        if not page_context:
            raise Http404('Page is not configured.')
        return page_context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page_context = self._get_page_context()
        context.update(page_context)
        context['page_key'] = self.page_key
        context['seo_title'] = page_context.get('seo_title')
        context['seo_description'] = page_context.get('seo_description')
        return context


class AboutPageView(CustomPageView):
    page_key = 'about'
    template_name = 'pages/about_page.html'


class ContactsPageView(CustomPageView):
    page_key = 'contacts'


class PageDetailView(DetailView):
    model = Page
    template_name = 'pages/page_detail.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page = self.get_object()
        context['page'] = page.content
        context['seo_title'] = page.title
        context['seo_description'] = (
            _content_description(page.content)
            or 'Информация о магазине Dombb.'
        )
        return context
