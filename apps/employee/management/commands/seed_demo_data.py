"""
Management command: python manage.py seed_demo_data

Creates:
  - 3 employee (staff) users
  - 5 regular users
  - Sample login/logout logs for each
  - 2-4 orders per user with order items and status logs
"""
import random
from datetime import timedelta, date

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.employee.models import EmployeeLoginLog
from apps.orders.models import Order, OrderItem, OrderStatusLog
from apps.products.models import Product


# ── Sample data pools ─────────────────────────────────────────────────────────

EMPLOYEES = [
    dict(username='priya_emp',   first_name='Priya',   last_name='Sharma',   email='priya.sharma@lumina.in',   is_staff=True),
    dict(username='rahul_emp',   first_name='Rahul',   last_name='Verma',    email='rahul.verma@lumina.in',    is_staff=True),
    dict(username='sneha_emp',   first_name='Sneha',   last_name='Patel',    email='sneha.patel@lumina.in',    is_staff=True),
]

USERS = [
    dict(username='aanya_k',   first_name='Aanya',   last_name='Kapoor',  email='aanya.kapoor@gmail.com'),
    dict(username='meera_s',   first_name='Meera',   last_name='Singh',   email='meera.singh@gmail.com'),
    dict(username='divya_r',   first_name='Divya',   last_name='Rao',     email='divya.rao@gmail.com'),
    dict(username='kavya_m',   first_name='Kavya',   last_name='Mehta',   email='kavya.mehta@hotmail.com'),
    dict(username='riya_j',    first_name='Riya',    last_name='Joshi',   email='riya.joshi@yahoo.com'),
]

PRODUCT_SAMPLES = [
    dict(name='Laneige Water Sleeping Mask',        brand='Laneige',       category='mask',        product_range='korean',  sku='LAN-WSM-001', price=1850),
    dict(name='COSRX Snail Mucin Essence',          brand='COSRX',         category='essence',     product_range='korean',  sku='COS-SME-002', price=1299),
    dict(name='Some By Mi AHA BHA PHA Toner',       brand='Some By Mi',    category='toner',       product_range='korean',  sku='SBM-ABP-003', price=999),
    dict(name='Innisfree Green Tea Serum',          brand='Innisfree',     category='serum',       product_range='korean',  sku='INF-GTS-004', price=1150),
    dict(name='Maybelline Fit Me Foundation',       brand='Maybelline',    category='foundation',  product_range='makeup',  sku='MAY-FMF-005', price=549),
    dict(name='MAC Ruby Woo Lipstick',              brand='MAC',           category='lipstick',    product_range='makeup',  sku='MAC-RWL-006', price=1850),
    dict(name='Nykaa Matte to Last Kajal',          brand='Nykaa',         category='eyeliner',    product_range='makeup',  sku='NYK-MLK-007', price=249),
    dict(name='Biotique Bio Honey Gel Moisturizer', brand='Biotique',      category='moisturizer', product_range='korean',  sku='BIO-BHG-008', price=299),
]

ADDRESSES = [
    dict(address_line1='12 Rose Garden Apartments, MG Road', city='Bangalore',  state='Karnataka',      pincode='560001'),
    dict(address_line1='45 Andheri West, Near Station',      city='Mumbai',     state='Maharashtra',    pincode='400058'),
    dict(address_line1='7/B Civil Lines, Sector 4',          city='Delhi',      state='Delhi',          pincode='110001'),
    dict(address_line1='33 Salt Lake, Sector V',             city='Kolkata',    state='West Bengal',    pincode='700091'),
    dict(address_line1='Plot 8, Jubilee Hills, Road No. 36', city='Hyderabad',  state='Telangana',      pincode='500033'),
]

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) AppleWebKit/605.1.15 Mobile Safari/604.1',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36',
]

IPS = ['103.21.58.14', '49.36.112.201', '122.161.48.90', '182.74.133.22', '59.180.44.7']


class Command(BaseCommand):
    help = 'Seeds demo employees, users, login logs, and orders into the database'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\n── Lumina Demo Data Seeder ──\n'))

        products = self._ensure_products()
        employees = self._create_users(EMPLOYEES, is_staff=True, label='Employee')
        users     = self._create_users(USERS,     is_staff=False, label='User')

        all_people = employees + users
        self._create_login_logs(all_people)
        self._create_orders(users, products)

        self.stdout.write(self.style.SUCCESS('\n✓ Demo data seeded successfully!\n'))

    # ── helpers ───────────────────────────────────────────────────────────────

    def _ensure_products(self):
        """Create sample products if they don't exist yet."""
        created = 0
        products = []
        for p in PRODUCT_SAMPLES:
            obj, new = Product.objects.get_or_create(
                sku=p['sku'],
                defaults=dict(
                    name=p['name'], brand=p['brand'],
                    category=p['category'], product_range=p['product_range'],
                    price=p['price'], suitable_for_skin_types=['all'],
                    targets=[], shades_available=[],
                )
            )
            products.append(obj)
            if new:
                created += 1
        self.stdout.write(f'  Products : {created} created, {len(products)-created} already existed')
        return products

    def _create_users(self, data_list, is_staff, label):
        created = 0
        objects = []
        for d in data_list:
            user, new = User.objects.get_or_create(
                username=d['username'],
                defaults=dict(
                    first_name=d['first_name'],
                    last_name=d['last_name'],
                    email=d['email'],
                    is_staff=is_staff,
                    is_active=True,
                )
            )
            if new:
                user.set_password('Lumina@2024')
                user.save()
                created += 1
            objects.append(user)
        self.stdout.write(f'  {label}s  : {created} created, {len(objects)-created} already existed')
        return objects

    def _create_login_logs(self, users):
        """Generate realistic login/logout sequences for each user."""
        count = 0
        now = timezone.now()
        for user in users:
            if EmployeeLoginLog.objects.filter(user=user).exists():
                continue  # skip if already has logs
            # 3–6 login sessions going back up to 30 days
            num_sessions = random.randint(3, 6)
            for i in range(num_sessions):
                login_time  = now - timedelta(days=random.randint(0, 30),
                                              hours=random.randint(0, 23),
                                              minutes=random.randint(0, 59))
                logout_time = login_time + timedelta(minutes=random.randint(10, 120))
                ip = random.choice(IPS)
                ua = random.choice(USER_AGENTS)
                key = f'demo_{user.pk}_{i}'

                # Create then backdate using update() to bypass auto_now_add
                log_in = EmployeeLoginLog.objects.create(
                    user=user, event='login',
                    ip_address=ip, user_agent=ua, session_key=key,
                )
                EmployeeLoginLog.objects.filter(pk=log_in.pk).update(timestamp=login_time)

                log_out = EmployeeLoginLog.objects.create(
                    user=user, event='logout',
                    ip_address=ip, user_agent=ua, session_key=key,
                )
                EmployeeLoginLog.objects.filter(pk=log_out.pk).update(timestamp=logout_time)
                count += 2

        self.stdout.write(f'  Login logs: {count} events created')

    def _create_orders(self, users, products):
        """Create 2–4 orders per user with items and status logs."""
        count = 0
        statuses_pool = [
            'pending', 'confirmed', 'packed', 'shipped',
            'out_for_delivery', 'delivered', 'delivered', 'cancelled',
        ]
        payment_pool = ['cod', 'upi', 'card', 'upi', 'cod']

        for user in users:
            if Order.objects.filter(user=user).exists():
                self.stdout.write(f'    {user.username}: already has orders, skipping')
                continue

            addr = random.choice(ADDRESSES)
            num_orders = random.randint(2, 4)

            for _ in range(num_orders):
                status  = random.choice(statuses_pool)
                payment = random.choice(payment_pool)
                pay_status = 'paid' if payment != 'cod' else random.choice(['pending', 'paid'])

                order = Order.objects.create(
                    user          = user,
                    full_name     = f'{user.first_name} {user.last_name}'.strip(),
                    phone         = f'9{random.randint(100000000, 999999999)}',
                    email         = user.email,
                    address_line1 = addr['address_line1'],
                    city          = addr['city'],
                    state         = addr['state'],
                    pincode       = addr['pincode'],
                    payment_method  = payment,
                    payment_status  = pay_status,
                    status          = status,
                    delivery_charge = 0 if random.random() > 0.3 else 49,
                    discount        = random.choice([0, 0, 50, 100, 150]),
                    order_notes     = '',
                )

                # Add 1–3 items
                chosen = random.sample(products, k=random.randint(1, 3))
                subtotal = 0
                for prod in chosen:
                    qty = random.randint(1, 2)
                    price = prod.price or 499
                    OrderItem.objects.create(
                        order=order, product=prod,
                        name=prod.name, brand=prod.brand,
                        sku=prod.sku, price=price, quantity=qty,
                    )
                    subtotal += price * qty

                order.subtotal = subtotal
                order.total    = subtotal + order.delivery_charge - order.discount
                order.estimated_delivery = date.today() + timedelta(days=random.randint(2, 7))
                order.save()

                # Status timeline logs
                status_flow = {
                    'pending':          [('pending',   'Order placed successfully',    addr['city'])],
                    'confirmed':        [('pending',   'Order placed',                 addr['city']),
                                         ('confirmed', 'Payment confirmed',             addr['city'])],
                    'packed':           [('confirmed', 'Payment confirmed',             addr['city']),
                                         ('packed',    'Items packed and ready',        'Warehouse, Bangalore')],
                    'shipped':          [('confirmed', 'Payment confirmed',             addr['city']),
                                         ('packed',    'Packed at warehouse',           'Warehouse, Bangalore'),
                                         ('shipped',   'Picked up by courier',          'Mumbai Hub')],
                    'out_for_delivery': [('shipped',   'In transit',                   'Mumbai Hub'),
                                         ('out_for_delivery', 'Out for delivery today', addr['city'])],
                    'delivered':        [('confirmed', 'Payment confirmed',             addr['city']),
                                         ('shipped',   'Shipped via Delhivery',         'Mumbai Hub'),
                                         ('delivered', 'Delivered successfully',        addr['city'])],
                    'cancelled':        [('pending',   'Order placed',                 addr['city']),
                                         ('cancelled', 'Order cancelled by customer',   addr['city'])],
                }
                for s, msg, loc in status_flow.get(status, [('pending', 'Order placed', addr['city'])]):
                    OrderStatusLog.objects.create(order=order, status=s, message=msg, location=loc)

                count += 1

        self.stdout.write(f'  Orders    : {count} created with items and tracking logs')
