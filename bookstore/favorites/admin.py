from django.contrib import admin

from .models import FavoriteItem, FavoriteList


class FavoriteItemInline(admin.TabularInline):
    model = FavoriteItem
    extra = 0


@admin.register(FavoriteList)
class FavoriteListAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'session_key', 'total_items', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('session_key', 'user__username', 'user__email')
    readonly_fields = ('total_items',)
    inlines = [FavoriteItemInline]


@admin.register(FavoriteItem)
class FavoriteItemAdmin(admin.ModelAdmin):
    list_display = ('favorite_list', 'product', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('product__name', 'favorite_list__user__username', 'favorite_list__session_key')
