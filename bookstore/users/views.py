from urllib.parse import urlencode

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.template.response import TemplateResponse
from django.core import signing
from django.core.mail import send_mail
from django.conf import settings
from .forms import CustomUserCreationForm, CustomUserLoginForm, EmailLoginRequestForm, \
    CustomUserUpdateForm, STATIC_SMS_CODE
from .models import CustomUser
from django.contrib import messages
from main.models import Product
from favorites.services import merge_session_favorites
from orders.models import Order
from django.views.decorators.http import require_POST
from common.phone import normalize_phone, PhoneValidationError


@require_POST
def request_sms_code(request):
    phone_input = request.POST.get('phone', '')
    flow = request.POST.get('flow', 'login')
    try:
        normalized_phone = normalize_phone(phone_input)
    except PhoneValidationError as exc:
        return JsonResponse({'ok': False, 'message': str(exc)}, status=400)

    if flow == 'register':
        if CustomUser.objects.filter(phone=normalized_phone).exists():
            return JsonResponse(
                {'ok': False, 'message': 'Номер телефона уже зарегистрирован'},
                status=409,
            )
    elif flow == 'login':
        if not CustomUser.objects.filter(phone=normalized_phone).exists():
            return JsonResponse(
                {'ok': False, 'message': 'Пользователь с таким телефоном не найден'},
                status=404,
            )

    return JsonResponse({
        'ok': True,
        'message': f'Код отправлен. Для тестирования используйте {STATIC_SMS_CODE}.',
        'phone': normalized_phone,
        'code_hint': STATIC_SMS_CODE,
    })


@require_POST
def request_email_link(request):
    flow = request.POST.get('flow', 'login')
    redirect_name = 'users:register' if flow == 'register' else 'users:login'
    template_name = 'users/register.html' if flow == 'register' else 'users/login.html'
    email_form = EmailLoginRequestForm(request.POST)

    phone_form = CustomUserLoginForm(request=request)
    register_form = CustomUserCreationForm()

    if email_form.is_valid():
        email = email_form.cleaned_data['email']
        if flow == 'login':
            user = CustomUser.objects.filter(email=email).first()
            if not user:
                messages.error(request, 'Пользователь с таким email не найден')
                return redirect(redirect_name)
            if not user.is_active:
                messages.error(request, 'Аккаунт деактивирован')
                return redirect(redirect_name)
        else:
            if CustomUser.objects.filter(email=email).exists():
                messages.error(request, 'Email уже используется. Попробуйте войти.')
                return redirect('users:login')

        token = signing.dumps({'email': email, 'flow': flow})
        confirm_url = request.build_absolute_uri(
            reverse('users:email_link_confirm') + f'?{urlencode({"token": token})}'
        )
        subject = 'Ссылка для входа в аккаунт'
        if flow == 'register':
            subject = 'Подтверждение email для регистрации'
        message = (
            'Чтобы подтвердить email и продолжить, перейдите по ссылке:\n'
            f'{confirm_url}\n\n'
            'Если вы не запрашивали ссылку, просто игнорируйте это письмо.'
        )
        try:
            send_mail(
                subject,
                message,
                getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@bookstore.local'),
                [email],
                fail_silently=False,
            )
            messages.success(request, 'Мы отправили ссылку на вашу почту. Проверьте email, чтобы продолжить.')
        except Exception:
            messages.error(request, 'Не удалось отправить письмо. Попробуйте позже.')
        return redirect(redirect_name)

    context = {
        'email_form': email_form,
    }
    if flow == 'register':
        context['form'] = register_form
    else:
        context['form'] = phone_form
    return render(request, template_name, context)


def email_link_confirm(request):
    token = request.GET.get('token') or ''
    if not token:
        messages.error(request, 'Ссылка недействительна или устарела')
        return redirect('users:login')

    try:
        data = signing.loads(token, max_age=getattr(settings, 'EMAIL_LINK_MAX_AGE', 1800))
    except signing.SignatureExpired:
        messages.error(request, 'Ссылка устарела, запросите новую')
        return redirect('users:login')
    except signing.BadSignature:
        messages.error(request, 'Ссылка недействительна')
        return redirect('users:login')

    email = data.get('email')
    flow = data.get('flow', 'login')
    if not email:
        messages.error(request, 'Некорректная ссылка')
        return redirect('users:login')

    if flow == 'register':
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Такой email уже использован. Попробуйте войти.')
            return redirect('users:login')
        request.session['verified_email'] = email
        messages.success(request, 'Email подтверждён. Завершите регистрацию.')
        return redirect('users:register')

    user = CustomUser.objects.filter(email=email).first()
    if not user:
        messages.error(request, 'Пользователь с таким email не найден')
        return redirect('users:login')
    if not user.is_active:
        messages.error(request, 'Аккаунт деактивирован')
        return redirect('users:login')

    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    merge_session_favorites(request, user)
    messages.success(request, '✅ Вход по email выполнен')
    return redirect('main:index')


def register(request):
    verified_email = request.session.get('verified_email')
    email_form = EmailLoginRequestForm()
    if request.method == 'POST':
        data = request.POST.copy()
        if verified_email:
            data['email'] = verified_email
        form = CustomUserCreationForm(data)
        if verified_email and 'email' in form.fields:
            form.fields['email'].widget.attrs['readonly'] = 'readonly'
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            merge_session_favorites(request, user)
            request.session.pop('verified_email', None)
            return redirect('main:index')
        elif form.errors.get('sms_code'):
            messages.error(request, 'Код неверный')
    else:
        initial = {}
        if verified_email:
            initial['email'] = verified_email
        form = CustomUserCreationForm(initial=initial)
        if verified_email and 'email' in form.fields:
            form.fields['email'].widget.attrs['readonly'] = 'readonly'
    return render(request, 'users/register.html', {
        'form': form,
        'email_form': email_form,
        'verified_email': verified_email,
    })


def login_view(request):
    email_form = EmailLoginRequestForm()
    if request.method == 'POST':
        form = CustomUserLoginForm(request=request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            merge_session_favorites(request, user)
            messages.success(request, '✅ Вы успешно вошли в аккаунт')
            return redirect('main:index')
        else:
            error_texts = [str(err).lower() for err in form.non_field_errors()]
            if 'password' in form.errors or any('код' in err for err in error_texts):
                messages.error(request, 'Код неверный')
    else:
        form = CustomUserLoginForm()
    return render(request, 'users/login.html', {'form': form, 'email_form': email_form})


@login_required(login_url='/users/login')
def profile_view(request):
    if request.method == 'POST':
        form = CustomUserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            if request.headers.get("HX-Request"):
                return HttpResponse(headers={'HX-Redirect': reverse('users:profile')})
            return redirect('users:profile')
    else:
        form = CustomUserUpdateForm(instance=request.user)

    recommended_products = Product.objects.all().order_by('id')[:3]

    last_order = (
        Order.objects.filter(user=request.user)
        .order_by('-created_at')
        .first()
    )

    return TemplateResponse(request, 'users/profile.html', {
        'form': form,
        'user': request.user,
        'recommended_products': recommended_products,
        'last_order': last_order,
    })


@login_required(login_url='/users/login')
def account_details(request):
    user = CustomUser.objects.get(id=request.user.id)
    return TemplateResponse(request, 'users/partials/account_details.html', {'user': user})


@login_required(login_url='/users/login')
def edit_account_details(request):
    form = CustomUserUpdateForm(instance=request.user)
    return TemplateResponse(request, 'users/partials/edit_account_details.html',
                            {'user': request.user, 'form': form})


@login_required(login_url='/users/login')
def update_account_details(request):
    if request.method == 'POST':
        form = CustomUserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            user.clean()
            user.save()
            updated_user = CustomUser.objects.get(id=user.id)
            request.user = updated_user
            if request.headers.get('HX-Request'):
                return TemplateResponse(request, 'users/partials/account_details.html', {'user': updated_user})
            return TemplateResponse(request, 'users/partials/account_details.html', {'user': updated_user})
        else:
            return TemplateResponse(request, 'users/partials/edit_account_details.html',
                                    {'user': request.user, 'form': form})
    if request.headers.get('HX-Request'):
        return HttpResponse(headers={'HX-Redirect': reverse('user:profile')})
    return redirect('users:profile')


def logout_view(request):
    logout(request)
    if request.headers.get('HX-Request'):
        return HttpResponse(headers={'HX-Redirect': reverse('main:index')})
    return redirect('main:index')
@login_required(login_url='/users/login')
def order_history(request):
    orders = (
        Order.objects.filter(user=request.user)
        .prefetch_related('items__product')
        .order_by('-created_at')
    )
    return TemplateResponse(request, 'users/order_history.html', {
        'orders': orders,
    })


@login_required(login_url='/users/login')
def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related('items__product'),
        id=order_id,
        user=request.user,
    )
    return TemplateResponse(request, 'users/order_detail.html', {
        'order': order,
    })
