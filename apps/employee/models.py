"""
Employee CRM models — Unified Workspace
Covers: Login logs, Leads, Call logs, Support tickets,
        Campaigns, Internal notes, Attendance, Excel export logs
"""
import secrets
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# ─────────────────────────────────────────────────────────────────────────────
# EMPLOYEE LOGIN LOG (existing)
# ─────────────────────────────────────────────────────────────────────────────

class EmployeeLoginLog(models.Model):
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_logs')
    event       = models.CharField(max_length=10, choices=[('login', 'Login'), ('logout', 'Logout')])
    timestamp   = models.DateTimeField(auto_now_add=True)
    ip_address  = models.GenericIPAddressField(null=True, blank=True)
    user_agent  = models.TextField(blank=True, default='')
    session_key = models.CharField(max_length=64, blank=True, default='')

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Employee Login Log'
        verbose_name_plural = 'Employee Login Logs'

    def __str__(self):
        return f"{self.user.username} — {self.event} at {self.timestamp:%d %b %Y %H:%M}"


# ─────────────────────────────────────────────────────────────────────────────
# ATTENDANCE
# ─────────────────────────────────────────────────────────────────────────────

class EmployeeAttendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent',  'Absent'),
        ('half',    'Half Day'),
        ('leave',   'On Leave'),
        ('wfh',     'Work From Home'),
    ]
    employee    = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance_records')
    date        = models.DateField()
    status      = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    check_in    = models.TimeField(null=True, blank=True)
    check_out   = models.TimeField(null=True, blank=True)
    notes       = models.CharField(max_length=300, blank=True)
    marked_by   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='attendance_marked')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('employee', 'date')
        ordering = ['-date']
        verbose_name = 'Attendance Record'

    def __str__(self):
        return f"{self.employee.username} — {self.date} [{self.get_status_display()}]"


# ─────────────────────────────────────────────────────────────────────────────
# CRM LEAD
# ─────────────────────────────────────────────────────────────────────────────

class Lead(models.Model):
    STAGE_CHOICES = [
        ('new',            'New Lead'),
        ('contacted',      'Contacted'),
        ('interested',     'Interested'),
        ('product_shared', 'Product Shared'),
        ('demo_given',     'Demo Given'),
        ('negotiation',    'Negotiation'),
        ('opportunity',    'Opportunity'),
        ('quotation',      'Quotation'),
        ('payment_pending','Payment Pending'),
        ('order_confirmed','Order Confirmed'),
        ('delivered',      'Delivered'),
        ('review_received','Review Received'),
        ('repeat_customer','Repeat Customer'),
        ('lost',           'Lost'),
    ]

    SOURCE_CHOICES = [
        ('website',     'Website'),
        ('instagram',   'Instagram'),
        ('facebook',    'Facebook'),
        ('whatsapp',    'WhatsApp'),
        ('referral',    'Referral'),
        ('campaign',    'Campaign'),
        ('cold_call',   'Cold Call'),
        ('walk_in',     'Walk-in'),
        ('other',       'Other'),
    ]

    lead_id     = models.CharField(max_length=20, unique=True, editable=False)
    name        = models.CharField(max_length=150)
    phone       = models.CharField(max_length=15)
    email       = models.EmailField(blank=True)
    city        = models.CharField(max_length=80, blank=True)
    source      = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='website')
    stage       = models.CharField(max_length=20, choices=STAGE_CHOICES, default='new')
    skin_concern = models.CharField(max_length=200, blank=True)
    budget      = models.CharField(max_length=100, blank=True)
    notes       = models.TextField(blank=True)

    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='assigned_leads')
    created_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='created_leads')
    linked_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='crm_leads',
                                    help_text='Lumina account if lead signed up')

    follow_up_date = models.DateField(null=True, blank=True)
    is_converted   = models.BooleanField(default=False)
    converted_at   = models.DateTimeField(null=True, blank=True)

    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'CRM Lead'

    def save(self, *args, **kwargs):
        if not self.lead_id:
            now = timezone.now()
            suffix = secrets.token_hex(2).upper()
            self.lead_id = f"LD{now.strftime('%y%m%d%H%M')}{suffix}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.lead_id} — {self.name} [{self.get_stage_display()}]"


# ─────────────────────────────────────────────────────────────────────────────
# OPPORTUNITY
# ─────────────────────────────────────────────────────────────────────────────

class Opportunity(models.Model):
    STAGE_CHOICES = [
        ('qualified',           'Qualified'),
        ('product_recommended', 'Product Recommended'),
        ('budget_confirmed',    'Budget Confirmed'),
        ('decision_maker',      'Decision Maker Reached'),
        ('proposal',            'Proposal Sent'),
        ('negotiation',         'Negotiation'),
        ('won',                 'Won'),
        ('lost',                'Lost'),
    ]

    opp_id      = models.CharField(max_length=20, unique=True, editable=False)
    lead        = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='opportunities')
    customer    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='opportunities')
    title       = models.CharField(max_length=200)
    stage       = models.CharField(max_length=30, choices=STAGE_CHOICES, default='qualified')
    value       = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    probability = models.PositiveSmallIntegerField(default=50, help_text='Win probability 0-100%')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='assigned_opportunities')
    close_date  = models.DateField(null=True, blank=True)
    notes       = models.TextField(blank=True)
    products    = models.ManyToManyField('products.Product', blank=True)

    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Opportunity'
        verbose_name_plural = 'Opportunities'

    def save(self, *args, **kwargs):
        if not self.opp_id:
            now = timezone.now()
            suffix = secrets.token_hex(2).upper()
            self.opp_id = f"OPP{now.strftime('%y%m%d%H%M')}{suffix}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.opp_id} — {self.title} [{self.get_stage_display()}]"


# ─────────────────────────────────────────────────────────────────────────────
# CALL LOG
# ─────────────────────────────────────────────────────────────────────────────

class CallLog(models.Model):
    DIRECTION_CHOICES = [
        ('inbound',  'Inbound'),
        ('outbound', 'Outbound'),
        ('followup', 'Follow-up'),
    ]

    CALL_STATUS_CHOICES = [
        ('connected',           'Connected'),
        ('no_answer',           'No Answer'),
        ('busy',                'Busy'),
        ('callback_requested',  'Callback Requested'),
        ('interested',          'Interested'),
        ('not_interested',      'Not Interested'),
        ('wrong_number',        'Wrong Number'),
        ('converted',           'Converted'),
        ('escalated',           'Escalated'),
    ]

    call_id         = models.CharField(max_length=20, unique=True, editable=False)
    employee        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='call_logs')
    lead            = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='call_logs')
    customer        = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='received_calls')
    customer_name   = models.CharField(max_length=150, blank=True)
    phone           = models.CharField(max_length=15)
    direction       = models.CharField(max_length=10, choices=DIRECTION_CHOICES, default='outbound')
    status          = models.CharField(max_length=25, choices=CALL_STATUS_CHOICES, default='connected')
    duration_seconds= models.PositiveIntegerField(default=0)
    notes           = models.TextField(blank=True)
    call_script     = models.TextField(blank=True)
    follow_up_date  = models.DateField(null=True, blank=True)
    follow_up_time  = models.TimeField(null=True, blank=True)

    # When customer clicks "Help" / "Call Back" from site
    is_customer_initiated = models.BooleanField(default=False)
    is_resolved     = models.BooleanField(default=False)
    resolved_at     = models.DateTimeField(null=True, blank=True)
    resolved_by     = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='resolved_calls')

    called_at       = models.DateTimeField(default=timezone.now)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-called_at']
        verbose_name = 'Call Log'

    def save(self, *args, **kwargs):
        if not self.call_id:
            now = timezone.now()
            suffix = secrets.token_hex(2).upper()
            self.call_id = f"CL{now.strftime('%y%m%d%H%M%S')}{suffix}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.call_id} — {self.phone} [{self.get_status_display()}]"

    @property
    def duration_display(self):
        m, s = divmod(self.duration_seconds, 60)
        return f"{m}m {s}s" if m else f"{s}s"


# ─────────────────────────────────────────────────────────────────────────────
# SUPPORT TICKET
# ─────────────────────────────────────────────────────────────────────────────

class SupportTicket(models.Model):
    PRIORITY_CHOICES = [
        ('low',      'Low'),
        ('medium',   'Medium'),
        ('high',     'High'),
        ('critical', 'Critical'),
    ]

    STATUS_CHOICES = [
        ('open',        'Open'),
        ('in_progress', 'In Progress'),
        ('waiting',     'Waiting on Customer'),
        ('resolved',    'Resolved'),
        ('closed',      'Closed'),
    ]

    CHANNEL_CHOICES = [
        ('chat',      'Live Chat'),
        ('whatsapp',  'WhatsApp'),
        ('email',     'Email'),
        ('phone',     'Phone'),
        ('portal',    'Customer Portal'),
    ]

    ticket_id   = models.CharField(max_length=20, unique=True, editable=False)
    customer    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='support_tickets')
    customer_name = models.CharField(max_length=150)
    customer_email= models.EmailField(blank=True)
    customer_phone= models.CharField(max_length=15, blank=True)

    subject     = models.CharField(max_length=300)
    description = models.TextField()
    channel     = models.CharField(max_length=10, choices=CHANNEL_CHOICES, default='chat')
    priority    = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status      = models.CharField(max_length=15, choices=STATUS_CHOICES, default='open')

    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='assigned_tickets')
    resolution  = models.TextField(blank=True)
    rating      = models.PositiveSmallIntegerField(null=True, blank=True,
                                                   help_text='Customer rating 1-5')
    linked_order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL,
                                     null=True, blank=True, related_name='support_tickets')

    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Support Ticket'

    def save(self, *args, **kwargs):
        if not self.ticket_id:
            now = timezone.now()
            suffix = secrets.token_hex(2).upper()
            self.ticket_id = f"TK{now.strftime('%y%m%d%H%M%S')}{suffix}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ticket_id} — {self.subject[:60]}"


class TicketReply(models.Model):
    ticket      = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='replies')
    author      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    message     = models.TextField()
    is_internal = models.BooleanField(default=False, help_text='Internal team note, not visible to customer')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Reply on {self.ticket.ticket_id} by {self.author}"


# ─────────────────────────────────────────────────────────────────────────────
# MARKETING CAMPAIGN
# ─────────────────────────────────────────────────────────────────────────────

class Campaign(models.Model):
    TYPE_CHOICES = [
        ('email',     'Email Campaign'),
        ('sms',       'SMS Campaign'),
        ('push',      'Push Notification'),
        ('whatsapp',  'WhatsApp Blast'),
        ('influencer','Influencer'),
        ('referral',  'Referral'),
        ('coupon',    'Coupon'),
    ]

    STATUS_CHOICES = [
        ('draft',     'Draft'),
        ('scheduled', 'Scheduled'),
        ('active',    'Active'),
        ('completed', 'Completed'),
        ('paused',    'Paused'),
    ]

    camp_id     = models.CharField(max_length=20, unique=True, editable=False)
    name        = models.CharField(max_length=200)
    type        = models.CharField(max_length=15, choices=TYPE_CHOICES, default='email')
    status      = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')
    description = models.TextField(blank=True)
    target_audience = models.CharField(max_length=200, blank=True)
    budget      = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    spent       = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    scheduled_at = models.DateTimeField(null=True, blank=True)
    started_at   = models.DateTimeField(null=True, blank=True)
    ended_at     = models.DateTimeField(null=True, blank=True)

    leads_generated = models.PositiveIntegerField(default=0)
    conversions     = models.PositiveIntegerField(default=0)
    revenue         = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='created_campaigns')
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Campaign'

    def save(self, *args, **kwargs):
        if not self.camp_id:
            now = timezone.now()
            suffix = secrets.token_hex(2).upper()
            self.camp_id = f"CP{now.strftime('%y%m%d%H%M')}{suffix}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.camp_id} — {self.name}"

    @property
    def roi(self):
        if self.spent and self.spent > 0:
            return round(((self.revenue - self.spent) / self.spent) * 100, 1)
        return 0


# ─────────────────────────────────────────────────────────────────────────────
# INTERNAL TEAM NOTE
# ─────────────────────────────────────────────────────────────────────────────

class InternalNote(models.Model):
    TAG_CHOICES = [
        ('general',   'General'),
        ('lead',      'Lead Update'),
        ('order',     'Order'),
        ('payment',   'Payment'),
        ('refund',    'Refund'),
        ('callback',  'Callback'),
        ('shipping',  'Shipping'),
        ('follow_up', 'Follow-up'),
    ]

    author      = models.ForeignKey(User, on_delete=models.CASCADE, related_name='internal_notes')
    content     = models.TextField()
    tag         = models.CharField(max_length=15, choices=TAG_CHOICES, default='general')

    # Optional links
    lead        = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='internal_notes')
    customer    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='emp_notes')
    ticket      = models.ForeignKey(SupportTicket, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='internal_notes')
    order_ref   = models.CharField(max_length=30, blank=True)

    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Internal Note'

    def __str__(self):
        return f"{self.author.username}: {self.content[:60]}"


# ─────────────────────────────────────────────────────────────────────────────
# CALLBACK REQUEST (customer-initiated from "Help" / calling option)
# ─────────────────────────────────────────────────────────────────────────────

class CallbackRequest(models.Model):
    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('assigned',  'Assigned'),
        ('called',    'Called'),
        ('resolved',  'Resolved'),
        ('missed',    'Missed'),
    ]

    customer        = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='callback_requests')
    name            = models.CharField(max_length=150)
    phone           = models.CharField(max_length=15)
    email           = models.EmailField(blank=True)
    issue_summary   = models.CharField(max_length=500)
    preferred_time  = models.CharField(max_length=100, blank=True)

    status          = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    assigned_to     = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='callback_assignments')
    employee_notes  = models.TextField(blank=True)
    is_resolved     = models.BooleanField(default=False)
    resolved_at     = models.DateTimeField(null=True, blank=True)

    # Linked call log after employee calls back
    call_log        = models.ForeignKey(CallLog, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='callback_request')

    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Callback Request'

    def __str__(self):
        return f"Callback: {self.name} ({self.phone}) [{self.get_status_display()}]"


# ─────────────────────────────────────────────────────────────────────────────
# DAILY SALES TARGET
# ─────────────────────────────────────────────────────────────────────────────

class SalesTarget(models.Model):
    employee    = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sales_targets')
    date        = models.DateField()
    target      = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    achieved    = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes       = models.CharField(max_length=300, blank=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('employee', 'date')
        ordering = ['-date']
        verbose_name = 'Sales Target'

    def __str__(self):
        return f"{self.employee.username} — {self.date}: ₹{self.achieved}/₹{self.target}"

    @property
    def pct(self):
        if self.target and self.target > 0:
            return min(int((self.achieved / self.target) * 100), 100)
        return 0
