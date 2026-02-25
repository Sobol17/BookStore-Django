from django import forms
from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('image_preview', 'product', 'quantity',
              'price', 'get_total_price')
    readonly_fields = ('image_preview', 'get_total_price')
    can_delete = False

    def image_preview(self, obj):
        image_url = obj.product.primary_image_url if obj.product else ''
        if image_url:
            return mark_safe(
                f'<img src="{image_url}" style="max-height: 100px; max-width: 100px; object-fit: cover;" />'
            )
        return mark_safe('<span style="color: gray;">Нет изображения</span>')

    image_preview.short_description = 'Изображение'

    def get_total_price(self, obj):
        try:
            return obj.get_total_price()
        except TypeError:
            return mark_safe('<span style="color: red;">Invalid Data</span>')

    get_total_price.short_description = 'Сумма'

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        labels = {
            'product': 'Товар',
            'quantity': 'Количество',
            'price': 'Цена',
        }
        if formfield and db_field.name in labels:
            formfield.label = labels[db_field.name]
        return formfield


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    class OrderAdminForm(forms.ModelForm):
        erp_exported_django = forms.BooleanField(
            required=False,
            disabled=True,
            label='Выгружен в ERP (Джанго)',
        )

        class Meta:
            model = Order
            fields = '__all__'

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['erp_exported_django'].initial = bool(
                self.instance and self.instance.erp_acknowledged_at
            )
            labels = {
                'user': 'Пользователь',
                'first_name': 'Имя',
                'last_name': 'Фамилия',
                'email': 'Email',
                'address1': 'Адрес (строка 1)',
                'address2': 'Адрес (строка 2)',
                'city': 'Город',
                'postal_code': 'Почтовый индекс',
                'phone': 'Телефон',
                'special_instructions': 'Комментарий к заказу',
                'total_price': 'Сумма заказа',
                'status': 'Статус',
                'payment_provider': 'Платежный провайдер',
                'youkassa_payment_intent_id': 'ID платежа ЮKassa',
                'created_at': 'Создан',
                'updated_at': 'Обновлен',
            }
            for field_name, label in labels.items():
                if field_name in self.fields:
                    self.fields[field_name].label = label

    form = OrderAdminForm

    list_display = (
        'order_id_display',
        'user_display',
        'email_display',
        'total_price_display',
        'payment_provider_display',
        'status_display',
        'erp_exported_django_status',
        'created_at_display',
        'updated_at_display',
    )
    list_filter = ('status', 'first_name', 'last_name')
    search_fields = ('email', 'first_name', 'last_name')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'total_price', 'youkassa_payment_intent_id')
    inlines = [OrderItemInline]

    fieldsets = (
        ('Информация о заказе', {
            'fields': ('user', 'first_name', 'last_name', 'email',
                       'address1', 'address2', 'city', 'postal_code',
                       'phone', 'special_instructions', 'total_price')
        }),
        ('Оплата и статус', {
            'fields': ('status', 'payment_provider', 'youkassa_payment_intent_id', 'erp_exported_django')
        }),
        ('Временные метки', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description='№', ordering='id')
    def order_id_display(self, obj):
        return obj.id

    @admin.display(description='Пользователь', ordering='user')
    def user_display(self, obj):
        return obj.user

    @admin.display(description='Email', ordering='email')
    def email_display(self, obj):
        return obj.email

    @admin.display(description='Сумма заказа', ordering='total_price')
    def total_price_display(self, obj):
        return obj.total_price

    @admin.display(description='Платежный провайдер', ordering='payment_provider')
    def payment_provider_display(self, obj):
        if not obj.payment_provider:
            return '—'
        return obj.get_payment_provider_display()

    @admin.display(description='Статус', ordering='status')
    def status_display(self, obj):
        return obj.get_status_display()

    @admin.display(boolean=True, description='Выгружен в ERP (Джанго)')
    def erp_exported_django_status(self, obj):
        return bool(obj.erp_acknowledged_at)

    @admin.display(description='Создан', ordering='created_at')
    def created_at_display(self, obj):
        return obj.created_at

    @admin.display(description='Обновлен', ordering='updated_at')
    def updated_at_display(self, obj):
        return obj.updated_at

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('user', 'first_name', 'last_name', 'email',
                                           'address1', 'address2', 'city', 'postal_code', 'phone')
        return self.readonly_fields
