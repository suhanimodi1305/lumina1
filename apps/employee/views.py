"""
Unified Employee CRM Workspace — Views
All modules: Dashboard, CRM, Orders, Support, Calling, Marketing,
             Products, Sales, Collaboration, Tasks, Calendar, Reports
"""
import csv
import io
import json
from datetime import date, timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from django.db.models import Q, Count, Sum, Avg
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.products.models import Product, SkinConcern
from apps.orders.models import Order, OrderStatusLog, UserRequirement
from apps.memberships.models import UserProfile

from .models import (
    EmployeeLoginLog, EmployeeAttendance, Lead, Opportunity,
    CallLog, SupportTicket, TicketReply, Campaign,
    InternalNote, CallbackRequest, SalesTarget
)


# ─────────────────────────────────────────────────────────────────────────────
# AUTH HELPER
# ─────────────────────────────────────────────────────────────────────────────

def _is_staff(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def _staff_required(fn):
    """Decorator that replaces redirect for non-staff."""
    from functools import wraps
    @wraps(fn)
    def wrapper(request, *args, **kwargs):
        if not _is_staff(request.user):
            return redirect('core:home')
        return fn(request, *args, **kwargs)
    return login_required(wrapper)


# ─────────────────────────────────────────────────────────────────────────────
# 1. MAIN DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────

@_staff_required
def portal(request):
    today = date.today()
    emp   = request.user

    # Today's sales target
    target_obj = SalesTarget.objects.filter(employee=emp, date=today).first()
    target_val   = target_obj.target   if target_obj else 0
    achieved_val = target_obj.achieved if target_obj else 0
    target_pct   = target_obj.pct      if target_obj else 0

    ctx = {
        # CRM
        'new_leads':        Lead.objects.filter(stage='new').count(),
        'followups':        Lead.objects.filter(follow_up_date=today).count(),
        'my_leads':         Lead.objects.filter(assigned_to=emp).count(),
        # Orders
        'pending_orders':   Order.objects.filter(
                                status__in=['pending','confirmed','packed']
                            ).count(),
        'today_orders':     Order.objects.filter(created_at__date=today).count(),
        # Support
        'open_tickets':     SupportTicket.objects.filter(status__in=['open','in_progress']).count(),
        'pending_callbacks':CallbackRequest.objects.filter(status='pending').count(),
        # Calling
        'today_calls':      CallLog.objects.filter(called_at__date=today).count(),
        # Chat (existing Conversation model)
        'live_chats':       0,  # placeholder — real-time via websocket
        # Sales target
        'target_val':    target_val,
        'achieved_val':  achieved_val,
        'target_pct':    target_pct,
        # Recent
        'recent_leads':  Lead.objects.filter(assigned_to=emp).order_by('-created_at')[:5],
        'recent_orders': Order.objects.order_by('-created_at')[:5],
        'recent_tickets':SupportTicket.objects.filter(
                             status__in=['open','in_progress']
                         ).order_by('-created_at')[:5],
        'recent_calls':  CallLog.objects.filter(employee=emp).order_by('-called_at')[:5],
        'recent_notes':  InternalNote.objects.order_by('-created_at')[:8],
        'pending_cbs':   CallbackRequest.objects.filter(
                             status='pending'
                         ).order_by('-created_at')[:5],
        'today': today,
    }
    return render(request, 'employee/portal.html', ctx)


# ─────────────────────────────────────────────────────────────────────────────
# 2. CRM — LEADS
# ─────────────────────────────────────────────────────────────────────────────

@_staff_required
def lead_list(request):
    q      = request.GET.get('q', '')
    stage  = request.GET.get('stage', '')
    source = request.GET.get('source', '')
    leads  = Lead.objects.select_related('assigned_to').order_by('-created_at')
    if q:
        leads = leads.filter(
            Q(name__icontains=q)|Q(phone__icontains=q)|Q(email__icontains=q)
        )
    if stage:
        leads = leads.filter(stage=stage)
    if source:
        leads = leads.filter(source=source)
    return render(request, 'employee/crm/lead_list.html', {
        'leads': leads, 'q': q, 'stage': stage, 'source': source,
        'stage_choices':  Lead.STAGE_CHOICES,
        'source_choices': Lead.SOURCE_CHOICES,
        'total': leads.count(),
    })


@_staff_required
def lead_detail(request, lead_id):
    lead = get_object_or_404(Lead, lead_id=lead_id)
    calls    = CallLog.objects.filter(lead=lead).order_by('-called_at')
    notes    = InternalNote.objects.filter(lead=lead).order_by('-created_at')
    opps     = Opportunity.objects.filter(lead=lead)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_stage':
            lead.stage = request.POST.get('stage', lead.stage)
            lead.notes = request.POST.get('notes', lead.notes)
            lead.follow_up_date = request.POST.get('follow_up_date') or None
            lead.save()
            messages.success(request, 'Lead updated.')
        elif action == 'add_note':
            content = request.POST.get('content', '').strip()
            if content:
                InternalNote.objects.create(
                    author=request.user, content=content,
                    lead=lead, tag=request.POST.get('tag', 'lead')
                )
                messages.success(request, 'Note added.')
        return redirect('employee:lead_detail', lead_id=lead_id)
    staff = User.objects.filter(Q(is_staff=True)|Q(is_superuser=True))
    return render(request, 'employee/crm/lead_detail.html', {
        'lead': lead, 'calls': calls, 'notes': notes, 'opps': opps,
        'stage_choices': Lead.STAGE_CHOICES,
        'tag_choices':   InternalNote.TAG_CHOICES,
        'staff': staff,
    })


@_staff_required
def lead_create(request):
    if request.method == 'POST':
        d = request.POST
        lead = Lead.objects.create(
            name=d.get('name','').strip(),
            phone=d.get('phone','').strip(),
            email=d.get('email','').strip(),
            city=d.get('city','').strip(),
            source=d.get('source','website'),
            stage=d.get('stage','new'),
            skin_concern=d.get('skin_concern','').strip(),
            budget=d.get('budget','').strip(),
            notes=d.get('notes','').strip(),
            assigned_to=request.user,
            created_by=request.user,
            follow_up_date=d.get('follow_up_date') or None,
        )
        messages.success(request, f'Lead {lead.lead_id} created.')
        return redirect('employee:lead_detail', lead_id=lead.lead_id)
    return render(request, 'employee/crm/lead_form.html', {
        'stage_choices': Lead.STAGE_CHOICES,
        'source_choices': Lead.SOURCE_CHOICES,
    })


# ─────────────────────────────────────────────────────────────────────────────
# 3. CRM — CUSTOMERS (360 view)
# ─────────────────────────────────────────────────────────────────────────────

@_staff_required
def customer_list(request):
    q    = request.GET.get('q', '')
    tier = request.GET.get('tier', '')
    users = User.objects.filter(is_staff=False, is_superuser=False).select_related('profile')
    if q:
        users = users.filter(
            Q(username__icontains=q)|Q(email__icontains=q)|
            Q(first_name__icontains=q)|Q(last_name__icontains=q)
        )
    if tier:
        users = users.filter(profile__tier=tier)
    return render(request, 'employee/crm/customer_list.html', {
        'customers': users.order_by('-date_joined'),
        'q': q, 'tier': tier,
        'tier_choices': UserProfile.TIER_CHOICES,
        'total': users.count(),
    })


@_staff_required
def customer_360(request, pk):
    """Full 360° customer view."""
    customer = get_object_or_404(User, pk=pk)
    orders   = Order.objects.filter(user=customer).order_by('-created_at')[:10]
    tickets  = SupportTicket.objects.filter(customer=customer).order_by('-created_at')[:10]
    calls    = CallLog.objects.filter(customer=customer).order_by('-called_at')[:10]
    leads    = Lead.objects.filter(linked_user=customer).order_by('-created_at')[:5]
    notes    = InternalNote.objects.filter(customer=customer).order_by('-created_at')[:10]
    try:
        profile = customer.profile
    except Exception:
        profile = None

    # Revenue from this customer
    revenue = Order.objects.filter(
        user=customer, status='delivered'
    ).aggregate(total=Sum('total'))['total'] or 0

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            InternalNote.objects.create(
                author=request.user, content=content,
                customer=customer, tag=request.POST.get('tag','general')
            )
            messages.success(request, 'Note added.')
        return redirect('employee:customer_360', pk=pk)

    return render(request, 'employee/crm/customer_360.html', {
        'customer': customer, 'profile': profile,
        'orders': orders, 'tickets': tickets,
        'calls': calls, 'leads': leads, 'notes': notes,
        'revenue': revenue,
        'tag_choices': InternalNote.TAG_CHOICES,
    })


# ─────────────────────────────────────────────────────────────────────────────
# 4. OPPORTUNITIES
# ─────────────────────────────────────────────────────────────────────────────

@_staff_required
def opportunity_list(request):
    stage = request.GET.get('stage', '')
    opps  = Opportunity.objects.select_related('lead','assigned_to').order_by('-created_at')
    if stage:
        opps = opps.filter(stage=stage)
    total_value = opps.aggregate(v=Sum('value'))['v'] or 0
    return render(request, 'employee/crm/opportunity_list.html', {
        'opps': opps, 'stage': stage,
        'stage_choices': Opportunity.STAGE_CHOICES,
        'total_value': total_value,
    })


# ─────────────────────────────────────────────────────────────────────────────
# 5. CALLING CENTER
# ─────────────────────────────────────────────────────────────────────────────

@_staff_required
def call_center(request):
    """Incoming / pending callback requests — main call center view."""
    pending_cbs = CallbackRequest.objects.filter(
        status__in=['pending', 'assigned']
    ).order_by('-created_at')
    today_calls = CallLog.objects.filter(
        employee=request.user, called_at__date=date.today()
    ).order_by('-called_at')
    return render(request, 'employee/calling/call_center.html', {
        'pending_cbs':  pending_cbs,
        'today_calls':  today_calls,
        'status_choices': CallLog.CALL_STATUS_CHOICES,
    })


@_staff_required
def call_history(request):
    q = request.GET.get('q', '')
    direction = request.GET.get('direction', '')
    status    = request.GET.get('status', '')
    calls = CallLog.objects.select_related('employee', 'lead').order_by('-called_at')
    if q:
        calls = calls.filter(
            Q(phone__icontains=q)|Q(customer_name__icontains=q)|
            Q(call_id__icontains=q)
        )
    if direction:
        calls = calls.filter(direction=direction)
    if status:
        calls = calls.filter(status=status)
    return render(request, 'employee/calling/call_history.html', {
        'calls': calls, 'q': q, 'direction': direction, 'status': status,
        'direction_choices': CallLog.DIRECTION_CHOICES,
        'status_choices':    CallLog.CALL_STATUS_CHOICES,
    })


@_staff_required
def log_call(request):
    """Log a new call (outbound or note a received call)."""
    if request.method == 'POST':
        d = request.POST
        lead_id = d.get('lead_id', '').strip()
        lead = Lead.objects.filter(lead_id=lead_id).first() if lead_id else None
        CallLog.objects.create(
            employee=request.user,
            lead=lead,
            customer_name=d.get('customer_name', '').strip(),
            phone=d.get('phone', '').strip(),
            direction=d.get('direction', 'outbound'),
            status=d.get('status', 'connected'),
            duration_seconds=int(d.get('duration_seconds', 0) or 0),
            notes=d.get('notes', '').strip(),
            follow_up_date=d.get('follow_up_date') or None,
            follow_up_time=d.get('follow_up_time') or None,
        )
        messages.success(request, 'Call logged.')
        next_url = d.get('next', 'employee:call_center')
        return redirect(next_url if '/' in next_url else next_url)
    leads = Lead.objects.filter(
        assigned_to=request.user
    ).order_by('-created_at')[:50]
    return render(request, 'employee/calling/log_call.html', {
        'leads': leads,
        'direction_choices': CallLog.DIRECTION_CHOICES,
        'status_choices':    CallLog.CALL_STATUS_CHOICES,
    })


@_staff_required
def callback_resolve(request, pk):
    """Mark a callback request as resolved."""
    cb = get_object_or_404(CallbackRequest, pk=pk)
    if request.method == 'POST':
        cb.status = 'resolved'
        cb.is_resolved = True
        cb.resolved_at = timezone.now()
        cb.employee_notes = request.POST.get('notes', cb.employee_notes)
        cb.assigned_to = request.user
        cb.save()
        messages.success(request, f'Callback for {cb.name} marked resolved.')
    return redirect('employee:call_center')


@require_POST
def request_callback(request):
    """
    Public-facing endpoint: customer clicks Help/Call button on site.
    Creates a CallbackRequest visible to all employees.
    """
    d = request.POST
    user = request.user if request.user.is_authenticated else None
    cb = CallbackRequest.objects.create(
        customer=user,
        name=d.get('name','').strip(),
        phone=d.get('phone','').strip(),
        email=d.get('email','').strip(),
        issue_summary=d.get('issue','').strip() or 'Customer requested a callback.',
        preferred_time=d.get('preferred_time','').strip(),
    )
    return JsonResponse({'ok': True, 'id': cb.pk, 'message': 'We will call you back shortly!'})


# ─────────────────────────────────────────────────────────────────────────────
# 6. SUPPORT TICKETS
# ─────────────────────────────────────────────────────────────────────────────

@_staff_required
def ticket_list(request):
    q        = request.GET.get('q', '')
    status   = request.GET.get('status', '')
    priority = request.GET.get('priority', '')
    tickets  = SupportTicket.objects.select_related('assigned_to','customer').order_by('-created_at')
    if q:
        tickets = tickets.filter(
            Q(ticket_id__icontains=q)|Q(subject__icontains=q)|
            Q(customer_name__icontains=q)|Q(customer_phone__icontains=q)
        )
    if status:
        tickets = tickets.filter(status=status)
    if priority:
        tickets = tickets.filter(priority=priority)
    return render(request, 'employee/support/ticket_list.html', {
        'tickets': tickets, 'q': q, 'status': status, 'priority': priority,
        'status_choices':   SupportTicket.STATUS_CHOICES,
        'priority_choices': SupportTicket.PRIORITY_CHOICES,
        'total': tickets.count(),
        'open_count': tickets.filter(status='open').count(),
    })


@_staff_required
def ticket_detail(request, ticket_id):
    ticket  = get_object_or_404(SupportTicket, ticket_id=ticket_id)
    replies = ticket.replies.all()
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'reply':
            msg = request.POST.get('message', '').strip()
            if msg:
                TicketReply.objects.create(
                    ticket=ticket, author=request.user,
                    message=msg,
                    is_internal='is_internal' in request.POST,
                )
                messages.success(request, 'Reply added.')
        elif action == 'update':
            ticket.status   = request.POST.get('status', ticket.status)
            ticket.priority = request.POST.get('priority', ticket.priority)
            assign_id = request.POST.get('assigned_to', '')
            if assign_id:
                try:
                    ticket.assigned_to = User.objects.get(pk=int(assign_id))
                except Exception:
                    pass
            if ticket.status == 'resolved' and not ticket.resolved_at:
                ticket.resolved_at = timezone.now()
            ticket.save()
            messages.success(request, 'Ticket updated.')
        return redirect('employee:ticket_detail', ticket_id=ticket_id)
    staff = User.objects.filter(Q(is_staff=True)|Q(is_superuser=True))
    return render(request, 'employee/support/ticket_detail.html', {
        'ticket': ticket, 'replies': replies, 'staff': staff,
        'status_choices':   SupportTicket.STATUS_CHOICES,
        'priority_choices': SupportTicket.PRIORITY_CHOICES,
    })


@_staff_required
def ticket_create(request):
    if request.method == 'POST':
        d = request.POST
        ticket = SupportTicket.objects.create(
            customer_name=d.get('customer_name','').strip(),
            customer_email=d.get('customer_email','').strip(),
            customer_phone=d.get('customer_phone','').strip(),
            subject=d.get('subject','').strip(),
            description=d.get('description','').strip(),
            channel=d.get('channel','chat'),
            priority=d.get('priority','medium'),
            assigned_to=request.user,
        )
        messages.success(request, f'Ticket {ticket.ticket_id} created.')
        return redirect('employee:ticket_detail', ticket_id=ticket.ticket_id)
    return render(request, 'employee/support/ticket_form.html', {
        'channel_choices':  SupportTicket.CHANNEL_CHOICES,
        'priority_choices': SupportTicket.PRIORITY_CHOICES,
    })


# ─────────────────────────────────────────────────────────────────────────────
# 7. MARKETING CAMPAIGNS
# ─────────────────────────────────────────────────────────────────────────────

@_staff_required
def campaign_list(request):
    status = request.GET.get('status', '')
    camps  = Campaign.objects.select_related('created_by').order_by('-created_at')
    if status:
        camps = camps.filter(status=status)
    return render(request, 'employee/marketing/campaign_list.html', {
        'camps': camps, 'status': status,
        'status_choices': Campaign.STATUS_CHOICES,
        'type_choices':   Campaign.TYPE_CHOICES,
    })


@_staff_required
def campaign_detail(request, camp_id):
    camp = get_object_or_404(Campaign, camp_id=camp_id)
    if request.method == 'POST':
        camp.status  = request.POST.get('status', camp.status)
        camp.leads_generated = int(request.POST.get('leads_generated', camp.leads_generated) or 0)
        camp.conversions     = int(request.POST.get('conversions', camp.conversions) or 0)
        camp.revenue         = request.POST.get('revenue', camp.revenue) or 0
        camp.spent           = request.POST.get('spent', camp.spent) or 0
        camp.save()
        messages.success(request, 'Campaign updated.')
        return redirect('employee:campaign_detail', camp_id=camp_id)
    return render(request, 'employee/marketing/campaign_detail.html', {
        'camp': camp,
        'status_choices': Campaign.STATUS_CHOICES,
    })


@_staff_required
def campaign_create(request):
    if request.method == 'POST':
        d = request.POST
        camp = Campaign.objects.create(
            name=d.get('name','').strip(),
            type=d.get('type','email'),
            description=d.get('description','').strip(),
            target_audience=d.get('target_audience','').strip(),
            budget=d.get('budget',0) or 0,
            status='draft',
            created_by=request.user,
            scheduled_at=d.get('scheduled_at') or None,
        )
        messages.success(request, f'Campaign {camp.camp_id} created.')
        return redirect('employee:campaign_detail', camp_id=camp.camp_id)
    return render(request, 'employee/marketing/campaign_form.html', {
        'type_choices': Campaign.TYPE_CHOICES,
    })


# ─────────────────────────────────────────────────────────────────────────────
# 8. INTERNAL NOTES (Team Collaboration)
# ─────────────────────────────────────────────────────────────────────────────

@_staff_required
def internal_notes(request):
    tag    = request.GET.get('tag', '')
    author = request.GET.get('author', '')
    notes  = InternalNote.objects.select_related('author').order_by('-created_at')
    if tag:
        notes = notes.filter(tag=tag)
    if author:
        notes = notes.filter(author__username=author)
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            InternalNote.objects.create(
                author=request.user,
                content=content,
                tag=request.POST.get('tag', 'general'),
                order_ref=request.POST.get('order_ref', '').strip(),
            )
            messages.success(request, 'Note posted.')
        return redirect('employee:internal_notes')
    staff = User.objects.filter(Q(is_staff=True)|Q(is_superuser=True))
    return render(request, 'employee/collab/internal_notes.html', {
        'notes': notes[:50], 'tag': tag, 'author': author,
        'tag_choices': InternalNote.TAG_CHOICES,
        'staff': staff,
    })


# ─────────────────────────────────────────────────────────────────────────────
# 9. ORDERS (existing, kept compatible)
# ─────────────────────────────────────────────────────────────────────────────

@_staff_required
def order_list(request):
    q      = request.GET.get('q', '')
    status = request.GET.get('status', 'all')
    orders = Order.objects.prefetch_related('items').order_by('-created_at')
    if q:
        orders = orders.filter(
            Q(order_id__icontains=q)|Q(full_name__icontains=q)|
            Q(phone__icontains=q)|Q(tracking_id__icontains=q)|
            Q(email__icontains=q)
        )
    if status != 'all':
        orders = orders.filter(status=status)
    return render(request, 'employee/orders/order_list.html', {
        'orders': orders, 'q': q, 'status_filter': status,
        'status_choices': Order.STATUS_CHOICES,
        'total': orders.count(),
    })


@_staff_required
def order_detail_emp(request, order_id):
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
                order=order, status=new_status,
                message=note or f'Status → {order.get_status_display()}',
                location=location,
            )
            if new_status == 'delivered' and order.user:
                try:
                    from django.conf import settings as dj_s
                    from django.db.models import F
                    profile, _ = UserProfile.objects.get_or_create(user=order.user)
                    pts = int(order.total // 100) * dj_s.PURCHASE_POINTS_RATE
                    if pts > 0:
                        UserProfile.objects.filter(pk=profile.pk).update(
                            loyalty_points=F('loyalty_points') + pts
                        )
                except Exception:
                    pass
            messages.success(request, f'Order {order.order_id} → {order.get_status_display()}')
        return redirect('employee:order_detail', order_id=order_id)
    return render(request, 'employee/orders/order_detail.html', {
        'order': order, 'logs': logs,
        'status_choices': Order.STATUS_CHOICES,
    })


@_staff_required
def requirement_list(request):
    q = request.GET.get('q', '')
    status = request.GET.get('status', 'all')
    reqs = UserRequirement.objects.prefetch_related('products').select_related('user','assigned_to')
    if q:
        reqs = reqs.filter(
            Q(req_id__icontains=q)|Q(user__username__icontains=q)|
            Q(title__icontains=q)|Q(full_name__icontains=q)|Q(phone__icontains=q)
        )
    if status != 'all':
        reqs = reqs.filter(status=status)
    return render(request, 'employee/orders/requirement_list.html', {
        'reqs': reqs, 'q': q, 'status_filter': status,
        'status_choices': UserRequirement.STATUS_CHOICES,
    })


@_staff_required
def requirement_detail_emp(request, req_id):
    req = get_object_or_404(UserRequirement, req_id=req_id)
    if request.method == 'POST':
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
            except Exception:
                pass
        req.save()
        messages.success(request, f'Requirement {req.req_id} updated.')
        return redirect('employee:requirement_detail', req_id=req_id)
    staff = User.objects.filter(Q(is_staff=True)|Q(is_superuser=True))
    return render(request, 'employee/orders/requirement_detail.html', {
        'req': req,
        'status_choices':   UserRequirement.STATUS_CHOICES,
        'priority_choices': UserRequirement.PRIORITY_CHOICES,
        'staff_users': staff,
    })


# ─────────────────────────────────────────────────────────────────────────────
# 10. PRODUCTS (existing, kept compatible)
# ─────────────────────────────────────────────────────────────────────────────

@_staff_required
def product_list(request):
    q      = request.GET.get('q', '')
    range_ = request.GET.get('range', 'all')
    cat    = request.GET.get('category', 'all')
    products = Product.objects.exclude(product_range='treatment').order_by('brand', 'name')
    if q:
        products = products.filter(
            Q(name__icontains=q)|Q(brand__icontains=q)|Q(sku__icontains=q)
        )
    if range_ != 'all':
        products = products.filter(product_range=range_)
    if cat != 'all':
        products = products.filter(category=cat)
    return render(request, 'employee/products/product_list.html', {
        'products': products, 'q': q, 'range_': range_, 'cat': cat,
        'total': products.count(),
    })


@_staff_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'employee/products/product_detail.html', {'product': product})


@_staff_required
def product_add(request):
    if request.method == 'POST':
        d = request.POST
        try:
            p = Product.objects.create(
                name=d.get('name','').strip(), brand=d.get('brand','').strip(),
                category=d.get('category','cleanser'),
                product_range=d.get('product_range','korean'),
                sku=d.get('sku','').strip(), price=d.get('price') or None,
                description=d.get('description','').strip(),
                key_ingredients=d.get('key_ingredients','').strip(),
                full_ingredients=d.get('full_ingredients','').strip(),
                image_url=d.get('image_url','').strip(),
                coverage=d.get('coverage','').strip(),
                finish=d.get('finish','').strip(),
                undertone_match=d.get('undertone_match',''),
                skin_tone_match=d.get('skin_tone_match',''),
                is_featured='is_featured' in d,
            )
            messages.success(request, f'Product "{p.name}" added.')
            return redirect('employee:product_detail', pk=p.pk)
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return render(request, 'employee/products/product_form.html', {'action': 'Add', 'product': None})


@_staff_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        d = request.POST
        try:
            product.name = d.get('name', product.name).strip()
            product.brand = d.get('brand', product.brand).strip()
            product.category = d.get('category', product.category)
            product.product_range = d.get('product_range', product.product_range)
            product.sku = d.get('sku', product.sku).strip()
            product.price = d.get('price') or None
            product.description = d.get('description','').strip()
            product.key_ingredients = d.get('key_ingredients','').strip()
            product.full_ingredients = d.get('full_ingredients','').strip()
            product.image_url = d.get('image_url','').strip()
            product.coverage = d.get('coverage','').strip()
            product.finish = d.get('finish','').strip()
            product.undertone_match = d.get('undertone_match','')
            product.skin_tone_match = d.get('skin_tone_match','')
            product.is_featured = 'is_featured' in d
            product.save()
            messages.success(request, f'"{product.name}" updated.')
            return redirect('employee:product_detail', pk=product.pk)
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return render(request, 'employee/products/product_form.html', {'action': 'Edit', 'product': product})


@_staff_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f'"{name}" deleted.')
        return redirect('employee:product_list')
    return render(request, 'employee/products/product_confirm_delete.html', {'product': product})


@_staff_required
def export_products(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="lumina_products.csv"'
    w = csv.writer(response)
    w.writerow(['SKU','Name','Brand','Category','Range','Price','Key Ingredients','Featured'])
    for p in Product.objects.all().order_by('brand','name'):
        w.writerow([p.sku,p.name,p.brand,p.category,p.product_range,
                    p.price or '',p.key_ingredients,p.is_featured])
    return response


@_staff_required
def bulk_import(request):
    results = []
    if request.method == 'POST':
        mode = request.POST.get('mode', 'csv')

        # ── CSV Upload ────────────────────────────────────────────────────
        if mode == 'csv' and request.FILES.get('csv_file'):
            from django.conf import settings as _s
            f = request.FILES['csv_file']
            if f.size > getattr(_s, 'MAX_CSV_UPLOAD_BYTES', 1 * 1024 * 1024):
                messages.error(request, 'File too large (max 1 MB).')
                return redirect('employee:bulk_import')
            try:
                raw = f.read()
                # Try UTF-8 with BOM first, then fall back to Windows-1252
                try:
                    decoded = raw.decode('utf-8-sig')
                except UnicodeDecodeError:
                    decoded = raw.decode('windows-1252', errors='replace')
            except Exception as e:
                messages.error(request, f'Could not read file: {e}')
                return redirect('employee:bulk_import')
            reader = csv.DictReader(io.StringIO(decoded))
            created = updated = errors = 0
            for row in reader:
                sku = row.get('sku', '').strip()
                if not sku:
                    errors += 1
                    continue
                try:
                    obj, was_created = Product.objects.update_or_create(
                        sku=sku, defaults={
                            'name': row.get('name', '').strip(),
                            'brand': row.get('brand', '').strip(),
                            'category': row.get('category', 'cleanser').strip(),
                            'product_range': row.get('product_range', 'korean').strip(),
                            'price': row.get('price') or None,
                            'description': row.get('description', '').strip(),
                            'key_ingredients': row.get('key_ingredients', '').strip(),
                            'image_url': row.get('image_url', '').strip(),
                            'is_featured': row.get('is_featured', '').lower() in ('1', 'true', 'yes'),
                        }
                    )
                    if was_created:
                        created += 1
                    else:
                        updated += 1
                    results.append({
                        'status': 'created' if was_created else 'updated',
                        'name': obj.name, 'sku': sku,
                    })
                except Exception as e:
                    errors += 1
                    results.append({'status': 'error', 'sku': sku, 'msg': str(e)})
            messages.success(request, f'CSV import done — {created} created, {updated} updated, {errors} errors.')

        # ── Manual Entry ──────────────────────────────────────────────────
        elif mode == 'manual':
            d = request.POST
            sku = d.get('sku', '').strip()
            name = d.get('name', '').strip()
            if not sku or not name:
                messages.error(request, 'Name and SKU are required.')
            else:
                try:
                    obj, was_created = Product.objects.update_or_create(
                        sku=sku, defaults={
                            'name': name,
                            'brand': d.get('brand', '').strip(),
                            'category': d.get('category', 'cleanser').strip(),
                            'product_range': d.get('product_range', 'korean').strip(),
                            'price': d.get('price') or None,
                            'description': d.get('description', '').strip(),
                            'key_ingredients': d.get('key_ingredients', '').strip(),
                            'image_url': d.get('image_url', '').strip(),
                            'is_featured': 'is_featured' in d,
                        }
                    )
                    action = 'created' if was_created else 'updated'
                    messages.success(request, f'Product "{obj.name}" {action} successfully.')
                    results.append({'status': action, 'name': obj.name, 'sku': sku})
                except Exception as e:
                    messages.error(request, f'Error saving product: {e}')

    return render(request, 'employee/products/bulk_import.html', {
        'results': results,
        'category_choices': Product.CATEGORY_CHOICES,
        'range_choices': Product.RANGE_CHOICES,
    })


@_staff_required
def clear_products(request):
    if request.method == 'POST':
        range_ = request.POST.get('range','all')
        if range_ == 'makeup':
            deleted, _ = Product.objects.filter(product_range='makeup').delete()
        elif range_ == 'korean':
            deleted, _ = Product.objects.filter(product_range='korean').delete()
        else:
            deleted, _ = Product.objects.all().delete()
        messages.success(request, f'Deleted {deleted} product(s).')
    return redirect('employee:product_list')


# ─────────────────────────────────────────────────────────────────────────────
# 11. REPORTS & ANALYTICS — with Excel export
# ─────────────────────────────────────────────────────────────────────────────

@_staff_required
def reports(request):
    today = date.today()
    period = request.GET.get('period', 'today')

    if period == 'today':
        start = today
    elif period == 'week':
        start = today - timedelta(days=7)
    elif period == 'month':
        start = today.replace(day=1)
    elif period == 'year':
        start = today.replace(month=1, day=1)
    else:
        start = today

    orders_qs = Order.objects.filter(created_at__date__gte=start)
    leads_qs  = Lead.objects.filter(created_at__date__gte=start)
    calls_qs  = CallLog.objects.filter(called_at__date__gte=start)
    tickets_qs= SupportTicket.objects.filter(created_at__date__gte=start)

    # Sales
    revenue   = orders_qs.filter(status='delivered').aggregate(t=Sum('total'))['t'] or 0
    order_cnt = orders_qs.count()
    avg_order = orders_qs.filter(status='delivered').aggregate(a=Avg('total'))['a'] or 0

    # Lead funnel
    lead_by_stage = list(
        leads_qs.values('stage').annotate(c=Count('id')).order_by('-c')
    )

    # Call stats
    call_by_status = list(
        calls_qs.values('status').annotate(c=Count('id')).order_by('-c')
    )

    # Ticket stats
    ticket_by_status = list(
        tickets_qs.values('status').annotate(c=Count('id'))
    )

    # Employee performance
    emp_perf = list(
        CallLog.objects.filter(called_at__date__gte=start)
            .values('employee__username')
            .annotate(calls=Count('id'))
            .order_by('-calls')[:10]
    )

    return render(request, 'employee/reports/reports.html', {
        'period': period, 'start': start,
        'revenue': revenue, 'order_cnt': order_cnt, 'avg_order': avg_order,
        'lead_cnt': leads_qs.count(),
        'converted_leads': leads_qs.filter(is_converted=True).count(),
        'call_cnt': calls_qs.count(),
        'ticket_cnt': tickets_qs.count(),
        'resolved_tickets': tickets_qs.filter(status='resolved').count(),
        'lead_by_stage': lead_by_stage,
        'call_by_status': call_by_status,
        'ticket_by_status': ticket_by_status,
        'emp_perf': emp_perf,
        'periods_list': [
            ('today', 'Today'),
            ('week',  'This Week'),
            ('month', 'This Month'),
            ('year',  'This Year'),
        ],
    })


@_staff_required
def export_report_excel(request):
    """
    Export full CRM report to CSV (Excel-compatible).
    Admin sees monthly/yearly breakdown; employee sees their own data.
    """
    period  = request.GET.get('period', 'month')
    section = request.GET.get('section', 'orders')
    today   = date.today()

    if period == 'today':
        start = today
    elif period == 'week':
        start = today - timedelta(days=7)
    elif period == 'month':
        start = today.replace(day=1)
    elif period == 'year':
        start = today.replace(month=1, day=1)
    else:
        start = today.replace(day=1)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        f'attachment; filename="lumina_{section}_{period}_{today}.csv"'
    )
    w = csv.writer(response)

    if section == 'orders':
        w.writerow(['Order ID','Customer','Phone','Email','Status',
                    'Payment','Total','Created'])
        for o in Order.objects.filter(created_at__date__gte=start).order_by('-created_at'):
            w.writerow([o.order_id, o.full_name, o.phone, o.email,
                        o.get_status_display(), o.get_payment_method_display(),
                        o.total, o.created_at.strftime('%d %b %Y %H:%M')])

    elif section == 'leads':
        w.writerow(['Lead ID','Name','Phone','Email','Source','Stage',
                    'Assigned To','Follow-up','Created'])
        for l in Lead.objects.filter(created_at__date__gte=start).order_by('-created_at'):
            w.writerow([l.lead_id, l.name, l.phone, l.email,
                        l.get_source_display(), l.get_stage_display(),
                        l.assigned_to.username if l.assigned_to else '',
                        l.follow_up_date or '', l.created_at.strftime('%d %b %Y %H:%M')])

    elif section == 'calls':
        w.writerow(['Call ID','Employee','Customer Name','Phone','Direction',
                    'Status','Duration','Called At'])
        for c in CallLog.objects.filter(called_at__date__gte=start).order_by('-called_at'):
            w.writerow([c.call_id, c.employee.username, c.customer_name, c.phone,
                        c.get_direction_display(), c.get_status_display(),
                        c.duration_display, c.called_at.strftime('%d %b %Y %H:%M')])

    elif section == 'tickets':
        w.writerow(['Ticket ID','Customer','Phone','Subject','Channel',
                    'Priority','Status','Assigned To','Created','Resolved'])
        for t in SupportTicket.objects.filter(created_at__date__gte=start).order_by('-created_at'):
            w.writerow([t.ticket_id, t.customer_name, t.customer_phone, t.subject,
                        t.get_channel_display(), t.get_priority_display(),
                        t.get_status_display(),
                        t.assigned_to.username if t.assigned_to else '',
                        t.created_at.strftime('%d %b %Y %H:%M'),
                        t.resolved_at.strftime('%d %b %Y %H:%M') if t.resolved_at else ''])

    elif section == 'attendance':
        w.writerow(['Employee','Date','Status','Check In','Check Out','Notes'])
        qs = EmployeeAttendance.objects.filter(date__gte=start).order_by('-date','employee__username')
        for a in qs:
            w.writerow([a.employee.username, a.date, a.get_status_display(),
                        a.check_in or '', a.check_out or '', a.notes])

    elif section == 'callbacks':
        w.writerow(['Name','Phone','Email','Issue','Status','Assigned To',
                    'Created','Resolved'])
        for cb in CallbackRequest.objects.filter(created_at__date__gte=start).order_by('-created_at'):
            w.writerow([cb.name, cb.phone, cb.email, cb.issue_summary,
                        cb.get_status_display(),
                        cb.assigned_to.username if cb.assigned_to else '',
                        cb.created_at.strftime('%d %b %Y %H:%M'),
                        cb.resolved_at.strftime('%d %b %Y %H:%M') if cb.resolved_at else ''])

    return response


# ─────────────────────────────────────────────────────────────────────────────
# 12. EMPLOYEE LIST / DETAIL (existing, kept compatible)
# ─────────────────────────────────────────────────────────────────────────────

@_staff_required
def employee_list(request):
    # Employees only see other employees (staff) — not superusers/admins
    # Admins manage employee accounts from /admin-panel/employees/ only
    employees = User.objects.filter(
        is_staff=True, is_superuser=False
    ).order_by('first_name', 'username')
    return render(request, 'employee/team/employee_list.html', {'employees': employees})


@_staff_required
def employee_detail(request, pk):
    # Employees can only view other employees (non-superuser staff).
    # Superuser/admin profiles are managed from /admin-panel/ only.
    employee = get_object_or_404(User, pk=pk, is_staff=True, is_superuser=False)
    logs = EmployeeLoginLog.objects.filter(user=employee).order_by('-timestamp')[:50]
    total_logins  = EmployeeLoginLog.objects.filter(user=employee, event='login').count()
    total_logouts = EmployeeLoginLog.objects.filter(user=employee, event='logout').count()
    last_login_log= EmployeeLoginLog.objects.filter(user=employee, event='login').first()
    attendance    = EmployeeAttendance.objects.filter(employee=employee).order_by('-date')[:30]
    return render(request, 'employee/team/employee_detail.html', {
        'employee': employee, 'logs': logs,
        'total_logins': total_logins, 'total_logouts': total_logouts,
        'last_login_log': last_login_log,
        'attendance': attendance,
    })


@_staff_required
def my_profile(request):
    """Employee's own profile page — personal info, attendance, login history."""
    emp = request.user
    from apps.admin_panel.models import EmployeeProfile, Department

    try:
        profile = emp.emp_profile
    except Exception:
        profile = None

    attendance = EmployeeAttendance.objects.filter(employee=emp).order_by('-date')[:30]
    logs       = EmployeeLoginLog.objects.filter(user=emp, event='login').order_by('-timestamp')[:10]
    total_logins = EmployeeLoginLog.objects.filter(user=emp, event='login').count()

    today = date.today()
    month_start = today.replace(day=1)
    my_calls  = CallLog.objects.filter(employee=emp, called_at__date__gte=month_start).count()
    my_leads  = Lead.objects.filter(assigned_to=emp).count()
    my_tickets= SupportTicket.objects.filter(assigned_to=emp, status__in=['open','in_progress']).count()

    return render(request, 'employee/my_profile.html', {
        'emp': emp,
        'profile': profile,
        'attendance': attendance,
        'logs': logs,
        'total_logins': total_logins,
        'my_calls': my_calls,
        'my_leads': my_leads,
        'my_tickets': my_tickets,
        'today': today,
    })


# ─────────────────────────────────────────────────────────────────────────────
# 13. ATTENDANCE
# ─────────────────────────────────────────────────────────────────────────────

@_staff_required
def attendance_today(request):
    today = date.today()
    staff = User.objects.filter(Q(is_staff=True)|Q(is_superuser=True))
    records = {
        a.employee_id: a
        for a in EmployeeAttendance.objects.filter(date=today)
    }
    if request.method == 'POST':
        for user in staff:
            status = request.POST.get(f'status_{user.pk}', '')
            if status:
                EmployeeAttendance.objects.update_or_create(
                    employee=user, date=today,
                    defaults={
                        'status': status,
                        'marked_by': request.user,
                        'check_in': request.POST.get(f'checkin_{user.pk}') or None,
                        'check_out': request.POST.get(f'checkout_{user.pk}') or None,
                    }
                )
        messages.success(request, 'Attendance saved.')
        return redirect('employee:attendance_today')
    return render(request, 'employee/team/attendance.html', {
        'staff': staff, 'records': records, 'today': today,
        'status_choices': EmployeeAttendance.STATUS_CHOICES,
    })


# ─────────────────────────────────────────────────────────────────────────────
# 14. MEMBERSHIPS (kept for sidebar link)
# ─────────────────────────────────────────────────────────────────────────────

@_staff_required
def memberships_proxy(request):
    from apps.memberships.views import memberships_admin
    return memberships_admin(request)



# ─────────────────────────────────────────────────────────────────────────────
# 15. EMPLOYEE MENU PAGE
# ─────────────────────────────────────────────────────────────────────────────

@_staff_required
def menu(request):
    """
    Full employee navigation menu page — styled identical to the admin panel.
    Acts as a visual sitemap / quick-access hub for all employee sections.
    """
    today = date.today()
    return render(request, 'employee/menu.html', {
        'today': today,
        'pending_orders':   Order.objects.filter(
                                status__in=['pending', 'confirmed', 'packed']
                            ).count(),
        'open_tickets':     SupportTicket.objects.filter(
                                status__in=['open', 'in_progress']
                            ).count(),
        'pending_callbacks':CallbackRequest.objects.filter(status='pending').count(),
        'my_leads':         Lead.objects.filter(assigned_to=request.user).count(),
        'today_calls':      CallLog.objects.filter(called_at__date=today).count(),
    })
