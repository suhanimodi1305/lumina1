"""
Order models — Checkout, Payment, Tracking
Security hardening:
  - Tracking IDs now use secrets.token_urlsafe (cryptographically random)
  - Order IDs remain human-readable but are collision-resistant
"""
import uuid
import secrets
import string
from django.db import models
from django.contrib.auth.models import User
from apps.products.models import Product


def _gen_order_id():
    """Generate a Flipkart-style order ID like OD260621003621ABCD"""
    from django.utils import timezone
    now = timezone.now()
    # Use secrets for the suffix — not random.choices
    suffix = secrets.token_hex(3).upper()   # 6 uppercase hex chars
    return f"OD{now.strftime('%y%m%d%H%M%S')}{suffix}"


def _gen_tracking_id():
    """Cryptographically random 16-char tracking ID (URL-safe)."""
    return secrets.token_urlsafe(12)[:16].upper()


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending',    'Pending'),
        ('confirmed',  'Order Confirmed'),
        ('packed',     'Packed'),
        ('shipped',    'Shipped'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered',  'Delivered'),
        ('cancelled',  'Cancelled'),
        ('returned',   'Returned'),
    ]

    PAYMENT_CHOICES = [
        ('cod',        'Cash on Delivery'),
        ('upi',        'UPI'),
        ('card',       'Credit / Debit Card'),
        ('netbanking', 'Net Banking'),
        ('wallet',     'Wallet'),
    ]

    # Identity
    order_id    = models.CharField(max_length=30, unique=True, default=_gen_order_id)
    tracking_id = models.CharField(max_length=20, unique=True, default=_gen_tracking_id)
    user        = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='orders')

    # Customer info
    full_name   = models.CharField(max_length=150)
    phone       = models.CharField(max_length=15)
    email       = models.EmailField(blank=True)

    # Delivery address
    address_line1 = models.CharField(max_length=250)
    address_line2 = models.CharField(max_length=250, blank=True)
    city          = models.CharField(max_length=100)
    state         = models.CharField(max_length=100)
    pincode       = models.CharField(max_length=10)

    # Payment
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cod')
    payment_status = models.CharField(max_length=20, default='pending')  # pending/paid/failed

    # Order status
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='pending')

    # Financials
    subtotal         = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_charge  = models.DecimalField(max_digits=8,  decimal_places=2, default=0)
    discount         = models.DecimalField(max_digits=8,  decimal_places=2, default=0)
    total            = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Dates
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)
    estimated_delivery = models.DateField(null=True, blank=True)
    delivered_at     = models.DateTimeField(null=True, blank=True)

    # Notes
    order_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'

    def __str__(self):
        return f"{self.order_id} — {self.full_name}"

    def get_status_step(self):
        steps = ['pending', 'confirmed', 'packed', 'shipped', 'out_for_delivery', 'delivered']
        try:
            return steps.index(self.status)
        except ValueError:
            return 0

    @property
    def is_cod(self):
        return self.payment_method == 'cod'


class OrderItem(models.Model):
    order    = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product  = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    name     = models.CharField(max_length=200)   # snapshot at time of order
    brand    = models.CharField(max_length=100, blank=True)
    image_url = models.URLField(blank=True)
    sku      = models.CharField(max_length=50, blank=True)
    shade    = models.CharField(max_length=100, blank=True)
    price    = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = 'Order Item'

    def __str__(self):
        return f"{self.name} x{self.quantity}"

    @property
    def line_total(self):
        return self.price * self.quantity


class OrderStatusLog(models.Model):
    """Timeline events for tracking page"""
    order      = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_logs')
    status     = models.CharField(max_length=25)
    message    = models.CharField(max_length=300)
    location   = models.CharField(max_length=200, blank=True)
    timestamp  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.order.order_id} → {self.status}"


class UserRequirement(models.Model):
    """
    A custom product / service request submitted by a user.
    Employees see these and fulfil them; admin can manage all.
    """
    STATUS_CHOICES = [
        ('pending',     'Pending Review'),
        ('accepted',    'Accepted'),
        ('processing',  'Processing'),
        ('dispatched',  'Dispatched'),
        ('delivered',   'Delivered'),
        ('rejected',    'Rejected'),
        ('cancelled',   'Cancelled'),
    ]

    PRIORITY_CHOICES = [
        ('low',    'Low'),
        ('normal', 'Normal'),
        ('high',   'High'),
        ('urgent', 'Urgent'),
    ]

    # Identity
    req_id  = models.CharField(max_length=30, unique=True)
    user    = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requirements')

    # What user wants
    title           = models.CharField(max_length=200, help_text='Brief title of requirement')
    products        = models.ManyToManyField(Product, blank=True, related_name='requirements',
                                             help_text='Products user wants')
    custom_product  = models.TextField(blank=True,
                                       help_text='Describe product if not in catalog (brand, name, shade…)')
    requirement_notes = models.TextField(blank=True,
                                         help_text='Special instructions, skin concerns, any details')
    quantity        = models.PositiveIntegerField(default=1)
    priority        = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')

    # Delivery address
    full_name     = models.CharField(max_length=150)
    phone         = models.CharField(max_length=15)
    email         = models.EmailField(blank=True)
    address_line1 = models.CharField(max_length=250)
    address_line2 = models.CharField(max_length=250, blank=True)
    city          = models.CharField(max_length=100)
    state         = models.CharField(max_length=100)
    pincode       = models.CharField(max_length=10)

    # Status & assignment
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_to     = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='assigned_requirements',
                                        help_text='Employee handling this requirement')
    employee_notes  = models.TextField(blank=True, help_text='Internal notes by employee/admin')
    linked_order    = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='requirements',
                                        help_text='Order created to fulfil this requirement')

    # Timestamps
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'User Requirement'
        verbose_name_plural = 'User Requirements'

    def save(self, *args, **kwargs):
        if not self.req_id:
            import secrets
            from django.utils import timezone
            now = timezone.now()
            suffix = secrets.token_hex(3).upper()   # 6 uppercase hex chars
            self.req_id = f"REQ{now.strftime('%y%m%d%H%M%S')}{suffix}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.req_id} — {self.user.username}: {self.title}"

    @property
    def status_color(self):
        return {
            'pending':    'warning',
            'accepted':   'info',
            'processing': 'primary',
            'dispatched': 'secondary',
            'delivered':  'success',
            'rejected':   'danger',
            'cancelled':  'dark',
        }.get(self.status, 'secondary')
