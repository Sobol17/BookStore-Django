from django.db import models


class ProductConditionChoices(models.TextChoices):
    GIFT = 'gift', 'Подарочное'
    EXCELLENT = 'excellent', 'Отличное'
    GOOD = 'good', 'Хорошее'
    FAIR = 'fair', 'Удовлетворительное'
    

class ProductCollections(models.TextChoices):
    NEW = 'new', 'Новинки'
    SALE = 'sale', 'Акции'
    RECOMMEND = 'recommend', 'Рекомендуем'