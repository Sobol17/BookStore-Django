from django.contrib import admin
from .models import Page

# Register your models here.
class PageAdmin(admin.ModelAdmin):
	list_display = ('title', 'slug', 'is_published', 'content')
	list_filter = ('is_published', 'title', 'slug')
	prepopulated_fields = {'slug': ('title',)}
	search_fields = ('title',)
 
 
admin.site.register(Page, PageAdmin)