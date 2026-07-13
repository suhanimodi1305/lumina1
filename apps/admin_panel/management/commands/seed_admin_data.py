"""
Management command to seed proper demo data for the admin panel:
  - Departments
  - Employee profiles (for existing staff users)
  - Sample orders with real products and customers
"""
import decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.admin_panel.models import EmployeeProfile, Department
from apps.orders.models import Order, OrderItem, OrderStatusLog
from apps.products.models import Product


DEPARTMENTS = [
    ('Sales & CRM', 'SALES'),
    ('Customer Support', 'CUST'),
    ('Marketing', 'MKT'),
    ('Operations', 'OPS'),
    ('HR & Admin', 'HR'),
]

EMPLOYEE_META = [
    ('Senior Sales Executive', 'SALES', 'morning',  '+91 9800000001', 'active'),
    ('Support Lead',           'CUST',  'morning',  '+91 9800000002', 'active'),
    ('Marketing Manager',      'MKT',   'flexible', '+91 9800000003', 'active'),
    ('Operations Head',        'OPS',   'morning',  '+91 9800000004', 'active'),
    ('Admin Supervisor',       'HR',    'flexible', '+91 9800000005', 'active'),
]

ORDER_SAMPLES = [
    {
        'full_name': 'Ananya Sharma',
        'phone': '+91 9876543210',
        'email': 'ananya.sharma@gmail.com',
        'address_line1': 'B-204, Green Valley Apartments',
        'address_line2': 'Near Central Park',
        'city': 'Mumbai',
        'state': 'Maharashtra',
        'pincode': '400001',
        'payment_method': 'upi',
        'payment_status': 'paid',
        'status': 'delivered',
        'note': 'Delivered on time',
        'product_count': 2,
    },
    {
        'full_name': 'Deepika Reddy',
        'phone': '+91 8765432109',
        'email': 'deepika.r@outlook.com',
        'address_line1': 'Flat 5A, Sunrise Towers, Koramangala',
        'address_line2': '',
        'city': 'Bangalore',
        'state': 'Karnataka',
        'pincode': '560034',
        'payment_method': 'card',
        'payment_status': 'paid',
        'status': 'shipped',
        'note': 'Dispatched via Blue Dart',
        'product_count': 1,
    },
    {
        'full_name': 'Meera Pillai',
        'phone': '+91 7654321098',
        'email': 'meera.pillai@yahoo.com',
        'address_line1': '12, MG Road, Sector 4',
        'address_line2': '',
        'city': 'Delhi',
        'state': 'Delhi',
        'pincode': '110001',
        'payment_method': 'cod',
        'payment_status': 'pending',
        'status': 'confirmed',
        'note': 'Order confirmed',
        'product_count': 3,
    },
    {
        'full_name': 'Kavya Nair',
        'phone': '+91 6543210987',
        'email': 'kavya.nair@gmail.com',
        'address_line1': '7/3, Lakeview Colony',
        'address_line2': 'Near Bus Stand',
        'city': 'Hyderabad',
        'state': 'Telangana',
        'pincode': '500001',
        'payment_method': 'netbanking',
        'payment_status': 'paid',
        'status': 'packed',
        'note': 'Packaging done',
        'product_count': 2,
    },
]


class Command(BaseCommand):
    help = 'Seeds admin panel demo data: departments, employee profiles, sample orders'

    def handle(self, *args, **options):
        self.stdout.write('Seeding demo data...')

        # ── Departments ────────────────────────────────────────────────
        depts = {}
        for name, code in DEPARTMENTS:
            d, created = Department.objects.get_or_create(
                name=name, defaults={'code': code}
            )
            depts[code] = d
            if created:
                self.stdout.write(f'  + Dept: {name}')
        self.stdout.write(f'  Departments: {len(depts)} ready')

        # ── Employee profiles ──────────────────────────────────────────
        staff_users = list(User.objects.filter(is_staff=True).order_by('id'))
        for i, emp in enumerate(staff_users):
            meta = EMPLOYEE_META[i % len(EMPLOYEE_META)]
            desig, dept_code, shift, phone, status = meta
            profile, created = EmployeeProfile.objects.get_or_create(user=emp)
            updated = False
            if not profile.designation:
                profile.designation = desig
                updated = True
            if not profile.department:
                profile.department = depts.get(dept_code)
                updated = True
            if not profile.phone:
                profile.phone = f'+91 9{800000001 + i}'
                updated = True
            if not profile.shift or profile.shift == 'morning':
                profile.shift = shift
                updated = True
            if updated:
                profile.save()
            self.stdout.write(
                f'  Employee: {emp.username} -> {profile.designation} ({profile.department})'
            )

        # ── Sample orders ──────────────────────────────────────────────
        products = list(Product.objects.all().order_by('?')[:30])
        customers = list(User.objects.filter(is_staff=False, is_superuser=False)[:8])

        if not products:
            self.stdout.write(self.style.WARNING('No products found — skipping orders'))
            return

        created_orders = 0
        for i, od in enumerate(ORDER_SAMPLES):
            # Try to link a real customer
            linked_user = customers[i % len(customers)] if customers else None

            # Pick products for this order
            start = (i * 3) % len(products)
            count = od['product_count']
            selected = []
            for j in range(count):
                selected.append(products[(start + j) % len(products)])

            subtotal = decimal.Decimal('0')
            items_to_create = []
            for idx, p in enumerate(selected):
                price = p.price if p.price else decimal.Decimal('599.00')
                qty = (idx % 2) + 1
                items_to_create.append({
                    'product': p,
                    'name': p.name,
                    'brand': p.brand,
                    'sku': p.sku,
                    'price': price,
                    'quantity': qty,
                })
                subtotal += price * qty

            delivery = decimal.Decimal('49.00') if subtotal < 999 else decimal.Decimal('0')
            discount = decimal.Decimal('50.00') if i % 2 == 0 else decimal.Decimal('0')
            total = subtotal + delivery - discount

            order = Order.objects.create(
                user=linked_user,
                full_name=od['full_name'],
                phone=od['phone'],
                email=od['email'],
                address_line1=od['address_line1'],
                address_line2=od['address_line2'],
                city=od['city'],
                state=od['state'],
                pincode=od['pincode'],
                payment_method=od['payment_method'],
                payment_status=od['payment_status'],
                status=od['status'],
                subtotal=subtotal,
                delivery_charge=delivery,
                discount=discount,
                total=total,
            )
            for idata in items_to_create:
                OrderItem.objects.create(order=order, **idata)

            OrderStatusLog.objects.create(
                order=order,
                status=od['status'],
                message=od['note'],
            )
            created_orders += 1
            self.stdout.write(
                f'  Order {order.order_id}: {od["full_name"]} | {od["status"]} | Rs.{total}'
            )

        self.stdout.write(self.style.SUCCESS(
            f'Done. {len(depts)} depts, {len(staff_users)} emp profiles, {created_orders} new orders.'
        ))
