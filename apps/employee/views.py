"""
Employee & Admin portal — full product management + employee detail & login log
"""
import csv
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.db.models import Q
from django.contrib import messages
from apps.products.models import Product, SkinConcern
from .models import EmployeeLoginLog


def _is_staff(user):
    """
    Staff check using Django's built-in flags only.
    Do NOT hardcode usernames — it creates a permanent backdoor.
    Grant access via Django Admin → user → is_staff checkbox.
    """
    return user.is_authenticated and (user.is_staff or user.is_superuser)


# ── Portal dashboard ──────────────────────────────────────────────────────────

@login_required
def portal(request):
    if not _is_staff(request.user):
        return redirect('core:home')
    from apps.orders.models import Order, UserRequirement
    products = Product.objects.all().order_by('product_range', 'brand', 'name')
    context = {
        'total_products':  products.count(),
        'total_korean':    products.filter(product_range='korean').count(),
        'total_makeup':    products.filter(product_range='makeup').count(),
        'recent_products': products[:10],
        # Order stats
        'total_orders':       Order.objects.count(),
        'pending_orders':     Order.objects.filter(status__in=['pending', 'confirmed', 'packed', 'shipped', 'out_for_delivery']).count(),
        'delivered_orders':   Order.objects.filter(status='delivered').count(),
        # Requirement stats
        'total_reqs':         UserRequirement.objects.count(),
        'pending_reqs':       UserRequirement.objects.filter(status__in=['pending', 'accepted', 'processing']).count(),
        'recent_reqs':        UserRequirement.objects.select_related('user').order_by('-created_at')[:5],
        'recent_orders':      Order.objects.prefetch_related('items').order_by('-created_at')[:5],
    }
    return render(request, 'employee/portal.html', context)


# ── Product list ──────────────────────────────────────────────────────────────

@login_required
def product_list(request):
    if not _is_staff(request.user):
        return redirect('core:home')
    q      = request.GET.get('q', '')
    range_ = request.GET.get('range', 'all')
    cat    = request.GET.get('category', 'all')
    products = Product.objects.all().order_by('brand', 'name')
    if q:
        products = products.filter(
            Q(name__icontains=q) | Q(brand__icontains=q) | Q(sku__icontains=q)
        )
    if range_ != 'all':
        products = products.filter(product_range=range_)
    if cat != 'all':
        products = products.filter(category=cat)
    return render(request, 'employee/product_list.html', {
        'products': products,
        'q':        q,
        'range_':   range_,
        'cat':      cat,
        'total':    products.count(),
    })


# ── Product detail ────────────────────────────────────────────────────────────

@login_required
def product_detail(request, pk):
    if not _is_staff(request.user):
        return redirect('core:home')
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'employee/product_detail.html', {'product': product})


# ── Add product ───────────────────────────────────────────────────────────────

@login_required
def product_add(request):
    if not _is_staff(request.user):
        return redirect('core:home')
    if request.method == 'POST':
        d = request.POST
        try:
            p = Product.objects.create(
                name             = d.get('name', '').strip(),
                brand            = d.get('brand', '').strip(),
                category         = d.get('category', 'cleanser'),
                product_range    = d.get('product_range', 'korean'),
                sku              = d.get('sku', '').strip(),
                price            = d.get('price') or None,
                description      = d.get('description', '').strip(),
                key_ingredients  = d.get('key_ingredients', '').strip(),
                full_ingredients = d.get('full_ingredients', '').strip(),
                image_url        = d.get('image_url', '').strip(),
                coverage         = d.get('coverage', '').strip(),
                finish           = d.get('finish', '').strip(),
                undertone_match  = d.get('undertone_match', ''),
                skin_tone_match  = d.get('skin_tone_match', ''),
                is_featured      = 'is_featured' in d,
            )
            messages.success(request, f'Product "{p.name}" added successfully.')
            return redirect('employee:product_detail', pk=p.pk)
        except Exception as e:
            messages.error(request, f'Error adding product: {e}')
    return render(request, 'employee/product_form.html', {
        'action': 'Add', 'product': None,
    })


# ── Edit product ──────────────────────────────────────────────────────────────

@login_required
def product_edit(request, pk):
    if not _is_staff(request.user):
        return redirect('core:home')
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        d = request.POST
        try:
            product.name             = d.get('name',  product.name).strip()
            product.brand            = d.get('brand', product.brand).strip()
            product.category         = d.get('category',      product.category)
            product.product_range    = d.get('product_range', product.product_range)
            product.sku              = d.get('sku',  product.sku).strip()
            product.price            = d.get('price') or None
            product.description      = d.get('description',      '').strip()
            product.key_ingredients  = d.get('key_ingredients',  '').strip()
            product.full_ingredients = d.get('full_ingredients', '').strip()
            product.image_url        = d.get('image_url', '').strip()
            product.coverage         = d.get('coverage', '').strip()
            product.finish           = d.get('finish',   '').strip()
            product.undertone_match  = d.get('undertone_match', '')
            product.skin_tone_match  = d.get('skin_tone_match', '')
            product.is_featured      = 'is_featured' in d
            product.save()
            messages.success(request, f'Product "{product.name}" updated.')
            return redirect('employee:product_detail', pk=product.pk)
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return render(request, 'employee/product_form.html', {
        'action': 'Edit', 'product': product,
    })


# ── Delete product ────────────────────────────────────────────────────────────

@login_required
def product_delete(request, pk):
    if not _is_staff(request.user):
        return redirect('core:home')
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f'"{name}" deleted.')
        return redirect('products:list')
    return render(request, 'employee/product_confirm_delete.html', {'product': product})


# ── Clear products (bulk delete) ──────────────────────────────────────────────

@login_required
def clear_products(request):
    """Bulk-delete products by range (staff only, POST required)."""
    if not _is_staff(request.user):
        return redirect('core:home')
    if request.method == 'POST':
        range_ = request.POST.get('range', 'all')
        if range_ == 'makeup':
            deleted, _ = Product.objects.filter(product_range='makeup').delete()
            messages.success(request, f'Deleted {deleted} makeup product(s).')
        elif range_ == 'korean':
            deleted, _ = Product.objects.filter(product_range='korean').delete()
            messages.success(request, f'Deleted {deleted} K-Beauty product(s).')
        else:
            deleted, _ = Product.objects.all().delete()
            messages.success(request, f'Deleted all {deleted} product(s).')
    return redirect('products:list')


# ── Export CSV ────────────────────────────────────────────────────────────────

@login_required
def export_products(request):
    if not _is_staff(request.user):
        return HttpResponse('Unauthorized', status=403)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="lumina_products.csv"'
    w = csv.writer(response)
    w.writerow([
        'SKU', 'Name', 'Brand', 'Category', 'Range',
        'Price', 'Key Ingredients', 'Description', 'Image URL', 'Featured',
    ])
    for p in Product.objects.all().order_by('brand', 'name'):
        w.writerow([
            p.sku, p.name, p.brand, p.category, p.product_range,
            p.price or '', p.key_ingredients,
            (p.description or '')[:200], p.image_url, p.is_featured,
        ])
    return response


# ── Bulk CSV import ───────────────────────────────────────────────────────────

@login_required
def bulk_import(request):
    """
    Bulk product import via CSV upload OR manual paste (JSON lines).
    Columns: name,brand,category,product_range,sku,price,description,
             key_ingredients,image_url,coverage,finish,undertone_match,
             skin_tone_match,is_featured
    """
    if not _is_staff(request.user):
        return redirect('core:home')

    results = []
    if request.method == 'POST':
        mode = request.POST.get('mode', 'csv')

        if mode == 'csv' and request.FILES.get('csv_file'):
            import csv as csv_mod
            import io
            from django.conf import settings as _settings
            f = request.FILES['csv_file']

            # ── File size guard ──────────────────────────────────────────────
            max_bytes = getattr(_settings, 'MAX_CSV_UPLOAD_BYTES', 1 * 1024 * 1024)
            if f.size > max_bytes:
                messages.error(request, f'CSV file too large (max {max_bytes // 1024} KB).')
                return redirect('employee:bulk_import')

            # ── Content type guard ───────────────────────────────────────────
            allowed_csv_types = ['text/csv', 'text/plain', 'application/csv',
                                  'application/vnd.ms-excel']
            if f.content_type and f.content_type not in allowed_csv_types:
                messages.error(request, 'Invalid file type. Please upload a CSV file.')
                return redirect('employee:bulk_import')

            try:
                decoded = f.read().decode('utf-8-sig')
            except UnicodeDecodeError:
                messages.error(request, 'File encoding error. Please save as UTF-8 CSV.')
                return redirect('employee:bulk_import')

            reader = csv_mod.DictReader(io.StringIO(decoded))
            created = updated = errors = 0
            for row in reader:
                try:
                    sku = row.get('sku', '').strip()
                    if not sku:
                        errors += 1
                        results.append({'status': 'error', 'row': row, 'msg': 'Missing SKU'})
                        continue
                    obj, was_created = Product.objects.update_or_create(
                        sku=sku,
                        defaults={
                            'name':             row.get('name', '').strip(),
                            'brand':            row.get('brand', '').strip(),
                            'category':         row.get('category', 'cleanser').strip(),
                            'product_range':    row.get('product_range', 'korean').strip(),
                            'price':            row.get('price') or None,
                            'description':      row.get('description', '').strip(),
                            'key_ingredients':  row.get('key_ingredients', '').strip(),
                            'full_ingredients': row.get('full_ingredients', '').strip(),
                            'image_url':        row.get('image_url', '').strip(),
                            'coverage':         row.get('coverage', '').strip(),
                            'finish':           row.get('finish', '').strip(),
                            'undertone_match':  row.get('undertone_match', '').strip(),
                            'skin_tone_match':  row.get('skin_tone_match', '').strip(),
                            'is_featured':      row.get('is_featured', '').lower() in ('1', 'true', 'yes'),
                        }
                    )
                    if was_created:
                        created += 1
                        results.append({'status': 'created', 'name': obj.name, 'sku': sku})
                    else:
                        updated += 1
                        results.append({'status': 'updated', 'name': obj.name, 'sku': sku})
                except Exception as e:
                    errors += 1
                    results.append({'status': 'error', 'row': dict(row), 'msg': str(e)})

            messages.success(request, f'Import done — {created} created, {updated} updated, {errors} errors.')

        elif mode == 'manual':
            # Single manual product from the form fields
            try:
                d = request.POST
                sku = d.get('sku', '').strip()
                if not sku:
                    messages.error(request, 'SKU is required.')
                else:
                    obj, was_created = Product.objects.update_or_create(
                        sku=sku,
                        defaults={
                            'name':             d.get('name', '').strip(),
                            'brand':            d.get('brand', '').strip(),
                            'category':         d.get('category', 'cleanser'),
                            'product_range':    d.get('product_range', 'korean'),
                            'price':            d.get('price') or None,
                            'description':      d.get('description', '').strip(),
                            'key_ingredients':  d.get('key_ingredients', '').strip(),
                            'full_ingredients': d.get('full_ingredients', '').strip(),
                            'image_url':        d.get('image_url', '').strip(),
                            'coverage':         d.get('coverage', '').strip(),
                            'finish':           d.get('finish', '').strip(),
                            'undertone_match':  d.get('undertone_match', ''),
                            'skin_tone_match':  d.get('skin_tone_match', ''),
                            'is_featured':      'is_featured' in d,
                        }
                    )
                    label = 'Added' if was_created else 'Updated'
                    messages.success(request, f'{label} "{obj.name}" (SKU: {sku}).')
                    results.append({'status': 'created' if was_created else 'updated', 'name': obj.name, 'sku': sku})
            except Exception as e:
                messages.error(request, f'Error: {e}')

    return render(request, 'employee/bulk_import.html', {
        'results': results,
        'category_choices': Product.CATEGORY_CHOICES,
        'range_choices':    Product.RANGE_CHOICES,
    })


# ── Employee list ─────────────────────────────────────────────────────────────

@login_required
def employee_list(request):
    """List all staff/employee accounts."""
    if not _is_staff(request.user):
        return redirect('core:home')
    employees = User.objects.filter(
        Q(is_staff=True) | Q(is_superuser=True) | Q(username='suhani')
    ).order_by('username')
    return render(request, 'employee/employee_list.html', {'employees': employees})


# ── Employee detail ───────────────────────────────────────────────────────────

@login_required
def employee_detail(request, pk):
    """Show details and login/logout history for a specific employee."""
    if not _is_staff(request.user):
        return redirect('core:home')
    employee = get_object_or_404(User, pk=pk)
    logs     = EmployeeLoginLog.objects.filter(user=employee).order_by('-timestamp')[:50]
    # Stats
    total_logins  = EmployeeLoginLog.objects.filter(user=employee, event='login').count()
    total_logouts = EmployeeLoginLog.objects.filter(user=employee, event='logout').count()
    last_login_log = EmployeeLoginLog.objects.filter(user=employee, event='login').first()
    return render(request, 'employee/employee_detail.html', {
        'employee':      employee,
        'logs':          logs,
        'total_logins':  total_logins,
        'total_logouts': total_logouts,
        'last_login_log': last_login_log,
    })


# ── Order & Requirement Management ────────────────────────────────────────────

from apps.orders.models import Order, OrderStatusLog, UserRequirement


@login_required
def order_list(request):
    """Employee view of all customer orders."""
    if not _is_staff(request.user):
        return redirect('core:home')
    q      = request.GET.get('q', '')
    status = request.GET.get('status', 'all')
    orders = Order.objects.prefetch_related('items').order_by('-created_at')
    if q:
        orders = orders.filter(
            Q(order_id__icontains=q) | Q(full_name__icontains=q) | Q(phone__icontains=q)
        )
    if status != 'all':
        orders = orders.filter(status=status)
    return render(request, 'employee/order_list.html', {
        'orders': orders, 'q': q, 'status_filter': status,
        'status_choices': Order.STATUS_CHOICES,
    })


@login_required
def order_detail_emp(request, order_id):
    """Employee view of a single order with ability to update status."""
    if not _is_staff(request.user):
        return redirect('core:home')
    order = get_object_or_404(Order, order_id=order_id)
    logs  = order.status_logs.all()

    if request.method == 'POST':
        new_status = request.POST.get('status', '').strip()
        note       = request.POST.get('note', '').strip()
        location   = request.POST.get('location', '').strip()
        if new_status and new_status != order.status:
            order.status = new_status
            order.save(update_fields=['status', 'updated_at'])
            OrderStatusLog.objects.create(
                order    = order,
                status   = new_status,
                message  = note or f'Status updated to {order.get_status_display()}',
                location = location,
            )
            # Award loyalty points for delivered orders
            if new_status == 'delivered' and order.user:
                try:
                    from django.conf import settings as dj_settings
                    from django.db.models import F
                    profile = order.user.profile
                    points = int(order.total // 100) * dj_settings.PURCHASE_POINTS_RATE
                    if points > 0:
                        from apps.memberships.models import UserProfile
                        UserProfile.objects.filter(pk=profile.pk).update(
                            loyalty_points=F('loyalty_points') + points
                        )
                except Exception:
                    pass  # never block order update
            messages.success(request, f'Order {order.order_id} status → {order.get_status_display()}')
        return redirect('employee:order_detail', order_id=order_id)

    return render(request, 'employee/order_detail.html', {
        'order': order, 'logs': logs,
        'status_choices': Order.STATUS_CHOICES,
    })


@login_required
def requirement_list(request):
    """Employee view of all user requirements."""
    if not _is_staff(request.user):
        return redirect('core:home')
    q      = request.GET.get('q', '')
    status = request.GET.get('status', 'all')
    reqs   = UserRequirement.objects.prefetch_related('products').select_related('user', 'assigned_to')

    if q:
        reqs = reqs.filter(
            Q(req_id__icontains=q) | Q(user__username__icontains=q) |
            Q(title__icontains=q) | Q(full_name__icontains=q) | Q(phone__icontains=q)
        )
    if status != 'all':
        reqs = reqs.filter(status=status)

    return render(request, 'employee/requirement_list.html', {
        'reqs': reqs, 'q': q, 'status_filter': status,
        'status_choices': UserRequirement.STATUS_CHOICES,
    })


@login_required
def requirement_detail_emp(request, req_id):
    """Employee view of a single requirement with ability to update status & notes."""
    if not _is_staff(request.user):
        return redirect('core:home')
    req = get_object_or_404(UserRequirement, req_id=req_id)

    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'update_status':
            new_status = request.POST.get('status', '').strip()
            emp_notes  = request.POST.get('employee_notes', '').strip()
            assign_id  = request.POST.get('assigned_to', '').strip()
            if new_status:
                req.status = new_status
            if emp_notes:
                req.employee_notes = emp_notes
            if assign_id:
                try:
                    req.assigned_to = User.objects.get(pk=int(assign_id))
                except (User.DoesNotExist, ValueError):
                    pass
            req.save()
            messages.success(request, f'Requirement {req.req_id} updated.')
        return redirect('employee:requirement_detail', req_id=req_id)

    staff_users = User.objects.filter(Q(is_staff=True) | Q(is_superuser=True))
    return render(request, 'employee/requirement_detail.html', {
        'req': req,
        'status_choices':   UserRequirement.STATUS_CHOICES,
        'priority_choices': UserRequirement.PRIORITY_CHOICES,
        'staff_users':      staff_users,
    })

from apps.memberships.views import memberships_admin  # noqa — re-exported for employee URL
