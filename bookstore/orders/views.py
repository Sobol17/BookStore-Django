import json
import logging
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import View

from cart.views import CartMixin
from integrations.erp import push_order_to_erp
from integrations.youkassa import (
    YoukassaAPIError,
    YoukassaConfigurationError,
    create_sbp_payment,
    fetch_payment,
)
from .forms import OrderForm
from .models import Order, OrderItem

logger = logging.getLogger(__name__)


@method_decorator(login_required(login_url='/users/login'), name='dispatch')
class CheckoutView(CartMixin, View):
    template_name = 'orders/checkout.html'

    def get(self, request):
        cart = self.get_cart(request)
        logger.debug(
            "Checkout GET: session_key=%s cart_id=%s total_items=%s subtotal=%s",
            request.session.session_key,
            cart.id,
            cart.total_items,
            cart.subtotal,
        )
        form = OrderForm(user=request.user)
        context = self._build_context(cart, form)
        return render(request, self.template_name, context)

    def post(self, request):
        cart = self.get_cart(request)
        form = OrderForm(request.POST, user=request.user)
        payment_provider = request.POST.get('payment_provider')
        valid_providers = [choice[0] for choice in Order.PAYMENT_PROVIDER_CHOICES]

        logger.debug(
            "Checkout POST: session_key=%s cart_id=%s total_items=%s payment_provider=%s",
            request.session.session_key,
            cart.id,
            cart.total_items,
            payment_provider,
        )

        if cart.total_items == 0:
            logger.warning("Checkout attempted with empty cart")
            context = self._build_context(
                cart,
                form,
                extra_context={
                    'error_message': 'Добавьте товары в корзину, чтобы оформить заказ.',
                    'selected_payment_provider': payment_provider,
                }
            )
            return render(request, self.template_name, context, status=400)

        if not payment_provider or payment_provider not in valid_providers:
            logger.error("Invalid payment provider: %s", payment_provider)
            context = self._build_context(
                cart,
                form,
                extra_context={
                    'error_message': 'Выберите доступный способ оплаты.',
                    'selected_payment_provider': payment_provider,
                }
            )
            return render(request, self.template_name, context, status=400)

        if form.is_valid():
            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user,
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    email=form.cleaned_data['email'],
                    address1=form.cleaned_data['address1'],
                    address2=form.cleaned_data['address2'],
                    city=form.cleaned_data['city'],
                    postal_code=form.cleaned_data['postal_code'],
                    phone=form.cleaned_data['phone'],
                    special_instructions='',
                    total_price=cart.subtotal,
                    payment_provider=payment_provider,
                )

                for item in cart.items.select_related('product'):
                    logger.debug('Adding item to order: product=%s quantity=%s', item.product.name, item.quantity)
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        price=item.product.price or Decimal('0.00')
                    )

                cart.clear_cart_items()

            # Create YooKassa payment after the DB transaction is committed
            if payment_provider == 'youkassa':
                return_url = request.build_absolute_uri(
                    reverse('users:order_detail', args=[order.id])
                )
                try:
                    payment_id, payment_url = create_sbp_payment(order, return_url)
                    order.youkassa_payment_intent_id = payment_id
                    order.youkassa_payment_url = payment_url
                    order.save(update_fields=['youkassa_payment_intent_id', 'youkassa_payment_url'])
                    logger.info('YooKassa payment created for order %s', order.id)
                except (YoukassaConfigurationError, YoukassaAPIError) as exc:
                    logger.error('Failed to create YooKassa payment for order %s: %s', order.id, exc)
                    messages.warning(
                        request,
                        f'Заказ №{order.id} оформлен, но не удалось создать ссылку для оплаты. '
                        'Обратитесь в поддержку.'
                    )

            messages.success(request, f'Заказ №{order.id} оформлен. Перейдите к оплате.')
            logger.info('Checkout completed successfully for order %s', order.id)
            detail_url = reverse('users:order_detail', args=[order.id])
            return redirect(detail_url)

        logger.warning("Checkout form validation error: %s", form.errors)
        context = self._build_context(
            cart,
            form,
            extra_context={
                'error_message': 'Проверьте корректность заполнения формы.',
                'selected_payment_provider': payment_provider,
            }
        )
        return render(request, self.template_name, context, status=400)

    def _build_context(self, cart, form, extra_context=None):
        cart_items = list(cart.items.select_related('product').order_by('-added_at'))
        extra_context = extra_context or {}
        selected_provider = extra_context.get('selected_payment_provider')
        if not selected_provider and Order.PAYMENT_PROVIDER_CHOICES:
            selected_provider = Order.PAYMENT_PROVIDER_CHOICES[0][0]
        context = {
            'form': form,
            'cart': cart,
            'cart_items': cart_items,
            'total_price': cart.subtotal,
            'cart_is_empty': len(cart_items) == 0,
            'payment_providers': Order.PAYMENT_PROVIDER_CHOICES,
            'selected_payment_provider': selected_provider,
        }
        if extra_context:
            context.update(extra_context)
        return context


@csrf_exempt
@require_POST
def youkassa_webhook(request):
    """Handle YooKassa webhook notifications."""
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        logger.warning('YooKassa webhook: invalid JSON body')
        return HttpResponse(status=400)

    event = body.get('event')
    if event != 'payment.succeeded':
        # Acknowledge other events without action
        return HttpResponse(status=200)

    payment_object = body.get('object') or {}
    payment_id = payment_object.get('id')
    if not payment_id:
        logger.warning('YooKassa webhook: missing payment id in payload')
        return HttpResponse(status=400)

    # Verify payment status by fetching from YooKassa API
    payment = fetch_payment(payment_id)
    if payment is None:
        logger.error('YooKassa webhook: could not verify payment %s', payment_id)
        return HttpResponse(status=200)

    if payment.status != 'succeeded':
        logger.info('YooKassa webhook: payment %s status is %s, skipping', payment_id, payment.status)
        return HttpResponse(status=200)

    metadata = payment.metadata or {}
    order_id = metadata.get('order_id')
    if not order_id:
        logger.warning('YooKassa webhook: payment %s has no order_id in metadata', payment_id)
        return HttpResponse(status=200)

    try:
        order = (
            Order.objects.select_related('user')
            .prefetch_related('items__product')
            .get(pk=order_id)
        )
    except Order.DoesNotExist:
        logger.warning('YooKassa webhook: order %s not found for payment %s', order_id, payment_id)
        return HttpResponse(status=200)

    if order.paid_at:
        logger.info('YooKassa webhook: order %s already marked as paid, skipping', order_id)
        return HttpResponse(status=200)

    order.paid_at = timezone.now()
    order.status = 'processing'
    order.save(update_fields=['paid_at', 'status', 'updated_at'])
    logger.info('Order %s marked as paid via YooKassa payment %s', order_id, payment_id)

    push_order_to_erp(order.id)

    return HttpResponse(status=200)
