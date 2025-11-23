from django.conf import settings
from django.db import models


class FavoriteList(models.Model):
    session_key = models.CharField(max_length=40, unique=True, null=True, blank=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-updated_at',)

    def __str__(self):
        if self.user:
            return f'Favorites of {self.user}'
        return f'Favorites session {self.session_key}'

    @property
    def total_items(self):
        return self.items.count()


class FavoriteItem(models.Model):
    favorite_list = models.ForeignKey(FavoriteList, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('main.Product', on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('favorite_list', 'product')
        ordering = ('-added_at',)

    def __str__(self):
        return f'{self.product} in favorites'
