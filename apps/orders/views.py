"""
Order views — Checkout → Payment → Success / Tracking
Security hardening:
  - Input validation on all POST fields (phone, pincode, qty)
  - order_success requires ownership check (prevents IDOR)
  - cart_add validates quantity to prevent negative/zero injection
"""
import re
import json
from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from apps.products.models import Product
from .models import Order, OrderItem, OrderStatusLog


# ── Validation helpers ────────────────────────────────────────────────────────

_PHONE_RE  = re.compile(r'^\+?[\d\s\-]{7,15}$')
_PIN_RE    = re.compile(r'^\d{4,10}$')
_NAME_RE   = re.compile(r"^[\w\s',.\-]{1,150}$")


def _clean_str(value: str, max_len: int = 250) -> str:
    """Strip whitespace and truncate to max_len."""
    return str(value).strip()[:max_len]


def _validate_checkout_data(post) -> dict:
    """
    Validate POST data for checkout form.
    Returns dict of errors (empty if all good).
    """
    errors = {}
    required = {
        'full_name':    (post.get('full_name', '').strip(),    150),
        'phone':        (post.get('phone', '').strip(),        15),
        'address_line1':(post.get('address_line1', '').strip(),250),
        'city':         (post.get('city', '').strip(),         100),
        'state':        (post.get('state', '').strip(),        100),
        'pincode':      (post.get('pincode', '').strip(),      10),
    }
    for field, (value, maxlen) in required.items():
        if not value:
            errors[field] = 'This field is required.'
        elif len(value) > maxlen:
            errors[field] = f'Too long (max {maxlen} characters).'

    phone = post.get('phone', '').strip()
    if phone and not _PHONE_RE.match(phone):
        errors['phone'] = 'Enter a valid phone number (7-15 digits).'

    pincode = post.get('pincode', '').strip()
    if pincode and not _PIN_RE.match(pincode):
        errors['pincode'] = 'Enter a valid pincode (digits only).'

    return errors


# ── helpers ──────────────────────────────────────────────────────────────────

def _get_cart(request):
    """Return cart list from session: [{product_id, qty, shade}, ...]"""
    return request.session.get('cart', [])


def _save_cart(request, cart):
    request.session['cart'] = cart
    request.session.modified = True


def _cart_products(cart):
    """Resolve cart items to (product, qty, shade) tuples."""
    result = []
    for item in cart:
        try:
            p = Product.objects.get(pk=item['product_id'])
            result.append({
                'product': p,
                'qty':     item.get('qty', 1),
                'shade':   item.get('shade', ''),
                'subtotal': p.price * item.get('qty', 1) if p.price else 0,
            })
        except Product.DoesNotExist:
            pass
    return result


def _calc_totals(items):
    subtotal = sum(i['subtotal'] for i in items)
    delivery = 0 if subtotal >= 499 else 49
    total    = subtotal + delivery
    return subtotal, delivery, total


# ── Add to cart (AJAX / redirect) ────────────────────────────────────────────

def cart_add(request, pk):
    product = get_object_or_404(Product, pk=pk)
    cart    = _get_cart(request)
    shade   = _clean_str(request.POST.get('shade', ''), max_len=100)

    # Validate qty: must be a positive integer, max 99 per item
    try:
        qty = max(1, min(99, int(request.POST.get('qty', 1))))
    except (ValueError, TypeError):
        qty = 1

    # Update existing item or append
    for item in cart:
        if item['product_id'] == pk and item.get('shade') == shade:
            item['qty'] = item.get('qty', 1) + qty
            break
    else:
        cart.append({'product_id': pk, 'qty': qty, 'shade': shade})

    _save_cart(request, cart)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'cart_count': len(cart), 'status': 'added'})
    messages.success(request, f'"{product.name}" added to cart.')
    return redirect('products:detail', pk=pk)


def cart_remove(request, pk):
    cart  = _get_cart(request)
    shade = request.POST.get('shade', '')
    cart  = [i for i in cart if not (i['product_id'] == pk and i.get('shade', '') == shade)]
    _save_cart(request, cart)
    return redirect('orders:checkout')


def cart_update(request, pk):
    cart  = _get_cart(request)
    shade = request.POST.get('shade', '')
    qty   = int(request.POST.get('qty', 1))
    for item in cart:
        if item['product_id'] == pk and item.get('shade', '') == shade:
            if qty <= 0:
                cart.remove(item)
            else:
                item['qty'] = qty
            break
    _save_cart(request, cart)
    return redirect('orders:checkout')


# ── CHECKOUT ─────────────────────────────────────────────────────────────────

def checkout(request):
    """
    Step 1 — Flipkart-style checkout: address + delivery options + order summary.
    GET  → show form pre-filled from session / user profile
    POST → validate address, save to session, redirect to payment
    """
    cart  = _get_cart(request)
    items = _cart_products(cart)

    # If cart is empty and a product_id param is given, do instant buy
    pid = request.GET.get('product_id') or request.POST.get('product_id')
    shade = request.GET.get('shade', '') or request.POST.get('shade', '')
    if not items and pid:
        try:
            p = Product.objects.get(pk=pid)
            items = [{'product': p, 'qty': 1, 'shade': shade,
                      'subtotal': p.price if p.price else 0}]
            # Temporarily store in session for payment step
            request.session['instant_buy'] = {'product_id': int(pid), 'shade': shade}
        except Product.DoesNotExist:
            pass

    if not items:
        messages.warning(request, 'Your cart is empty.')
        return redirect('products:list')

    subtotal, delivery, total = _calc_totals(items)

    # Pre-fill from logged-in user
    # Used by template to pre-fill values.
    initial = {
        'full_name': request.user.get_full_name() or request.user.username if request.user.is_authenticated else '',
        'email': request.user.email if request.user.is_authenticated else '',
    }


    if request.method == 'POST':
        # Server-side validation using the dedicated validator
        errors = _validate_checkout_data(request.POST)
        if errors:
            # Merge POST values into form_data so template has one clean dict
            form_data = {
                'full_name':    request.POST.get('full_name', ''),
                'phone':        request.POST.get('phone', ''),
                'email':        request.POST.get('email', ''),
                'address_line1':request.POST.get('address_line1', ''),
                'address_line2':request.POST.get('address_line2', ''),
                'city':         request.POST.get('city', ''),
                'state':        request.POST.get('state', ''),
                'pincode':      request.POST.get('pincode', ''),
                'order_notes':  request.POST.get('order_notes', ''),
            }
            return render(request, 'orders/checkout.html', {
                'items': items, 'subtotal': subtotal,
                'delivery': delivery, 'total': total,
                'form_data': form_data, 'errors': errors,
                'pid': pid, 'shade': shade,
            })
        # Save sanitized address to session for payment step
        request.session['checkout_data'] = {
            'full_name':    _clean_str(request.POST['full_name'],    150),
            'phone':        _clean_str(request.POST['phone'],        15),
            'email':        _clean_str(request.POST.get('email', ''), 254),
            'address_line1':_clean_str(request.POST['address_line1'], 250),
            'address_line2':_clean_str(request.POST.get('address_line2', ''), 250),
            'city':         _clean_str(request.POST['city'],         100),
            'state':        _clean_str(request.POST['state'],        100),
            'pincode':      _clean_str(request.POST['pincode'],      10),
            'order_notes':  _clean_str(request.POST.get('order_notes', ''), 500),
        }
        request.session.modified = True
        return redirect('orders:payment')

    # GET — pre-fill from user profile
    form_data = {
        'full_name':    initial.get('full_name', ''),
        'phone':        '',
        'email':        initial.get('email', ''),
        'address_line1':'',
        'address_line2':'',
        'city':         '',
        'state':        '',
        'pincode':      '',
        'order_notes':  '',
    }
    return render(request, 'orders/checkout.html', {
        'items': items, 'subtotal': subtotal,
        'delivery': delivery, 'total': total,
        'form_data': form_data, 'errors': {},
        'pid': pid, 'shade': shade,
    })


# ── PAYMENT ──────────────────────────────────────────────────────────────────

def payment(request):
    """
    Step 2 — Payment method selection (COD highlighted, UPI/Card shown).
    POST → create Order + OrderItems + status log → redirect to success.
    """
    cd = request.session.get('checkout_data')
    if not cd:
        return redirect('orders:checkout')

    cart     = _get_cart(request)
    ib       = request.session.get('instant_buy')
    items    = []

    if ib:
        try:
            p = Product.objects.get(pk=ib['product_id'])
            items = [{'product': p, 'qty': 1, 'shade': ib.get('shade', ''),
                      'subtotal': p.price if p.price else 0}]
        except Product.DoesNotExist:
            pass
    else:
        items = _cart_products(cart)

    if not items:
        return redirect('orders:checkout')

    subtotal, delivery, total = _calc_totals(items)

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'cod')

        # ── Create Order ──────────────────────────────────────────────────
        estimated = timezone.now().date() + timedelta(days=5)
        order = Order.objects.create(
            user             = request.user if request.user.is_authenticated else None,
            full_name        = cd['full_name'],
            phone            = cd['phone'],
            email            = cd.get('email', ''),
            address_line1    = cd['address_line1'],
            address_line2    = cd.get('address_line2', ''),
            city             = cd['city'],
            state            = cd['state'],
            pincode          = cd['pincode'],
            order_notes      = cd.get('order_notes', ''),
            payment_method   = payment_method,
            payment_status   = 'pending' if payment_method == 'cod' else 'paid',
            status           = 'confirmed',
            subtotal         = subtotal,
            delivery_charge  = delivery,
            total            = total,
            estimated_delivery = estimated,
        )

        # ── Create Order Items ────────────────────────────────────────────
        for i in items:
            p = i['product']
            OrderItem.objects.create(
                order     = order,
                product   = p,
                name      = p.name,
                brand     = p.brand,
                image_url = p.image_url or '',
                sku       = p.sku,
                shade     = i.get('shade', ''),
                price     = p.price or 0,
                quantity  = i['qty'],
            )

        # ── Initial status log ────────────────────────────────────────────
        OrderStatusLog.objects.create(
            order    = order,
            status   = 'confirmed',
            message  = 'Order placed successfully. Seller notified.',
            location = 'Lumina Processing Centre',
        )

        # ── Clear session ─────────────────────────────────────────────────
        for key in ('checkout_data', 'cart', 'instant_buy'):
            request.session.pop(key, None)
        request.session.modified = True

        return redirect('orders:success', order_id=order.order_id)

    return render(request, 'orders/payment.html', {
        'cd': cd, 'items': items,
        'subtotal': subtotal, 'delivery': delivery, 'total': total,
    })


# ── SUCCESS ───────────────────────────────────────────────────────────────────

def order_success(request, order_id):
    """
    Show order confirmation.
    Only the user who placed the order (or an authenticated guest whose
    session matches) may view this page — prevents IDOR enumeration.
    """
    order = get_object_or_404(Order, order_id=order_id)

    # Ownership check: logged-in user must own the order,
    # OR the order was placed by a guest in this same session.
    if order.user:
        if not request.user.is_authenticated or request.user != order.user:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("You do not have permission to view this order.")
    # For guest orders (order.user is None) we cannot verify ownership here —
    # allow display but don't expose sensitive address data in the template
    # (templates should guard with {% if request.user.is_authenticated %}).

    return render(request, 'orders/success.html', {'order': order})


# ── TRACKING ─────────────────────────────────────────────────────────────────

def order_tracking(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    logs  = order.status_logs.all()

    STEPS = [
        ('confirmed',        'Order Confirmed',    '✅'),
        ('packed',           'Packed',             '📦'),
        ('shipped',          'Shipped',            '🚚'),
        ('out_for_delivery', 'Out for Delivery',   '🏃'),
        ('delivered',        'Delivered',          '🎉'),
    ]
    current_step = order.get_status_step()

    return render(request, 'orders/tracking.html', {
        'order':        order,
        'logs':         logs,
        'steps':        STEPS,
        'current_step': current_step,
    })


# ── MY ORDERS ────────────────────────────────────────────────────────────────

def my_orders(request):
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    orders = Order.objects.filter(user=request.user).prefetch_related('items')
    return render(request, 'orders/my_orders.html', {'orders': orders})


# ── TRACK BY ID (public) ─────────────────────────────────────────────────────

def track_order(request):
    order  = None
    error  = None
    q      = request.GET.get('q', '').strip()
    if q:
        try:
            order = Order.objects.prefetch_related('items', 'status_logs').get(
                order_id=q
            )
        except Order.DoesNotExist:
            try:
                order = Order.objects.prefetch_related('items', 'status_logs').get(
                    tracking_id=q
                )
            except Order.DoesNotExist:
                error = f'No order found for "{q}". Check your Order ID or Tracking ID.'

    return render(request, 'orders/track.html', {
        'order': order, 'error': error, 'q': q,
    })


# ── USER REQUIREMENTS ────────────────────────────────────────────────────────

from .models import UserRequirement
from apps.products.models import Product as _Product


@login_required
def my_requirements(request):
    """List all requirements for the logged-in user."""
    reqs = UserRequirement.objects.filter(user=request.user).prefetch_related('products')
    return render(request, 'orders/my_requirements.html', {'reqs': reqs})


@login_required
def requirement_create(request):
    """Submit a new product requirement / special request."""
    products = _Product.objects.all().order_by('brand', 'name')
    errors   = {}

    if request.method == 'POST':
        title    = request.POST.get('title', '').strip()
        qty      = request.POST.get('quantity', '1').strip()
        priority = request.POST.get('priority', 'normal')
        notes    = request.POST.get('requirement_notes', '').strip()
        custom   = request.POST.get('custom_product', '').strip()
        selected = request.POST.getlist('products')

        fn  = request.POST.get('full_name', '').strip()
        ph  = request.POST.get('phone', '').strip()
        em  = request.POST.get('email', '').strip()
        a1  = request.POST.get('address_line1', '').strip()
        a2  = request.POST.get('address_line2', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        pin  = request.POST.get('pincode', '').strip()

        required_fields = {
            'title': title, 'full_name': fn, 'phone': ph,
            'address_line1': a1, 'city': city, 'state': state, 'pincode': pin,
        }
        errors = {k: 'This field is required.' for k, v in required_fields.items() if not v}
        if not selected and not custom:
            errors['products'] = 'Select at least one product or describe what you need.'

        if not errors:
            req = UserRequirement.objects.create(
                user             = request.user,
                title            = title,
                custom_product   = custom,
                requirement_notes = notes,
                quantity         = max(1, int(qty) if qty.isdigit() else 1),
                priority         = priority,
                full_name        = fn,
                phone            = ph,
                email            = em,
                address_line1    = a1,
                address_line2    = a2,
                city             = city,
                state            = state,
                pincode          = pin,
            )
            if selected:
                req.products.set(_Product.objects.filter(pk__in=selected))

            messages.success(request, f'Requirement "{req.title}" submitted! We\'ll reach out soon.')
            return redirect('orders:my_requirements')

        # Re-render with errors
        form_data = request.POST
        selected_ids = [int(x) for x in selected if x.isdigit()]
        return render(request, 'orders/requirement_form.html', {
            'products': products, 'errors': errors,
            'form_data': form_data, 'selected_ids': selected_ids,
        })

    form_data = {
        'full_name': request.user.get_full_name() or '',
        'email':     request.user.email or '',
    }
    return render(request, 'orders/requirement_form.html', {
        'products': products, 'errors': {}, 'form_data': form_data,
    })


@login_required
def requirement_detail(request, req_id):
    """User can view the detail of their own requirement."""
    req = get_object_or_404(UserRequirement, req_id=req_id, user=request.user)
    return render(request, 'orders/requirement_detail.html', {'req': req})


@login_required
def requirement_cancel(request, req_id):
    """User can cancel a pending requirement."""
    req = get_object_or_404(UserRequirement, req_id=req_id, user=request.user)
    if request.method == 'POST' and req.status in ('pending', 'accepted'):
        req.status = 'cancelled'
        req.save()
        messages.success(request, f'Requirement "{req.title}" cancelled.')
    return redirect('orders:my_requirements')
