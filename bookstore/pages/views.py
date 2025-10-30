from django.shortcuts import render
from django.views.generic import TemplateView, DetailView
from .models import Page

# Create your views here.
class PageDetailView(DetailView):
	model = Page
	template_name = 'pages/page_detail.html'
	slug_field = 'slug'
	slug_url_kwarg = 'slug'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		page = self.get_object()
		context['page'] = page.content
		return context