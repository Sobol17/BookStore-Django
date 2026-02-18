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
        return mark_safe('<span style="color: gray;">No image</span>')

    image_preview.short_description = 'Image'

    def get_total_price(self, obj):
        try:
            return obj.get_total_price()
        except TypeError:
            return mark_safe('<span style="color: red;">Invalid Data</span>')

    get_total_price.short_description = 'Total Price'


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

    form = OrderAdminForm

    list_display = ('id', 'user', 'email',
                    'total_price', 'payment_provider',
                    'status', 'erp_exported_django_status',
                    'created_at', 'updated_at')
    list_filter = ('status', 'first_name', 'last_name')
    search_fields = ('email', 'first_name', 'last_name')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'total_price', 'youkassa_payment_intent_id')
    inlines = [OrderItemInline]

    fieldsets = (
        ('Order Information', {
            'fields': ('user', 'first_name', 'last_name', 'email',
                       'address1', 'address2', 'city', 'postal_code',
                       'phone', 'special_instructions', 'total_price')
        }),
        ('Payment and Status', {
            'fields': ('status', 'payment_provider', 'youkassa_payment_intent_id', 'erp_exported_django')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(boolean=True, description='Выгружен в ERP (Джанго)')
    def erp_exported_django_status(self, obj):
        return bool(obj.erp_acknowledged_at)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('user', 'first_name', 'last_name', 'email',
                                           'address1', 'address2', 'city', 'postal_code', 'phone')
        return self.readonly_fields
