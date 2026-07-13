"""
Lumina Admin Panel — Complete ERP/CRM/HRMS views.
Admin: suhani_1 / suhanimodi7090@gmail.com
"""
from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
import csv

from apps.orders.models import Order, OrderItem
from apps.products.models import Product
from apps.memberships.models import UserProfile
from apps.employee.models import (
    EmployeeAttendance, Lead, Opportunity, CallLog,
    SupportTicket, Campaign, SalesTarget, EmployeeLoginLog,
    InternalNote, CallbackRequest
)
from apps.scanner.models import ScanResult
from apps.diagnostic.models import DiagnosticSession

from .models import (
    EmployeeProfile, Department, SalaryRecord,
    EmployeeLeave, EmployeeDocument, AdminActivity, AdminTask,
    CompanySettings
)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _is_admin(user):
    return user.is_authenticated and user.is_superuser


def _admin_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(request, *args, **kwargs):
        if not _is_admin(request.user):
            messages.error(request, 'Admin access required.')
            return redirect('core:home')
        return fn(request, *args, **kwargs)
    return login_required(wrapper)


def _log(request, action, module, desc):
    try:
        ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() \
             or request.META.get('REMOTE_ADDR', '')
        AdminActivity.objects.create(
            admin=request.user, action=action,
            module=module, description=desc, ip_address=ip or None
        )
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# 1. ADMIN DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────

@_admin_required
def dashboard(request):
    today = date.today()
    month_start = today.replace(day=1)
    year_start  = today.replace(month=1, day=1)

    # Revenue KPIs
    today_revenue = Order.objects.filter(
        created_at__date=today, status='delivered'
    ).aggregate(t=Sum('total'))['t'] or 0

    month_revenue = Order.objects.filter(
        created_at__date__gte=month_start, status='delivered'
    ).aggregate(t=Sum('total'))['t'] or 0

    year_revenue = Order.objects.filter(
        created_at__date__gte=year_start, status='delivered'
    ).aggregate(t=Sum('total'))['t'] or 0

    # Orders
    today_orders   = Order.objects.filter(created_at__date=today).count()
    pending_orders = Order.objects.filter(status__in=['pending','confirmed','packed']).count()

    # Users
    today_registrations = User.objects.filter(
        date_joined__date=today, is_staff=False, is_superuser=False
    ).count()
    total_users = User.objects.filter(is_staff=False, is_superuser=False).count()

    # CRM
    today_leads   = Lead.objects.filter(created_at__date=today).count()
    total_leads   = Lead.objects.count()
    today_opps    = Opportunity.objects.filter(created_at__date=today).count()

    # Support
    open_tickets    = SupportTicket.objects.filter(status__in=['open','in_progress']).count()
    pending_refunds = Order.objects.filter(status='returned').count()

    # Employees
    active_employees = User.objects.filter(is_staff=True, is_active=True).count()
    today_attendance = EmployeeAttendance.objects.filter(date=today, status='present').count()

    # AI
    ai_scans_today = ScanResult.objects.filter(created_at__date=today).count()
    ai_scans_month = ScanResult.objects.filter(created_at__date__gte=month_start).count()

    # Calls
    today_calls = CallLog.objects.filter(called_at__date=today).count()

    # Products
    low_stock = Product.objects.count()  # placeholder (no stock field yet)

    # Monthly revenue chart (last 6 months)
    chart_months, chart_revenue = [], []
    for i in range(5, -1, -1):
        d = today.replace(day=1) - timedelta(days=i * 28)
        m_start = d.replace(day=1)
        try:
            if d.month == 12:
                m_end = d.replace(year=d.year+1, month=1, day=1)
            else:
                m_end = d.replace(month=d.month+1, day=1)
        except ValueError:
            m_end = d.replace(day=28)
        rev = Order.objects.filter(
            created_at__date__gte=m_start,
            created_at__date__lt=m_end,
            status='delivered'
        ).aggregate(t=Sum('total'))['t'] or 0
        chart_months.append(m_start.strftime('%b'))
        chart_revenue.append(float(rev))

    # Top products
    top_products = OrderItem.objects.values('name').annotate(
        cnt=Count('id')
    ).order_by('-cnt')[:5]

    # Recent orders
    recent_orders = Order.objects.order_by('-created_at')[:8]

    # Lead funnel
    lead_funnel = list(Lead.objects.values('stage').annotate(c=Count('id')).order_by('-c')[:6])

    # Recent activity
    recent_activity = AdminActivity.objects.select_related('admin').order_by('-created_at')[:10]

    ctx = {
        'today': today,
        'today_revenue': today_revenue,
        'month_revenue': month_revenue,
        'year_revenue': year_revenue,
        'today_orders': today_orders,
        'pending_orders': pending_orders,
        'today_leads': today_leads,
        'total_leads': total_leads,
        'today_opps': today_opps,
        'today_registrations': today_registrations,
        'total_users': total_users,
        'open_tickets': open_tickets,
        'pending_refunds': pending_refunds,
        'active_employees': active_employees,
        'today_attendance': today_attendance,
        'ai_scans_today': ai_scans_today,
        'ai_scans_month': ai_scans_month,
        'today_calls': today_calls,
        'low_stock': low_stock,
        'chart_months': chart_months,
        'chart_revenue': chart_revenue,
        'top_products': top_products,
        'recent_orders': recent_orders,
        'lead_funnel': lead_funnel,
        'recent_activity': recent_activity,
    }
    return render(request, 'admin_panel/dashboard.html', ctx)


# ─────────────────────────────────────────────────────────────────────────────
# 2. USER MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

@_admin_required
def user_list(request):
    q       = request.GET.get('q', '')
    tier    = request.GET.get('tier', '')
    status  = request.GET.get('status', '')
    users   = User.objects.filter(
        is_staff=False, is_superuser=False
    ).select_related('profile').order_by('-date_joined')

    if q:
        users = users.filter(
            Q(username__icontains=q) | Q(email__icontains=q) |
            Q(first_name__icontains=q) | Q(last_name__icontains=q)
        )
    if tier:
        users = users.filter(profile__tier=tier)
    if status == 'active':
        users = users.filter(is_active=True)
    elif status == 'inactive':
        users = users.filter(is_active=False)

    total   = users.count()
    premium = users.filter(profile__tier__in=['medium','vip']).count()
    blocked = users.filter(is_active=False).count()

    return render(request, 'admin_panel/users/list.html', {
        'users': users[:100], 'q': q, 'tier': tier, 'status_filter': status,
        'total': total, 'premium': premium, 'blocked': blocked,
        'tier_choices': UserProfile.TIER_CHOICES,
    })


@_admin_required
def user_detail(request, pk):
    user = get_object_or_404(User, pk=pk)
    try:
        profile = user.profile
    except Exception:
        profile = None
    orders    = Order.objects.filter(user=user).order_by('-created_at')[:10]
    scans     = ScanResult.objects.filter(user=user).order_by('-created_at')[:5]
    tickets   = SupportTicket.objects.filter(customer=user).order_by('-created_at')[:5]
    leads     = Lead.objects.filter(linked_user=user).order_by('-created_at')[:5]
    revenue   = orders.filter(status='delivered').aggregate(t=Sum('total'))['t'] or 0

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'toggle_active':
            user.is_active = not user.is_active
            user.save()
            _log(request, 'update', 'users', f'Toggled active={user.is_active} for {user.username}')
            messages.success(request, f'User {"activated" if user.is_active else "blocked"}.')
        elif action == 'set_tier' and profile:
            new_tier = request.POST.get('tier', profile.tier)
            profile.tier = new_tier
            profile.save()
            _log(request, 'update', 'users', f'Set tier={new_tier} for {user.username}')
            messages.success(request, f'Tier updated to {new_tier}.')
        return redirect('admin_panel:user_detail', pk=pk)

    return render(request, 'admin_panel/users/detail.html', {
        'target_user': user, 'profile': profile,
        'orders': orders, 'scans': scans, 'tickets': tickets,
        'leads': leads, 'revenue': revenue,
        'tier_choices': UserProfile.TIER_CHOICES,
    })


# ─────────────────────────────────────────────────────────────────────────────
# 3. EMPLOYEE MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

@_admin_required
def emp_list(request):
    q    = request.GET.get('q', '')
    dept = request.GET.get('dept', '')
    emps = User.objects.filter(
        Q(is_staff=True) | Q(is_superuser=True)
    ).select_related('emp_profile').order_by('first_name', 'username')
    if q:
        emps = emps.filter(
            Q(username__icontains=q) | Q(email__icontains=q) |
            Q(first_name__icontains=q) | Q(last_name__icontains=q)
        )
    if dept:
        emps = emps.filter(emp_profile__department__id=dept)
    departments = Department.objects.all()
    return render(request, 'admin_panel/employees/list.html', {
        'employees': emps, 'q': q, 'dept_filter': dept,
        'departments': departments,
        'total': emps.count(),
    })


@_admin_required
def emp_detail(request, pk):
    emp = get_object_or_404(User, pk=pk)
    try:
        profile = emp.emp_profile
    except Exception:
        profile = None
    attendance = EmployeeAttendance.objects.filter(employee=emp).order_by('-date')[:30]
    salary_records = SalaryRecord.objects.filter(employee=emp).order_by('-year','-month')[:12]
    leave_requests = EmployeeLeave.objects.filter(employee=emp).order_by('-created_at')[:10]
    documents      = EmployeeDocument.objects.filter(employee=emp).order_by('-uploaded_at')
    login_logs     = EmployeeLoginLog.objects.filter(user=emp).order_by('-timestamp')[:20]
    leads = Lead.objects.filter(assigned_to=emp).order_by('-created_at')[:5]
    calls = CallLog.objects.filter(employee=emp).order_by('-called_at')[:5]
    tickets = SupportTicket.objects.filter(assigned_to=emp).order_by('-created_at')[:5]

    # Performance summary
    today = date.today()
    month_start = today.replace(day=1)
    perf = {
        'total_calls':    CallLog.objects.filter(employee=emp, called_at__date__gte=month_start).count(),
        'connected_calls':CallLog.objects.filter(employee=emp, called_at__date__gte=month_start, status='connected').count(),
        'leads_created':  Lead.objects.filter(assigned_to=emp, created_at__date__gte=month_start).count(),
        'tickets_solved': SupportTicket.objects.filter(assigned_to=emp, status='resolved', updated_at__date__gte=month_start).count(),
        'sales_closed':   Lead.objects.filter(assigned_to=emp, stage='order_confirmed', updated_at__date__gte=month_start).count(),
    }

    return render(request, 'admin_panel/employees/detail.html', {
        'emp': emp, 'profile': profile,
        'attendance': attendance, 'salary_records': salary_records,
        'leave_requests': leave_requests, 'documents': documents,
        'login_logs': login_logs, 'leads': leads,
        'calls': calls, 'tickets': tickets, 'perf': perf,
    })


@_admin_required
def emp_add(request):
    if request.method == 'POST':
        d = request.POST
        try:
            username  = d.get('username', '').strip()
            email     = d.get('email', '').strip()
            password  = d.get('password', '').strip()
            if not username or not email or not password:
                messages.error(request, 'Username, email and password are required.')
                raise ValueError('missing fields')
            user = User.objects.create_user(
                username=username, email=email, password=password,
                first_name=d.get('first_name','').strip(),
                last_name=d.get('last_name','').strip(),
                is_staff=True,
            )
            dept_id = d.get('department', '')
            dept = Department.objects.filter(pk=dept_id).first() if dept_id else None
            EmployeeProfile.objects.create(
                user=user,
                designation=d.get('designation','').strip(),
                department=dept,
                phone=d.get('phone','').strip(),
                shift=d.get('shift','morning'),
            )
            _log(request, 'create', 'employees', f'Created employee {user.username}')
            messages.success(request, f'Employee {user.username} created.')
            return redirect('admin_panel:emp_detail', pk=user.pk)
        except ValueError:
            pass
    departments = Department.objects.all()
    return render(request, 'admin_panel/employees/form.html', {
        'action': 'Add', 'departments': departments,
        'shift_choices': EmployeeProfile.SHIFT_CHOICES,
        'status_choices': EmployeeProfile.STATUS_CHOICES,
        'gender_choices': EmployeeProfile.GENDER_CHOICES,
        'blood_choices':  EmployeeProfile.BLOOD_GROUP_CHOICES,
    })


@_admin_required
def emp_edit(request, pk):
    emp = get_object_or_404(User, pk=pk)
    try:
        profile = emp.emp_profile
    except Exception:
        profile = EmployeeProfile.objects.create(user=emp)
    if request.method == 'POST':
        d = request.POST
        emp.first_name = d.get('first_name', emp.first_name).strip()
        emp.last_name  = d.get('last_name', emp.last_name).strip()
        emp.email      = d.get('email', emp.email).strip()
        emp.save()
        dept_id = d.get('department', '')
        profile.designation = d.get('designation', profile.designation).strip()
        profile.phone       = d.get('phone', profile.phone).strip()
        profile.shift       = d.get('shift', profile.shift)
        profile.status      = d.get('status', profile.status)
        if dept_id:
            profile.department = Department.objects.filter(pk=dept_id).first()
        profile.dob        = d.get('dob') or None
        profile.gender     = d.get('gender', profile.gender)
        profile.blood_group = d.get('blood_group', profile.blood_group)
        profile.address    = d.get('address', '').strip()
        profile.city       = d.get('city', '').strip()
        profile.state      = d.get('state', '').strip()
        profile.pincode    = d.get('pincode', '').strip()
        profile.skills     = d.get('skills', '').strip()
        profile.save()
        _log(request, 'update', 'employees', f'Updated employee {emp.username}')
        messages.success(request, f'{emp.username} updated.')
        return redirect('admin_panel:emp_detail', pk=pk)
    departments = Department.objects.all()
    return render(request, 'admin_panel/employees/form.html', {
        'action': 'Edit', 'emp': emp, 'profile': profile,
        'departments': departments,
        'shift_choices': EmployeeProfile.SHIFT_CHOICES,
        'status_choices': EmployeeProfile.STATUS_CHOICES,
        'gender_choices': EmployeeProfile.GENDER_CHOICES,
        'blood_choices':  EmployeeProfile.BLOOD_GROUP_CHOICES,
    })


@_admin_required
def emp_delete(request, pk):
    emp = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        username = emp.username
        emp.delete()
        _log(request, 'delete', 'employees', f'Deleted employee {username}')
        messages.success(request, f'Employee "{username}" deleted.')
        return redirect('admin_panel:emp_list')
    return render(request, 'admin_panel/employees/confirm_delete.html', {'emp': emp})


# ─────────────────────────────────────────────────────────────────────────────
# 4. DEPARTMENTS
# ─────────────────────────────────────────────────────────────────────────────

@_admin_required
def dept_list(request):
    if request.method == 'POST':
        name = request.POST.get('name','').strip()
        code = request.POST.get('code','').strip()
        if name:
            Department.objects.get_or_create(name=name, defaults={'code': code})
            messages.success(request, f'Department "{name}" created.')
        return redirect('admin_panel:dept_list')
    depts = Department.objects.annotate(member_count=Count('members'))
    return render(request, 'admin_panel/employees/departments.html', {'depts': depts})


# ─────────────────────────────────────────────────────────────────────────────
# 5. SALARY MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

@_admin_required
def salary_list(request):
    today = date.today()
    month = int(request.GET.get('month', today.month))
    year  = int(request.GET.get('year', today.year))
    q     = request.GET.get('q', '')
    records = SalaryRecord.objects.filter(
        month=month, year=year
    ).select_related('employee').order_by('employee__username')
    if q:
        records = records.filter(employee__username__icontains=q)
    return render(request, 'admin_panel/employees/salary_list.html', {
        'records': records, 'month': month, 'year': year,
        'total_paid': records.filter(status='paid').aggregate(t=Sum('net_salary'))['t'] or 0,
        'months': list(range(1,13)),
        'years': list(range(today.year-2, today.year+1)),
    })


@_admin_required
def salary_add(request):
    if request.method == 'POST':
        d    = request.POST
        uid  = d.get('employee', '')
        emp  = get_object_or_404(User, pk=uid)
        month = int(d.get('month', date.today().month))
        year  = int(d.get('year',  date.today().year))
        rec, created = SalaryRecord.objects.get_or_create(
            employee=emp, month=month, year=year,
            defaults={
                'basic_salary': d.get('basic_salary', 0) or 0,
                'hra':          d.get('hra', 0) or 0,
                'allowances':   d.get('allowances', 0) or 0,
                'incentives':   d.get('incentives', 0) or 0,
                'deductions':   d.get('deductions', 0) or 0,
                'tax_deducted': d.get('tax_deducted', 0) or 0,
                'created_by':   request.user,
            }
        )
        if not created:
            rec.basic_salary = d.get('basic_salary', 0) or 0
            rec.hra          = d.get('hra', 0) or 0
            rec.allowances   = d.get('allowances', 0) or 0
            rec.incentives   = d.get('incentives', 0) or 0
            rec.deductions   = d.get('deductions', 0) or 0
            rec.tax_deducted = d.get('tax_deducted', 0) or 0
        rec.compute_net()
        rec.status = d.get('status', 'pending')
        rec.save()
        _log(request, 'create', 'salary', f'Salary record for {emp.username} {month}/{year}')
        messages.success(request, f'Salary saved for {emp.username}.')
        return redirect('admin_panel:salary_list')
    employees = User.objects.filter(is_staff=True)
    return render(request, 'admin_panel/employees/salary_form.html', {
        'employees': employees,
        'status_choices': SalaryRecord.STATUS_CHOICES,
        'months': list(range(1,13)),
        'years': list(range(date.today().year-2, date.today().year+1)),
    })


# ─────────────────────────────────────────────────────────────────────────────
# 6. LEAVE MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

@_admin_required
def leave_list(request):
    status = request.GET.get('status', '')
    leaves = EmployeeLeave.objects.select_related('employee','approved_by').order_by('-created_at')
    if status:
        leaves = leaves.filter(status=status)
    return render(request, 'admin_panel/employees/leave_list.html', {
        'leaves': leaves, 'status_filter': status,
        'status_choices': EmployeeLeave.STATUS_CHOICES,
        'total': leaves.count(),
        'pending': leaves.filter(status='pending').count(),
    })


@_admin_required
def leave_action(request, pk):
    leave = get_object_or_404(EmployeeLeave, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action in ('approved', 'rejected'):
            leave.status      = action
            leave.approved_by = request.user
            leave.admin_notes = request.POST.get('notes', '').strip()
            leave.save()
            _log(request, 'approve' if action == 'approved' else 'reject',
                 'leaves', f'{action.title()} leave for {leave.employee.username}')
            messages.success(request, f'Leave {action}.')
    return redirect('admin_panel:leave_list')


# ─────────────────────────────────────────────────────────────────────────────
# 7. ATTENDANCE MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

@_admin_required
def attendance_overview(request):
    target_date = request.GET.get('date', str(date.today()))
    try:
        from datetime import datetime
        d = datetime.strptime(target_date, '%Y-%m-%d').date()
    except ValueError:
        d = date.today()

    staff = User.objects.filter(Q(is_staff=True)|Q(is_superuser=True))
    records = {
        a.employee_id: a
        for a in EmployeeAttendance.objects.filter(date=d)
    }
    if request.method == 'POST':
        for user in staff:
            status = request.POST.get(f'status_{user.pk}','')
            if status:
                EmployeeAttendance.objects.update_or_create(
                    employee=user, date=d,
                    defaults={
                        'status':    status,
                        'marked_by': request.user,
                        'check_in':  request.POST.get(f'checkin_{user.pk}') or None,
                        'check_out': request.POST.get(f'checkout_{user.pk}') or None,
                    }
                )
        messages.success(request, f'Attendance saved for {d}.')
        return redirect(f'{request.path}?date={d}')

    present = sum(1 for uid, r in records.items() if r.status=='present')
    return render(request, 'admin_panel/employees/attendance.html', {
        'staff': staff, 'records': records, 'target_date': d,
        'present': present, 'total_staff': staff.count(),
        'status_choices': EmployeeAttendance.STATUS_CHOICES,
    })


# ─────────────────────────────────────────────────────────────────────────────
# 8. ORDERS MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

@_admin_required
def order_list(request):
    q      = request.GET.get('q', '')
    status = request.GET.get('status', 'all')
    period = request.GET.get('period', 'all')
    orders = Order.objects.prefetch_related('items').select_related('user').order_by('-created_at')

    if q:
        orders = orders.filter(
            Q(order_id__icontains=q)|Q(full_name__icontains=q)|
            Q(phone__icontains=q)|Q(email__icontains=q)
        )
    if status != 'all':
        orders = orders.filter(status=status)
    today = date.today()
    if period == 'today':
        orders = orders.filter(created_at__date=today)
    elif period == 'week':
        orders = orders.filter(created_at__date__gte=today-timedelta(days=7))
    elif period == 'month':
        orders = orders.filter(created_at__date__gte=today.replace(day=1))

    total_revenue = orders.filter(status='delivered').aggregate(t=Sum('total'))['t'] or 0
    return render(request, 'admin_panel/orders/list.html', {
        'orders': orders[:200], 'q': q, 'status_filter': status,
        'period': period, 'total': orders.count(),
        'total_revenue': total_revenue,
        'status_choices': Order.STATUS_CHOICES,
    })


@_admin_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    from apps.orders.models import OrderStatusLog
    logs = order.status_logs.all()
    if request.method == 'POST':
        new_status = request.POST.get('status', '').strip()
        note       = request.POST.get('note', '').strip()
        if new_status and new_status != order.status:
            order.status = new_status
            order.save(update_fields=['status', 'updated_at'])
            OrderStatusLog.objects.create(
                order=order, status=new_status,
                message=note or f'Status → {order.get_status_display()}',
            )
            _log(request, 'update', 'orders', f'Order {order.order_id} → {new_status}')
            messages.success(request, f'Order {order.order_id} updated to {order.get_status_display()}.')
        return redirect('admin_panel:order_detail', order_id=order_id)
    return render(request, 'admin_panel/orders/detail.html', {
        'order': order, 'logs': logs,
        'status_choices': Order.STATUS_CHOICES,
    })


@_admin_required
def order_add(request):
    """Create a new order manually from the admin panel."""
    from apps.orders.models import OrderItem, OrderStatusLog
    customers = User.objects.filter(is_staff=False, is_superuser=False).order_by('username')
    products_qs = Product.objects.all().order_by('brand', 'name')
    if request.method == 'POST':
        d = request.POST
        try:
            user_id = d.get('user_id', '')
            order_user = User.objects.filter(pk=user_id).first() if user_id else None

            order = Order.objects.create(
                user=order_user,
                full_name=d.get('full_name', '').strip(),
                phone=d.get('phone', '').strip(),
                email=d.get('email', '').strip(),
                address_line1=d.get('address_line1', '').strip(),
                address_line2=d.get('address_line2', '').strip(),
                city=d.get('city', '').strip(),
                state=d.get('state', '').strip(),
                pincode=d.get('pincode', '').strip(),
                payment_method=d.get('payment_method', 'cod'),
                payment_status=d.get('payment_status', 'pending'),
                status=d.get('status', 'pending'),
                subtotal=d.get('subtotal', 0) or 0,
                delivery_charge=d.get('delivery_charge', 0) or 0,
                discount=d.get('discount', 0) or 0,
                total=d.get('total', 0) or 0,
                order_notes=d.get('order_notes', '').strip(),
            )
            # Add items
            product_ids = d.getlist('item_product[]')
            item_names  = d.getlist('item_name[]')
            item_prices = d.getlist('item_price[]')
            item_qtys   = d.getlist('item_qty[]')
            for idx, iname in enumerate(item_names):
                iname = iname.strip()
                if not iname:
                    continue
                prod = Product.objects.filter(pk=product_ids[idx]).first() if idx < len(product_ids) and product_ids[idx] else None
                OrderItem.objects.create(
                    order=order,
                    product=prod,
                    name=iname,
                    brand=prod.brand if prod else '',
                    sku=prod.sku if prod else '',
                    price=item_prices[idx] if idx < len(item_prices) else 0,
                    quantity=item_qtys[idx] if idx < len(item_qtys) else 1,
                )
            OrderStatusLog.objects.create(
                order=order, status=order.status,
                message=f'Order created by admin {request.user.username}',
            )
            _log(request, 'create', 'orders', f'Created order {order.order_id} for {order.full_name}')
            messages.success(request, f'Order {order.order_id} created.')
            return redirect('admin_panel:order_detail', order_id=order.order_id)
        except Exception as e:
            messages.error(request, f'Error creating order: {e}')
    return render(request, 'admin_panel/orders/form.html', {
        'action': 'Create', 'order': None,
        'customers': customers, 'products_qs': products_qs,
        'status_choices': Order.STATUS_CHOICES,
        'payment_choices': Order.PAYMENT_CHOICES,
    })


@_admin_required
def order_edit(request, order_id):
    """Edit an existing order from the admin panel."""
    from apps.orders.models import OrderItem, OrderStatusLog
    order = get_object_or_404(Order, order_id=order_id)
    customers = User.objects.filter(is_staff=False, is_superuser=False).order_by('username')
    products_qs = Product.objects.all().order_by('brand', 'name')
    if request.method == 'POST':
        d = request.POST
        old_status = order.status
        user_id = d.get('user_id', '')
        order.user = User.objects.filter(pk=user_id).first() if user_id else order.user
        order.full_name = d.get('full_name', order.full_name).strip()
        order.phone = d.get('phone', order.phone).strip()
        order.email = d.get('email', order.email).strip()
        order.address_line1 = d.get('address_line1', order.address_line1).strip()
        order.address_line2 = d.get('address_line2', order.address_line2).strip()
        order.city = d.get('city', order.city).strip()
        order.state = d.get('state', order.state).strip()
        order.pincode = d.get('pincode', order.pincode).strip()
        order.payment_method = d.get('payment_method', order.payment_method)
        order.payment_status = d.get('payment_status', order.payment_status)
        order.status = d.get('status', order.status)
        order.subtotal = d.get('subtotal', order.subtotal) or order.subtotal
        order.delivery_charge = d.get('delivery_charge', order.delivery_charge) or 0
        order.discount = d.get('discount', order.discount) or 0
        order.total = d.get('total', order.total) or order.total
        order.order_notes = d.get('order_notes', order.order_notes).strip()
        order.save()
        if order.status != old_status:
            OrderStatusLog.objects.create(
                order=order, status=order.status,
                message=f'Status updated by admin {request.user.username}',
            )
        _log(request, 'update', 'orders', f'Updated order {order.order_id}')
        messages.success(request, f'Order {order.order_id} updated.')
        return redirect('admin_panel:order_detail', order_id=order_id)
    return render(request, 'admin_panel/orders/form.html', {
        'action': 'Edit', 'order': order,
        'customers': customers, 'products_qs': products_qs,
        'status_choices': Order.STATUS_CHOICES,
        'payment_choices': Order.PAYMENT_CHOICES,
    })


@_admin_required
def order_delete(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    if request.method == 'POST':
        oid = order.order_id
        order.delete()
        _log(request, 'delete', 'orders', f'Deleted order {oid}')
        messages.success(request, f'Order {oid} deleted.')
        return redirect('admin_panel:order_list')
    return render(request, 'admin_panel/orders/confirm_delete.html', {'order': order})


# ─────────────────────────────────────────────────────────────────────────────
# 9. PRODUCT MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

@_admin_required
def product_list(request):
    q    = request.GET.get('q', '')
    cat  = request.GET.get('cat', '')
    prng = request.GET.get('range', '')
    products = Product.objects.all()
    if q:
        products = products.filter(Q(name__icontains=q)|Q(brand__icontains=q)|Q(sku__icontains=q))
    if prng:
        products = products.filter(product_range=prng)
    if cat:
        products = products.filter(category=cat)

    # Build category choices filtered by range for JS-driven cascading
    # Map range → valid categories
    RANGE_CATEGORY_MAP = {
        'korean':    ['cleanser','toner','essence','serum','ampoule','moisturizer','cream',
                      'emulsion','sunscreen','mask','eye_cream','exfoliator','oil','mist'],
        'makeup':    ['primer','foundation','concealer','setting_powder','powder','blush',
                      'bronzer','highlighter','eyeshadow','eyeshadow_palette','eyeliner',
                      'mascara','lipstick','lip_gloss','lip_liner'],
        'ayurvedic': ['cleanser','toner','serum','moisturizer','cream','mask','oil'],
        'pharmacy':  ['cleanser','serum','moisturizer','sunscreen','eye_cream'],
    }
    # All range choices excluding 'treatment'
    range_choices_filtered = [(v, l) for v, l in Product.RANGE_CHOICES if v != 'treatment']
    # Get category choices for current range (or all if no range)
    if prng and prng in RANGE_CATEGORY_MAP:
        allowed_cats = RANGE_CATEGORY_MAP[prng]
        cat_choices_filtered = [(v, l) for v, l in Product.CATEGORY_CHOICES if v in allowed_cats]
    else:
        cat_choices_filtered = Product.CATEGORY_CHOICES

    import json as _json
    range_cat_map_json = _json.dumps(RANGE_CATEGORY_MAP)
    all_cat_choices_json = _json.dumps({v: l for v, l in Product.CATEGORY_CHOICES})

    return render(request, 'admin_panel/products/list.html', {
        'products': products.order_by('brand','name'), 'q': q, 'cat': cat, 'prng': prng,
        'total': products.count(),
        'cat_choices': cat_choices_filtered,
        'range_choices': range_choices_filtered,
        'range_cat_map_json': range_cat_map_json,
        'all_cat_choices_json': all_cat_choices_json,
    })


@_admin_required
def product_add_admin(request):
    RANGE_CHOICES_FILTERED = [(v, l) for v, l in Product.RANGE_CHOICES if v != 'treatment']
    if request.method == 'POST':
        d = request.POST
        try:
            p = Product.objects.create(
                name=d.get('name', '').strip(),
                brand=d.get('brand', '').strip(),
                category=d.get('category', 'cleanser'),
                product_range=d.get('product_range', 'korean'),
                sku=d.get('sku', '').strip(),
                price=d.get('price') or None,
                description=d.get('description', '').strip(),
                key_ingredients=d.get('key_ingredients', '').strip(),
                image_url=d.get('image_url', '').strip(),
                is_featured='is_featured' in d,
            )
            _log(request, 'create', 'products', f'Created product "{p.name}" [{p.sku}]')
            messages.success(request, f'Product "{p.name}" added successfully.')
            return redirect('admin_panel:product_list')
        except Exception as e:
            messages.error(request, f'Error: {e}')
    import json as _json
    RANGE_CATEGORY_MAP = {
        'korean':    ['cleanser','toner','essence','serum','ampoule','moisturizer','cream',
                      'emulsion','sunscreen','mask','eye_cream','exfoliator','oil','mist'],
        'makeup':    ['primer','foundation','concealer','setting_powder','powder','blush',
                      'bronzer','highlighter','eyeshadow','eyeshadow_palette','eyeliner',
                      'mascara','lipstick','lip_gloss','lip_liner'],
        'ayurvedic': ['cleanser','toner','serum','moisturizer','cream','mask','oil'],
        'pharmacy':  ['cleanser','serum','moisturizer','sunscreen','eye_cream'],
    }
    return render(request, 'admin_panel/products/form.html', {
        'action': 'Add', 'product': None,
        'range_choices': RANGE_CHOICES_FILTERED,
        'cat_choices': Product.CATEGORY_CHOICES,
        'range_cat_map_json': _json.dumps(RANGE_CATEGORY_MAP),
        'all_cat_choices_json': _json.dumps({v: l for v, l in Product.CATEGORY_CHOICES}),
    })


@_admin_required
def product_edit_admin(request, pk):
    product = get_object_or_404(Product, pk=pk)
    RANGE_CHOICES_FILTERED = [(v, l) for v, l in Product.RANGE_CHOICES if v != 'treatment']
    if request.method == 'POST':
        d = request.POST
        try:
            product.name = d.get('name', product.name).strip()
            product.brand = d.get('brand', product.brand).strip()
            product.category = d.get('category', product.category)
            product.product_range = d.get('product_range', product.product_range)
            product.sku = d.get('sku', product.sku).strip()
            product.price = d.get('price') or None
            product.description = d.get('description', '').strip()
            product.key_ingredients = d.get('key_ingredients', '').strip()
            product.image_url = d.get('image_url', '').strip()
            product.is_featured = 'is_featured' in d
            product.save()
            _log(request, 'update', 'products', f'Updated product "{product.name}" [{product.sku}]')
            messages.success(request, f'"{product.name}" updated.')
            return redirect('admin_panel:product_list')
        except Exception as e:
            messages.error(request, f'Error: {e}')
    import json as _json
    RANGE_CATEGORY_MAP = {
        'korean':    ['cleanser','toner','essence','serum','ampoule','moisturizer','cream',
                      'emulsion','sunscreen','mask','eye_cream','exfoliator','oil','mist'],
        'makeup':    ['primer','foundation','concealer','setting_powder','powder','blush',
                      'bronzer','highlighter','eyeshadow','eyeshadow_palette','eyeliner',
                      'mascara','lipstick','lip_gloss','lip_liner'],
        'ayurvedic': ['cleanser','toner','serum','moisturizer','cream','mask','oil'],
        'pharmacy':  ['cleanser','serum','moisturizer','sunscreen','eye_cream'],
    }
    return render(request, 'admin_panel/products/form.html', {
        'action': 'Edit', 'product': product,
        'range_choices': RANGE_CHOICES_FILTERED,
        'cat_choices': Product.CATEGORY_CHOICES,
        'range_cat_map_json': _json.dumps(RANGE_CATEGORY_MAP),
        'all_cat_choices_json': _json.dumps({v: l for v, l in Product.CATEGORY_CHOICES}),
    })


@_admin_required
def product_delete_admin(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        name = product.name
        product.delete()
        _log(request, 'delete', 'products', f'Deleted product "{name}"')
        messages.success(request, f'Product "{name}" deleted.')
        return redirect('admin_panel:product_list')
    return render(request, 'admin_panel/products/confirm_delete.html', {'product': product})


# ─────────────────────────────────────────────────────────────────────────────
# 10. CRM OVERVIEW
# ─────────────────────────────────────────────────────────────────────────────

@_admin_required
def crm_overview(request):
    period = request.GET.get('period', 'month')
    today  = date.today()
    if period == 'today':
        start = today
    elif period == 'week':
        start = today - timedelta(days=7)
    elif period == 'year':
        start = today.replace(month=1, day=1)
    else:
        start = today.replace(day=1)

    leads     = Lead.objects.filter(created_at__date__gte=start)
    opps      = Opportunity.objects.filter(created_at__date__gte=start)
    calls     = CallLog.objects.filter(called_at__date__gte=start)

    stage_data = list(leads.values('stage').annotate(c=Count('id')).order_by('-c'))
    top_emp    = list(
        leads.values('assigned_to__username').annotate(c=Count('id')).order_by('-c')[:5]
    )
    source_data = list(leads.values('source').annotate(c=Count('id')).order_by('-c'))

    return render(request, 'admin_panel/crm/overview.html', {
        'period': period, 'start': start,
        'total_leads': leads.count(),
        'converted_leads': leads.filter(is_converted=True).count(),
        'total_opps': opps.count(),
        'won_opps': opps.filter(stage='won').count(),
        'opp_value': opps.filter(stage='won').aggregate(v=Sum('value'))['v'] or 0,
        'total_calls': calls.count(),
        'connected': calls.filter(status='connected').count(),
        'stage_data': stage_data,
        'top_emp': top_emp,
        'source_data': source_data,
        'recent_leads': Lead.objects.order_by('-created_at')[:10],
    })


# ─────────────────────────────────────────────────────────────────────────────
# 11. ANALYTICS & REPORTS
# ─────────────────────────────────────────────────────────────────────────────

@_admin_required
def analytics(request):
    today = date.today()
    period = request.GET.get('period', 'month')
    if period == 'today':
        start = today
    elif period == 'week':
        start = today - timedelta(days=7)
    elif period == 'year':
        start = today.replace(month=1, day=1)
    else:
        start = today.replace(day=1)

    orders_qs  = Order.objects.filter(created_at__date__gte=start)
    revenue    = orders_qs.filter(status='delivered').aggregate(t=Sum('total'))['t'] or 0
    avg_order  = orders_qs.filter(status='delivered').aggregate(a=Avg('total'))['a'] or 0

    leads_qs   = Lead.objects.filter(created_at__date__gte=start)
    scans_qs   = ScanResult.objects.filter(created_at__date__gte=start)
    tickets_qs = SupportTicket.objects.filter(created_at__date__gte=start)

    # Monthly revenue trend (12 months)
    monthly_data = []
    for i in range(11, -1, -1):
        d = today.replace(day=1)
        for _ in range(i):
            d = (d - timedelta(days=1)).replace(day=1)
        try:
            m_end = d.replace(month=d.month % 12 + 1, day=1) if d.month < 12 else d.replace(year=d.year+1, month=1, day=1)
        except ValueError:
            m_end = d.replace(day=28) + timedelta(days=4)
            m_end = m_end.replace(day=1)
        rev = Order.objects.filter(
            created_at__date__gte=d, created_at__date__lt=m_end, status='delivered'
        ).aggregate(t=Sum('total'))['t'] or 0
        monthly_data.append({'month': d.strftime('%b %y'), 'revenue': float(rev)})

    # Top categories
    top_cats = list(
        OrderItem.objects.filter(order__created_at__date__gte=start)
        .values('name').annotate(cnt=Count('id'), rev=Sum('price'))
        .order_by('-cnt')[:8]
    )

    # User growth (last 6 months)
    user_growth = []
    for i in range(5, -1, -1):
        d = today.replace(day=1)
        for _ in range(i):
            d = (d - timedelta(days=1)).replace(day=1)
        cnt = User.objects.filter(
            date_joined__date__gte=d,
            is_staff=False
        ).count()
        user_growth.append({'month': d.strftime('%b'), 'users': cnt})

    # Support resolution rate
    total_t  = tickets_qs.count()
    resolved = tickets_qs.filter(status='resolved').count()
    res_rate = round((resolved / total_t * 100), 1) if total_t else 0

    return render(request, 'admin_panel/analytics.html', {
        'period': period, 'start': start,
        'revenue': revenue, 'avg_order': avg_order,
        'order_count': orders_qs.count(),
        'lead_count': leads_qs.count(),
        'scan_count': scans_qs.count(),
        'ticket_count': total_t,
        'res_rate': res_rate,
        'monthly_data': monthly_data,
        'top_cats': top_cats,
        'user_growth': user_growth,
        'periods_list': [
            ('today','Today'),('week','This Week'),
            ('month','This Month'),('year','This Year'),
        ],
    })


@_admin_required
def export_report(request):
    section = request.GET.get('section', 'orders')
    period  = request.GET.get('period', 'month')
    today   = date.today()
    if period == 'today':
        start = today
    elif period == 'week':
        start = today - timedelta(days=7)
    elif period == 'year':
        start = today.replace(month=1, day=1)
    else:
        start = today.replace(day=1)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        f'attachment; filename="lumina_admin_{section}_{period}_{today}.csv"'
    )
    w = csv.writer(response)

    if section == 'orders':
        w.writerow(['Order ID','Customer','Email','Phone','Status','Total','Date'])
        for o in Order.objects.filter(created_at__date__gte=start).order_by('-created_at'):
            w.writerow([o.order_id, o.full_name, o.email, o.phone,
                        o.get_status_display(), o.total, o.created_at.strftime('%d %b %Y')])
    elif section == 'users':
        w.writerow(['Username','Email','Tier','Active','Date Joined'])
        for u in User.objects.filter(
            is_staff=False, date_joined__date__gte=start
        ).select_related('profile'):
            tier = getattr(getattr(u, 'profile', None), 'tier', 'N/A')
            w.writerow([u.username, u.email, tier, u.is_active, u.date_joined.strftime('%d %b %Y')])
    elif section == 'leads':
        w.writerow(['Lead ID','Name','Phone','Stage','Source','Assigned To','Date'])
        for l in Lead.objects.filter(created_at__date__gte=start):
            w.writerow([l.lead_id, l.name, l.phone, l.stage, l.source,
                        l.assigned_to.username if l.assigned_to else '', l.created_at.strftime('%d %b %Y')])
    elif section == 'employees':
        w.writerow(['Username','Email','First Name','Last Name','Department','Status','Joined'])
        for u in User.objects.filter(is_staff=True).select_related('emp_profile'):
            p = getattr(u, 'emp_profile', None)
            dept = str(p.department) if p and p.department else ''
            status = p.status if p else ''
            w.writerow([u.username, u.email, u.first_name, u.last_name,
                        dept, status, u.date_joined.strftime('%d %b %Y')])

    _log(request, 'export', section, f'Exported {section} report ({period})')
    return response


# ─────────────────────────────────────────────────────────────────────────────
# 12. SETTINGS
# ─────────────────────────────────────────────────────────────────────────────

@_admin_required
def settings_view(request):
    settings_obj, _ = CompanySettings.objects.get_or_create(pk=1)
    if request.method == 'POST':
        d = request.POST
        settings_obj.company_name    = d.get('company_name', settings_obj.company_name)
        settings_obj.company_email   = d.get('company_email', settings_obj.company_email)
        settings_obj.support_email   = d.get('support_email', settings_obj.support_email)
        settings_obj.hr_email        = d.get('hr_email', settings_obj.hr_email)
        settings_obj.sales_email     = d.get('sales_email', settings_obj.sales_email)
        settings_obj.marketing_email = d.get('marketing_email', settings_obj.marketing_email)
        settings_obj.phone           = d.get('phone', settings_obj.phone)
        settings_obj.address         = d.get('address', settings_obj.address)
        settings_obj.city            = d.get('city', settings_obj.city)
        settings_obj.state           = d.get('state', settings_obj.state)
        settings_obj.gstin           = d.get('gstin', settings_obj.gstin)
        settings_obj.website         = d.get('website', settings_obj.website)
        settings_obj.smtp_host       = d.get('smtp_host', settings_obj.smtp_host)
        settings_obj.smtp_port       = int(d.get('smtp_port', settings_obj.smtp_port) or 587)
        settings_obj.save()
        _log(request, 'update', 'settings', 'Company settings updated')
        messages.success(request, 'Settings saved.')
        return redirect('admin_panel:settings')
    return render(request, 'admin_panel/settings.html', {'company': settings_obj})


# ─────────────────────────────────────────────────────────────────────────────
# 13. ADMIN TASKS
# ─────────────────────────────────────────────────────────────────────────────

@_admin_required
def task_list(request):
    status = request.GET.get('status', '')
    tasks  = AdminTask.objects.select_related('assigned_to','created_by').order_by('-created_at')
    if status:
        tasks = tasks.filter(status=status)
    if request.method == 'POST':
        d = request.POST
        assign_id = d.get('assigned_to', '')
        assigned  = User.objects.filter(pk=assign_id).first() if assign_id else None
        AdminTask.objects.create(
            title=d.get('title','').strip(),
            description=d.get('description','').strip(),
            priority=d.get('priority','medium'),
            due_date=d.get('due_date') or None,
            assigned_to=assigned,
            created_by=request.user,
        )
        messages.success(request, 'Task created.')
        return redirect('admin_panel:task_list')
    staff = User.objects.filter(is_staff=True)
    return render(request, 'admin_panel/tasks.html', {
        'tasks': tasks, 'status_filter': status,
        'status_choices': AdminTask.STATUS_CHOICES,
        'priority_choices': AdminTask.PRIORITY_CHOICES,
        'staff': staff,
    })


@_admin_required
def task_update(request, pk):
    task = get_object_or_404(AdminTask, pk=pk)
    if request.method == 'POST':
        task.status = request.POST.get('status', task.status)
        task.save()
        messages.success(request, 'Task updated.')
    return redirect('admin_panel:task_list')


# ─────────────────────────────────────────────────────────────────────────────
# 14. AUDIT LOG
# ─────────────────────────────────────────────────────────────────────────────

@_admin_required
def audit_log(request):
    q      = request.GET.get('q', '')
    action = request.GET.get('action', '')
    module = request.GET.get('module', '')
    logs   = AdminActivity.objects.select_related('admin').order_by('-created_at')
    if q:
        logs = logs.filter(Q(description__icontains=q)|Q(admin__username__icontains=q))
    if action:
        logs = logs.filter(action=action)
    if module:
        logs = logs.filter(module=module)
    return render(request, 'admin_panel/audit_log.html', {
        'logs': logs[:200], 'q': q, 'action_filter': action, 'module_filter': module,
        'action_choices': AdminActivity.ACTION_CHOICES,
    })


# ─────────────────────────────────────────────────────────────────────────────
# 15. QUICK AJAX ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@_admin_required
def dashboard_kpis(request):
    """Returns live KPI JSON for dashboard cards refresh."""
    today = date.today()
    data = {
        'today_orders': Order.objects.filter(created_at__date=today).count(),
        'open_tickets': SupportTicket.objects.filter(status__in=['open','in_progress']).count(),
        'today_leads':  Lead.objects.filter(created_at__date=today).count(),
        'today_revenue': str(
            Order.objects.filter(created_at__date=today, status='delivered')
            .aggregate(t=Sum('total'))['t'] or 0
        ),
    }
    return JsonResponse(data)


# ─────────────────────────────────────────────────────────────────────────────
# 16. USER EDIT
# ─────────────────────────────────────────────────────────────────────────────

@_admin_required
def user_edit(request, pk):
    target_user = get_object_or_404(User, pk=pk)
    try:
        profile = target_user.profile
    except Exception:
        profile = None

    if request.method == 'POST':
        d = request.POST
        target_user.first_name = d.get('first_name', target_user.first_name).strip()
        target_user.last_name  = d.get('last_name', target_user.last_name).strip()
        target_user.email      = d.get('email', target_user.email).strip()
        new_pass = d.get('new_password', '').strip()
        if new_pass:
            target_user.set_password(new_pass)
        target_user.save()
        if profile:
            profile.tier = d.get('tier', profile.tier)
            profile.save()
        _log(request, 'update', 'users', f'Admin edited user {target_user.username}')
        messages.success(request, f'User {target_user.username} updated.')
        return redirect('admin_panel:user_detail', pk=pk)

    return render(request, 'admin_panel/users/edit.html', {
        'target_user': target_user,
        'profile': profile,
        'tier_choices': UserProfile.TIER_CHOICES,
    })


# ─────────────────────────────────────────────────────────────────────────────
# 17. ADMIN CRM — LEADS
# ─────────────────────────────────────────────────────────────────────────────

@_admin_required
def crm_leads(request):
    q      = request.GET.get('q', '')
    stage  = request.GET.get('stage', '')
    source = request.GET.get('source', '')
    emp_id = request.GET.get('emp', '')
    today  = date.today()

    leads = Lead.objects.select_related('assigned_to').order_by('-created_at')
    if q:
        leads = leads.filter(Q(name__icontains=q)|Q(phone__icontains=q)|Q(email__icontains=q))
    if stage:
        leads = leads.filter(stage=stage)
    if source:
        leads = leads.filter(source=source)
    if emp_id:
        leads = leads.filter(assigned_to__pk=emp_id)

    employees = User.objects.filter(is_staff=True).order_by('username')
    return render(request, 'admin_panel/crm/leads.html', {
        'leads': leads[:200], 'q': q, 'stage': stage, 'source': source,
        'total': leads.count(),
        'stage_choices': Lead.STAGE_CHOICES,
        'source_choices': Lead.SOURCE_CHOICES,
        'employees': employees,
        'today': today,
    })


@_admin_required
def crm_lead_edit(request, lead_id):
    lead = get_object_or_404(Lead, lead_id=lead_id)
    if request.method == 'POST':
        d = request.POST
        lead.name        = d.get('name', lead.name).strip()
        lead.phone       = d.get('phone', lead.phone).strip()
        lead.email       = d.get('email', lead.email).strip()
        lead.city        = d.get('city', lead.city).strip()
        lead.source      = d.get('source', lead.source)
        lead.stage       = d.get('stage', lead.stage)
        lead.notes       = d.get('notes', lead.notes).strip()
        emp_id = d.get('assigned_to', '')
        lead.assigned_to = User.objects.filter(pk=emp_id).first() if emp_id else lead.assigned_to
        lead.follow_up_date = d.get('follow_up_date') or None
        lead.save()
        _log(request, 'update', 'crm', f'Updated lead {lead.lead_id}')
        messages.success(request, f'Lead {lead.lead_id} updated.')
        return redirect('admin_panel:crm_leads')
    employees = User.objects.filter(is_staff=True).order_by('username')
    return render(request, 'admin_panel/crm/lead_edit.html', {
        'lead': lead,
        'stage_choices': Lead.STAGE_CHOICES,
        'source_choices': Lead.SOURCE_CHOICES,
        'employees': employees,
    })


# ─────────────────────────────────────────────────────────────────────────────
# 18. ADMIN CRM — OPPORTUNITIES
# ─────────────────────────────────────────────────────────────────────────────

@_admin_required
def crm_opportunities(request):
    stage = request.GET.get('stage', '')
    opps = Opportunity.objects.select_related('assigned_to', 'lead').order_by('-created_at')
    if stage:
        opps = opps.filter(stage=stage)
    total_value = opps.aggregate(t=Sum('value'))['t'] or 0
    return render(request, 'admin_panel/crm/opportunities.html', {
        'opps': opps[:200], 'stage': stage,
        'stage_choices': Opportunity.STAGE_CHOICES,
        'total_value': total_value,
    })


# ─────────────────────────────────────────────────────────────────────────────
# 19. ADMIN CRM — CALLING CENTER
# ─────────────────────────────────────────────────────────────────────────────

@_admin_required
def crm_calling(request):
    today  = date.today()
    emp_id = request.GET.get('emp', '')
    status = request.GET.get('status', '')

    calls = CallLog.objects.select_related('employee').order_by('-called_at')
    if emp_id:
        calls = calls.filter(employee__pk=emp_id)
    if status:
        calls = calls.filter(status=status)

    pending_cbs = CallbackRequest.objects.filter(status='pending').order_by('-created_at')
    today_calls_qs = CallLog.objects.filter(called_at__date=today)
    employees = User.objects.filter(is_staff=True).order_by('username')

    # Stats
    stats = {
        'total_today':     today_calls_qs.count(),
        'connected_today': today_calls_qs.filter(status='connected').count(),
        'pending_cbs':     pending_cbs.count(),
        'total_all':       calls.count(),
    }
    return render(request, 'admin_panel/crm/calling.html', {
        'calls': calls[:200], 'pending_cbs': pending_cbs,
        'today_calls': today_calls_qs[:50],
        'status_choices': CallLog.CALL_STATUS_CHOICES,
        'employees': employees,
        'emp_filter': emp_id,
        'status_filter': status,
        'stats': stats,
        'today': today,
    })


# ─────────────────────────────────────────────────────────────────────────────
# 20. ADMIN CRM — SUPPORT TICKETS
# ─────────────────────────────────────────────────────────────────────────────

@_admin_required
def crm_support(request):
    q        = request.GET.get('q', '')
    status   = request.GET.get('status', '')
    priority = request.GET.get('priority', '')
    emp_id   = request.GET.get('emp', '')

    tickets = SupportTicket.objects.select_related('assigned_to', 'customer').order_by('-created_at')
    if q:
        tickets = tickets.filter(Q(subject__icontains=q)|Q(customer_name__icontains=q)|Q(ticket_id__icontains=q))
    if status:
        tickets = tickets.filter(status=status)
    if priority:
        tickets = tickets.filter(priority=priority)
    if emp_id:
        tickets = tickets.filter(assigned_to__pk=emp_id)

    employees = User.objects.filter(is_staff=True).order_by('username')
    stats = {
        'total':      tickets.count(),
        'open':       tickets.filter(status='open').count(),
        'in_progress':tickets.filter(status='in_progress').count(),
        'resolved':   tickets.filter(status='resolved').count(),
        'critical':   tickets.filter(priority='critical').count(),
    }
    return render(request, 'admin_panel/crm/support.html', {
        'tickets': tickets[:200], 'q': q,
        'status_filter': status, 'priority_filter': priority,
        'status_choices': SupportTicket.STATUS_CHOICES,
        'priority_choices': SupportTicket.PRIORITY_CHOICES,
        'employees': employees, 'emp_filter': emp_id,
        'stats': stats,
    })


@_admin_required
def crm_ticket_detail(request, ticket_id):
    from apps.employee.models import TicketReply
    ticket = get_object_or_404(SupportTicket, ticket_id=ticket_id)
    replies = ticket.replies.all().order_by('created_at')
    employees = User.objects.filter(is_staff=True).order_by('username')

    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'reply':
            msg = request.POST.get('message', '').strip()
            if msg:
                TicketReply.objects.create(
                    ticket=ticket, author=request.user,
                    message=msg,
                    is_internal='is_internal' in request.POST,
                )
                _log(request, 'update', 'support', f'Reply on ticket {ticket_id}')
        elif action == 'update_status':
            ticket.status      = request.POST.get('status', ticket.status)
            ticket.priority    = request.POST.get('priority', ticket.priority)
            emp_id = request.POST.get('assigned_to', '')
            if emp_id:
                ticket.assigned_to = User.objects.filter(pk=emp_id).first()
            if ticket.status == 'resolved' and not ticket.resolved_at:
                ticket.resolved_at = timezone.now()
            ticket.save()
            _log(request, 'update', 'support', f'Updated ticket {ticket_id} → {ticket.status}')
            messages.success(request, 'Ticket updated.')
        return redirect('admin_panel:crm_ticket_detail', ticket_id=ticket_id)

    return render(request, 'admin_panel/crm/ticket_detail.html', {
        'ticket': ticket, 'replies': replies,
        'employees': employees,
        'status_choices': SupportTicket.STATUS_CHOICES,
        'priority_choices': SupportTicket.PRIORITY_CHOICES,
    })


# ─────────────────────────────────────────────────────────────────────────────
# 21. ADMIN CRM — CAMPAIGNS
# ─────────────────────────────────────────────────────────────────────────────

@_admin_required
def crm_campaigns(request):
    q      = request.GET.get('q', '')
    status = request.GET.get('status', '')
    camps  = Campaign.objects.order_by('-created_at')
    if q:
        camps = camps.filter(Q(name__icontains=q)|Q(camp_id__icontains=q))
    if status:
        camps = camps.filter(status=status)
    total_budget = camps.aggregate(t=Sum('budget'))['t'] or 0
    total_revenue = camps.aggregate(t=Sum('revenue'))['t'] or 0
    return render(request, 'admin_panel/crm/campaigns.html', {
        'camps': camps[:200], 'q': q, 'status_filter': status,
        'status_choices': Campaign.STATUS_CHOICES,
        'type_choices': Campaign.TYPE_CHOICES,
        'total_budget': total_budget,
        'total_revenue': total_revenue,
    })


# ─────────────────────────────────────────────────────────────────────────────
# 22. ADMIN CRM — INTERNAL NOTES
# ─────────────────────────────────────────────────────────────────────────────

@_admin_required
def crm_notes(request):
    tag    = request.GET.get('tag', '')
    emp_id = request.GET.get('emp', '')
    notes  = InternalNote.objects.select_related('author').order_by('-created_at')
    if tag:
        notes = notes.filter(tag=tag)
    if emp_id:
        notes = notes.filter(author__pk=emp_id)

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        note_tag = request.POST.get('tag', 'general')
        if content:
            InternalNote.objects.create(
                author=request.user,
                content=content,
                tag=note_tag,
            )
            _log(request, 'create', 'notes', f'Admin created internal note')
            messages.success(request, 'Note added.')
        return redirect('admin_panel:crm_notes')

    employees = User.objects.filter(is_staff=True).order_by('username')
    return render(request, 'admin_panel/crm/notes.html', {
        'notes': notes[:100], 'tag_filter': tag, 'emp_filter': emp_id,
        'tag_choices': InternalNote.TAG_CHOICES,
        'employees': employees,
    })


# ─────────────────────────────────────────────────────────────────────────────
# 23. ADMIN CRM — REPORTS
# ─────────────────────────────────────────────────────────────────────────────

@_admin_required
def crm_reports(request):
    period = request.GET.get('period', 'month')
    today  = date.today()
    if period == 'today':
        start = today
    elif period == 'week':
        start = today - timedelta(days=7)
    elif period == 'year':
        start = today.replace(month=1, day=1)
    else:
        start = today.replace(day=1)

    orders_qs  = Order.objects.filter(created_at__date__gte=start)
    revenue    = orders_qs.filter(status='delivered').aggregate(t=Sum('total'))['t'] or 0
    avg_order  = orders_qs.filter(status='delivered').aggregate(a=Avg('total'))['a'] or 0
    order_cnt  = orders_qs.count()

    leads_qs       = Lead.objects.filter(created_at__date__gte=start)
    lead_cnt       = leads_qs.count()
    converted_leads = leads_qs.filter(is_converted=True).count()

    calls_qs  = CallLog.objects.filter(called_at__date__gte=start)
    call_cnt  = calls_qs.count()

    tickets_qs     = SupportTicket.objects.filter(created_at__date__gte=start)
    ticket_cnt     = tickets_qs.count()
    resolved_tickets = tickets_qs.filter(status='resolved').count()

    # Lead by stage
    lead_by_stage = list(
        leads_qs.values('stage').annotate(c=Count('id')).order_by('-c')
    )
    # Call by status
    call_by_status = list(
        calls_qs.values('status').annotate(c=Count('id')).order_by('-c')
    )
    # Ticket by status
    ticket_by_status = list(
        tickets_qs.values('status').annotate(c=Count('id')).order_by('-c')
    )
    # Employee performance (calls)
    emp_perf = list(
        calls_qs.values('employee__username').annotate(calls=Count('id')).order_by('-calls')[:10]
    )

    return render(request, 'admin_panel/crm/reports.html', {
        'period': period,
        'periods_list': [
            ('today','Today'),('week','This Week'),
            ('month','This Month'),('year','This Year'),
        ],
        'revenue': revenue, 'avg_order': avg_order,
        'order_cnt': order_cnt, 'lead_cnt': lead_cnt or 1,
        'converted_leads': converted_leads,
        'call_cnt': call_cnt or 1, 'ticket_cnt': ticket_cnt,
        'resolved_tickets': resolved_tickets,
        'lead_by_stage': lead_by_stage,
        'call_by_status': call_by_status,
        'ticket_by_status': ticket_by_status,
        'emp_perf': emp_perf,
    })
