"""
Management command: python manage.py add_sample_data

Adds comprehensive sample data including:
  - Specific users: suhani (employee), janvi_u (employee), priya_emp (employee)
  - 5 customers with full profiles
  - 4-5 entries across ALL models (products, orders, scans, reviews, etc.)
  - Complete data for understanding the system in Django admin

Password for all test users: Lumina@2025
"""
import random
from datetime import timedelta, date, time as dtime
from decimal import Decimal
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Add comprehensive sample data with specific users and 4-5 entries per model'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\n== Adding Sample Data ==\n'))

        self.stdout.write(self.style.HTTP_INFO('-- Step 1: Core reference data --'))
        products  = self._create_products()
        self._create_coupons()
        self._create_quick_prompts()
        self._create_company_settings()

        self.stdout.write(self.style.HTTP_INFO('-- Step 2: Users --'))
        admin     = self._create_superuser()
        employees = self._create_employees()
        customers = self._create_customers()

        self.stdout.write(self.style.HTTP_INFO('-- Step 3: Employee / HR data --'))
        self._create_salary_and_leaves(employees, admin)
        self._create_attendance(employees, admin)
        self._create_sales_targets(employees)
        self._create_admin_tasks(admin, employees)
        self._create_admin_activity(admin)

        self.stdout.write(self.style.HTTP_INFO('-- Step 4: Customer data --'))
        self._create_orders(customers, products)
        self._create_scans(customers)
        self._create_diagnostic(customers)
        self._create_progress(customers)
        self._create_notifications(customers)
        self._create_reviews(customers, products)

        self.stdout.write(self.style.HTTP_INFO('-- Step 5: CRM & support --'))
        self._create_crm_leads(employees)
        self._create_support_tickets(customers, employees)
        self._create_campaigns(employees)

        self.stdout.write(self.style.HTTP_INFO('-- Step 6: Blog --'))
        self._create_blog(admin)

        self.stdout.write(self.style.SUCCESS('\n[OK] All sample data added successfully!\n'))
        self.stdout.write('  +---------------------------------------------+')
        self.stdout.write('  |         LOGIN CREDENTIALS                   |')
        self.stdout.write('  |  Password for ALL users: Lumina@2025        |')
        self.stdout.write('  +---------------------------------------------+')
        self.stdout.write('  |  SUPERADMIN  : suhani                       |')
        self.stdout.write('  +---------------------------------------------+')
        self.stdout.write('  |  EMPLOYEES   : janvi_u                      |')
        self.stdout.write('  |               priya_emp                     |')
        self.stdout.write('  |               rahul_emp                     |')
        self.stdout.write('  |               sneha_emp                     |')
        self.stdout.write('  +---------------------------------------------+')
        self.stdout.write('  |  CUSTOMERS   : aanya_k   (VIP)              |')
        self.stdout.write('  |               meera_s   (Medium)            |')
        self.stdout.write('  |               divya_r   (Normal)            |')
        self.stdout.write('  |               kavya_m   (Normal)            |')
        self.stdout.write('  |               riya_j    (Medium)            |')
        self.stdout.write('  +---------------------------------------------+')

    def _create_superuser(self):
        """Create suhani as superuser (admin)"""
        user, created = User.objects.get_or_create(
            username='suhani',
            defaults={
                'email': 'suhanimodi7090@gmail.com',
                'first_name': 'Suhani',
                'last_name': 'Modi',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        user.set_password('Lumina@2025')
        user.save()
        self.stdout.write(f'  Superuser suhani: {"created" if created else "updated password"}')
        return user

    def _create_employees(self):
        """Create janvi_u, priya_emp, and a third employee"""
        from apps.admin_panel.models import EmployeeProfile, Department
        from apps.memberships.models import UserProfile

        # Ensure departments exist
        dept_cc, _ = Department.objects.get_or_create(
            name='Customer Care',
            defaults={'code': 'CC', 'description': 'Customer support and satisfaction'}
        )
        dept_sales, _ = Department.objects.get_or_create(
            name='Sales',
            defaults={'code': 'SLS', 'description': 'Sales and revenue generation'}
        )
        dept_mkt, _ = Department.objects.get_or_create(
            name='Marketing',
            defaults={'code': 'MKT', 'description': 'Marketing and brand campaigns'}
        )

        emp_data = [
            {
                'username': 'janvi_u', 'first_name': 'Janvi', 'last_name': 'Upadhyay',
                'email': 'janvi@lumina.in', 'password': 'Lumina@2025',
                'designation': 'Skin Care Specialist', 'department': dept_cc,
                'phone': '9876543211', 'city': 'Ahmedabad',
                'joining_date': date(2023, 3, 10), 'experience_years': 3,
            },
            {
                'username': 'priya_emp', 'first_name': 'Priya', 'last_name': 'Sharma',
                'email': 'priya@lumina.in', 'password': 'Lumina@2025',
                'designation': 'Skin Consultant', 'department': dept_cc,
                'phone': '9876543210', 'city': 'Mumbai',
                'joining_date': date(2023, 1, 15), 'experience_years': 4,
            },
            {
                'username': 'rahul_emp', 'first_name': 'Rahul', 'last_name': 'Verma',
                'email': 'rahul@lumina.in', 'password': 'Lumina@2025',
                'designation': 'Sales Executive', 'department': dept_sales,
                'phone': '9123456780', 'city': 'Delhi',
                'joining_date': date(2022, 6, 1), 'experience_years': 5,
            },
            {
                'username': 'sneha_emp', 'first_name': 'Sneha', 'last_name': 'Patel',
                'email': 'sneha@lumina.in', 'password': 'Lumina@2025',
                'designation': 'Marketing Manager', 'department': dept_mkt,
                'phone': '9988776655', 'city': 'Bangalore',
                'joining_date': date(2021, 9, 20), 'experience_years': 6,
            },
        ]

        objs = []
        for e in emp_data:
            user, created = User.objects.get_or_create(
                username=e['username'],
                defaults={
                    'first_name': e['first_name'], 'last_name': e['last_name'],
                    'email': e['email'], 'is_staff': True, 'is_active': True,
                }
            )
            user.set_password(e['password'])
            user.save()

            UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'tier': 'normal', 'staff_role': 'admin',
                    'onboarding_complete': True,
                }
            )

            EmployeeProfile.objects.get_or_create(
                user=user,
                defaults={
                    'department': e['department'],
                    'designation': e['designation'],
                    'joining_date': e['joining_date'],
                    'status': 'active',
                    'phone': e['phone'],
                    'city': e['city'],
                    'country': 'India',
                    'shift': 'morning',
                    'experience_years': e['experience_years'],
                    'qualification': 'B.Sc Cosmetology',
                    'skills': 'Skin Analysis, Customer Service, Product Knowledge',
                    'languages': 'Hindi, English, Gujarati',
                }
            )

            action = 'created' if created else 'updated'
            self.stdout.write(f'  Employee {e["username"]}: {action}')
            objs.append(user)

        return objs

    def _create_customers(self):
        """Create 5 customer users with complete profiles"""
        from apps.memberships.models import UserProfile
        from apps.accounts.models import SavedAddress

        cust_data = [
            {
                'username': 'aanya_k', 'first_name': 'Aanya', 'last_name': 'Kapoor',
                'email': 'aanya@gmail.com', 'password': 'Lumina@2025',
                'tier': 'vip', 'loyalty_points': 1800, 'city': 'Mumbai', 'phone': '9870001111',
                'address': '12 Rose Garden Apts, MG Road', 'state': 'Maharashtra', 'pincode': '400001',
            },
            {
                'username': 'meera_s', 'first_name': 'Meera', 'last_name': 'Singh',
                'email': 'meera@gmail.com', 'password': 'Lumina@2025',
                'tier': 'medium', 'loyalty_points': 650, 'city': 'Delhi', 'phone': '9870002222',
                'address': '45 Andheri West, Near Station', 'state': 'Delhi', 'pincode': '110001',
            },
            {
                'username': 'divya_r', 'first_name': 'Divya', 'last_name': 'Rao',
                'email': 'divya@gmail.com', 'password': 'Lumina@2025',
                'tier': 'normal', 'loyalty_points': 200, 'city': 'Hyderabad', 'phone': '9870003333',
                'address': '33 Salt Lake, Sector V', 'state': 'Telangana', 'pincode': '500033',
            },
            {
                'username': 'kavya_m', 'first_name': 'Kavya', 'last_name': 'Mehta',
                'email': 'kavya@gmail.com', 'password': 'Lumina@2025',
                'tier': 'normal', 'loyalty_points': 120, 'city': 'Bangalore', 'phone': '9870004444',
                'address': 'Plot 8, Jubilee Hills', 'state': 'Karnataka', 'pincode': '560001',
            },
            {
                'username': 'riya_j', 'first_name': 'Riya', 'last_name': 'Joshi',
                'email': 'riya@gmail.com', 'password': 'Lumina@2025',
                'tier': 'medium', 'loyalty_points': 500, 'city': 'Pune', 'phone': '9870005555',
                'address': '7 Koregaon Park Lane', 'state': 'Maharashtra', 'pincode': '411001',
            },
        ]

        objs = []
        for c in cust_data:
            user, created = User.objects.get_or_create(
                username=c['username'],
                defaults={
                    'first_name': c['first_name'], 'last_name': c['last_name'],
                    'email': c['email'], 'is_active': True,
                }
            )
            user.set_password(c['password'])
            user.save()

            UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'tier': c['tier'],
                    'loyalty_points': c['loyalty_points'],
                    'onboarding_complete': True,
                    'onboarding_step': 'done',
                }
            )

            SavedAddress.objects.get_or_create(
                user=user, label='home',
                defaults={
                    'full_name': f"{c['first_name']} {c['last_name']}",
                    'phone': c['phone'],
                    'address_line1': c['address'],
                    'city': c['city'],
                    'state': c['state'],
                    'pincode': c['pincode'],
                    'is_default': True,
                }
            )

            action = 'created' if created else 'updated'
            self.stdout.write(f'  Customer {c["username"]} [{c["tier"].upper()}]: {action}')
            objs.append((user, c))

        return objs

    def _create_products(self):
        """Create reference products and auto-load all Indian makeup & skincare fixtures"""
        from apps.products.models import Product, SkinConcern
        from django.core.management import call_command

        concerns_data = [
            {'name': 'Acne',         'slug': 'acne',         'icon': '🔴', 'description': 'Pimples and breakouts'},
            {'name': 'Pigmentation', 'slug': 'pigmentation', 'icon': '🟤', 'description': 'Dark spots and uneven tone'},
            {'name': 'Dryness',      'slug': 'dryness',      'icon': '💧', 'description': 'Dehydration and flaking'},
            {'name': 'Aging',        'slug': 'aging',        'icon': '⏳', 'description': 'Fine lines and wrinkles'},
            {'name': 'Dullness',     'slug': 'dullness',     'icon': '⭐', 'description': 'Lack of radiance'},
        ]
        for c in concerns_data:
            SkinConcern.objects.get_or_create(slug=c['slug'], defaults=c)

        # Load fixture data for Indian Makeup (MARS, Nykaa, Maybelline, MAC), Ayurvedic, & K-beauty
        fixtures = [
            'mars_makeup_products',
            'maybelline_mac_nykaa_products',
            'sp_ayurved_products',
            'sas_korean_products',
            'korean_products',
            'makeup_products',
            'skin_concerns',
        ]
        for fx in fixtures:
            try:
                call_command('loaddata', fx, verbosity=0)
                self.stdout.write(f'  Loaded fixture: {fx}')
            except Exception as fe:
                self.stdout.write(f'  Fixture {fx} note: {fe}')

        products_data = [
            {
                'name': 'Laneige Water Sleeping Mask', 'brand': 'Laneige',
                'category': 'mask', 'product_range': 'korean', 'sku': 'LAN-WSM-001',
                'price': Decimal('1850'),
                'description': 'Overnight hydration mask with mineral water and beta-glucan.',
                'key_ingredients': 'Mineral Water, Beta-Glucan, Evening Primrose Extract',
                'suitable_for_skin_types': ['dry', 'combination', 'normal'],
                'is_featured': True,
            },
            {
                'name': 'COSRX Snail Mucin Essence', 'brand': 'COSRX',
                'category': 'essence', 'product_range': 'korean', 'sku': 'COS-SME-002',
                'price': Decimal('1299'),
                'description': '96% snail secretion filtrate for repair and hydration.',
                'key_ingredients': 'Snail Secretion Filtrate, Panthenol, Sodium Hyaluronate',
                'suitable_for_skin_types': ['all'],
                'is_featured': True,
            },
            {
                'name': 'Some By Mi AHA BHA PHA Toner', 'brand': 'Some By Mi',
                'category': 'toner', 'product_range': 'korean', 'sku': 'SBM-ABP-003',
                'price': Decimal('999'),
                'description': 'Exfoliating toner with triple acids to unclog pores.',
                'key_ingredients': 'AHA, BHA, PHA, Tea Tree, Niacinamide',
                'suitable_for_skin_types': ['oily', 'combination'],
                'is_featured': False,
            },
            {
                'name': 'Maybelline Fit Me Foundation', 'brand': 'Maybelline',
                'category': 'foundation', 'product_range': 'makeup', 'sku': 'MAY-FMF-005',
                'price': Decimal('549'),
                'description': 'Natural finish foundation with SPF 18 for all skin types.',
                'key_ingredients': 'SPF 18, Poreless Formula, Natural Pigments',
                'suitable_for_skin_types': ['all'],
                'is_featured': False,
            },
            {
                'name': 'Biotique Neem Face Wash', 'brand': 'Biotique',
                'category': 'cleanser', 'product_range': 'ayurvedic', 'sku': 'BIO-NNF-007',
                'price': Decimal('199'),
                'description': 'Ayurvedic neem face wash for oily and acne-prone skin.',
                'key_ingredients': 'Neem Extract, Tulsi, Turmeric',
                'suitable_for_skin_types': ['oily', 'combination'],
                'is_featured': False,
            },
        ]

        objs = []
        for p in products_data:
            obj, created = Product.objects.get_or_create(
                sku=p['sku'],
                defaults={
                    'name': p['name'], 'brand': p['brand'],
                    'category': p['category'], 'product_range': p['product_range'],
                    'price': p['price'], 'description': p['description'],
                    'key_ingredients': p['key_ingredients'],
                    'suitable_for_skin_types': p['suitable_for_skin_types'],
                    'targets': [], 'shades_available': [],
                    'is_featured': p.get('is_featured', False),
                }
            )
            objs.append(obj)
        return objs

    def _create_orders(self, customers, products):
        """Create 4-5 orders per customer with items and status logs"""
        from apps.orders.models import Order, OrderItem, OrderStatusLog

        statuses = ['delivered', 'delivered', 'shipped', 'confirmed', 'cancelled']
        payments = ['upi', 'card', 'cod', 'upi', 'netbanking']
        count = 0

        for (user, c) in customers:
            if Order.objects.filter(user=user).count() >= 3:
                continue
            for i in range(4):
                status  = statuses[i % len(statuses)]
                payment = payments[i % len(payments)]
                order = Order.objects.create(
                    user=user,
                    full_name=f'{user.first_name} {user.last_name}',
                    phone=c['phone'],
                    email=user.email,
                    address_line1=c['address'],
                    city=c['city'], state=c['state'], pincode=c['pincode'],
                    payment_method=payment,
                    payment_status='paid' if payment != 'cod' else 'pending',
                    status=status,
                    delivery_charge=Decimal('0') if i % 2 == 0 else Decimal('49'),
                    discount=Decimal(str([0, 50, 100, 0][i % 4])),
                    estimated_delivery=date.today() + timedelta(days=random.randint(2, 7)),
                )
                chosen = random.sample(products, k=min(random.randint(1, 3), len(products)))
                subtotal = Decimal('0')
                for prod in chosen:
                    qty = random.randint(1, 2)
                    price = prod.price or Decimal('499')
                    OrderItem.objects.create(
                        order=order, product=prod,
                        name=prod.name, brand=prod.brand,
                        sku=prod.sku, price=price, quantity=qty,
                    )
                    subtotal += price * qty
                order.subtotal = subtotal
                order.total = subtotal + order.delivery_charge - order.discount
                order.save()

                flow = {
                    'delivered': [
                        ('confirmed', 'Payment confirmed', c['city']),
                        ('shipped',   'Shipped via Delhivery', 'Mumbai Hub'),
                        ('delivered', 'Package delivered', c['city']),
                    ],
                    'shipped': [
                        ('confirmed', 'Payment confirmed', c['city']),
                        ('shipped',   'In transit', 'Mumbai Hub'),
                    ],
                    'confirmed': [('confirmed', 'Order placed and confirmed', c['city'])],
                    'cancelled': [
                        ('pending',   'Order placed', c['city']),
                        ('cancelled', 'Cancelled by customer', c['city']),
                    ],
                }
                for s, msg, loc in flow.get(status, [('pending', 'Order placed', c['city'])]):
                    OrderStatusLog.objects.create(order=order, status=s, message=msg, location=loc)
                count += 1

        self.stdout.write(f'  Orders: {count} created')

    def _create_blog(self, admin_user):
        """Create 4 blog categories and 5 blog posts"""
        from apps.blog.models import BlogCategory, BlogPost

        cats_data = [
            {'name': 'Skincare Tips',      'slug': 'skincare-tips',      'icon': '✨', 'order': 1},
            {'name': 'K-Beauty',           'slug': 'k-beauty',           'icon': '🇰🇷', 'order': 2},
            {'name': 'Makeup Tutorials',   'slug': 'makeup-tutorials',   'icon': '💄', 'order': 3},
            {'name': 'Ingredients Guide',  'slug': 'ingredients-guide',  'icon': '🧪', 'order': 4},
        ]
        cats = {}
        for c in cats_data:
            obj, _ = BlogCategory.objects.get_or_create(slug=c['slug'], defaults=c)
            cats[c['slug']] = obj

        posts_data = [
            {
                'title': 'The Ultimate Guide to Korean Skincare Routine',
                'slug': 'ultimate-guide-korean-skincare-routine',
                'cat': 'k-beauty', 'status': 'published', 'is_featured': True, 'reading_time': 7,
                'excerpt': 'Learn the famous 10-step K-beauty routine adapted for Indian skin.',
                'content': '<h2>What is K-Beauty?</h2><p>Korean skincare focuses on layering lightweight products for deep hydration and a glass-skin effect.</p><h2>The 10-Step Routine</h2><ol><li>Oil Cleanser</li><li>Water-Based Cleanser</li><li>Exfoliator</li><li>Toner</li><li>Essence</li><li>Serums/Ampoules</li><li>Sheet Mask</li><li>Eye Cream</li><li>Moisturizer</li><li>SPF</li></ol>',
            },
            {
                'title': 'Niacinamide vs Vitamin C: Which One Should You Use?',
                'slug': 'niacinamide-vs-vitamin-c',
                'cat': 'ingredients-guide', 'status': 'published', 'is_featured': False, 'reading_time': 5,
                'excerpt': 'Two of the most popular brightening ingredients explained.',
                'content': '<h2>Niacinamide (Vitamin B3)</h2><p>Niacinamide reduces pore size, controls sebum, brightens dark spots, and strengthens the skin barrier. Gentle enough for daily use on all skin types.</p><h2>Vitamin C</h2><p>A powerful antioxidant that neutralizes free radicals, boosts collagen, and fades hyperpigmentation. Use in the morning under SPF.</p>',
            },
            {
                'title': 'Skincare Routine for Acne-Prone Skin in Indian Climate',
                'slug': 'skincare-routine-acne-prone-indian-climate',
                'cat': 'skincare-tips', 'status': 'published', 'is_featured': True, 'reading_time': 6,
                'excerpt': 'Beat humidity and breakouts with this routine for Indian skin.',
                'content': '<h2>Why Indian Climate Makes Acne Worse</h2><p>High humidity increases sebum production. Combined with pollution and heat, this clogs pores.</p><h2>Morning Routine</h2><ul><li>Gel cleanser</li><li>Niacinamide 10% serum</li><li>Oil-free moisturizer</li><li>Mineral SPF 50</li></ul>',
            },
            {
                'title': 'How to Pick the Right Foundation Shade for Indian Skin',
                'slug': 'right-foundation-shade-indian-skin',
                'cat': 'makeup-tutorials', 'status': 'published', 'is_featured': False, 'reading_time': 5,
                'excerpt': 'A guide to understanding undertones and finding your match.',
                'content': '<h2>Understanding Undertones</h2><p>Warm undertone: Yellow, peachy hints. Cool: Pink, red hints. Neutral: Mix of both. Olive: Greenish-grey common in South Asian skin.</p><h2>How to Test</h2><p>Always swatch on your jawline in natural light.</p>',
            },
            {
                'title': 'Top 5 Ayurvedic Skincare Ingredients That Actually Work',
                'slug': 'top-5-ayurvedic-skincare-ingredients',
                'cat': 'skincare-tips', 'status': 'published', 'is_featured': False, 'reading_time': 4,
                'excerpt': 'Ancient wisdom meets modern skincare with these proven ingredients.',
                'content': '<h2>1. Neem</h2><p>Powerful antibacterial that fights acne-causing bacteria.</p><h2>2. Turmeric</h2><p>Anti-inflammatory and brightening — reduces dark spots.</p><h2>3. Rose Water</h2><p>Natural toner that soothes and hydrates.</p><h2>4. Aloe Vera</h2><p>Deeply hydrating and calming for sensitive skin.</p><h2>5. Sandalwood</h2><p>Cooling, anti-inflammatory, and great for oily skin.</p>',
            },
        ]

        created = 0
        for p in posts_data:
            _, new = BlogPost.objects.get_or_create(
                slug=p['slug'],
                defaults={
                    'title': p['title'],
                    'category': cats.get(p['cat']),
                    'excerpt': p['excerpt'],
                    'content': p['content'],
                    'status': p['status'],
                    'is_featured': p['is_featured'],
                    'reading_time': p['reading_time'],
                    'author': admin_user,
                    'author_name': 'Lumina Team',
                    'published_at': timezone.now() - timedelta(days=random.randint(1, 60)),
                    'tags': 'skincare,beauty,tips',
                    'view_count': random.randint(50, 900),
                }
            )
            if new:
                created += 1
        self.stdout.write(f'  Blog posts: {created} created')

    def _create_notifications(self, customers):
        """Create 4-5 notifications per customer"""
        from apps.notifications.models import Notification

        notifs = [
            {'notif_type': 'tier_upgrade',     'icon': '🌟', 'title': "You've been upgraded to VIP!",         'message': 'Congratulations! Your loyalty points have unlocked VIP tier benefits.'},
            {'notif_type': 'scan_reminder',    'icon': '📸', 'title': 'Time for your Day-30 Scan',            'message': "It's been 30 days since your first scan. Take a new scan to track progress!"},
            {'notif_type': 'points_earned',    'icon': '⭐', 'title': 'You earned 150 points!',               'message': 'You earned 150 loyalty points for completing your weekly check-in.'},
            {'notif_type': 'routine_reminder', 'icon': '🌙', 'title': "Don't forget your night routine!",     'message': 'Completing your PM routine earns you 10 points. Keep the streak going!'},
            {'notif_type': 'order_update',     'icon': '📦', 'title': 'Your order has been shipped!',         'message': 'Your order is on its way! Expected delivery in 3-5 business days.'},
        ]
        created = 0
        for (user, _) in customers:
            if user.notifications.count() >= 3:
                continue
            for nd in notifs:
                Notification.objects.get_or_create(
                    user=user, title=nd['title'],
                    defaults={
                        'notif_type': nd['notif_type'],
                        'message': nd['message'],
                        'icon': nd['icon'],
                        'is_read': random.choice([True, False]),
                    }
                )
                created += 1
        self.stdout.write(f'  Notifications: {created} created')

    def _create_reviews(self, customers, products):
        """Create product reviews — one per customer per product"""
        from apps.reviews.models import ProductReview

        skin_types = ['oily', 'dry', 'combination', 'normal', 'sensitive']
        concerns   = ['acne', 'pigmentation', 'dryness', 'aging', 'dullness']
        reviews_data = [
            {'rating': 5, 'title': 'Absolutely love this!',           'body': 'This product transformed my skin completely. My skin feels so hydrated and glowing every morning. Will definitely repurchase!'},
            {'rating': 4, 'title': 'Great product, minor issues',      'body': 'Packaging could be better but the product itself works really well. Noticed visible results within 2 weeks of use.'},
            {'rating': 5, 'title': 'Holy grail skincare item',         'body': 'I have tried many products for my acne-prone skin and this is by far the best. No breakouts after using this!'},
            {'rating': 3, 'title': 'Good but not amazing',             'body': 'Decent product for the price. Did not see dramatic results but my skin feels softer and more moisturized.'},
            {'rating': 5, 'title': 'Repurchased 3 times already',      'body': 'Cannot imagine my skincare routine without this. Perfect for the humid Indian climate. Highly recommend!'},
        ]
        created = 0
        for i, (user, _) in enumerate(customers):
            prod = products[i % len(products)]
            from apps.reviews.models import ProductReview
            _, new = ProductReview.objects.get_or_create(
                product=prod, user=user,
                defaults={
                    'rating':           reviews_data[i % len(reviews_data)]['rating'],
                    'title':            reviews_data[i % len(reviews_data)]['title'],
                    'body':             reviews_data[i % len(reviews_data)]['body'],
                    'skin_type':        random.choice(skin_types),
                    'concern':          random.choice(concerns),
                    'used_for_weeks':   random.randint(2, 12),
                    'would_recommend':  True,
                    'status':           'approved',
                    'purchase_verified': True,
                    'helpful_count':    random.randint(0, 25),
                }
            )
            if new:
                created += 1
        self.stdout.write(f'  Reviews: {created} created')

    def _create_scans(self, customers):
        """Create 1-2 scan results per customer"""
        from apps.scanner.models import ScanResult

        skin_tones  = ['fair', 'light', 'medium', 'tan', 'deep']
        undertones  = ['warm', 'cool', 'neutral', 'olive']
        skin_types  = ['oily', 'dry', 'combination', 'normal']
        face_shapes = ['oval', 'round', 'square', 'heart', 'oblong']
        severities  = ['none', 'mild', 'moderate']

        created = 0
        for i, (user, _) in enumerate(customers):
            if user.scans.exists():
                continue
            for j in range(2):
                ScanResult.objects.create(
                    user=user,
                    gender='female',
                    skin_tone=skin_tones[i % len(skin_tones)],
                    undertone=undertones[i % len(undertones)],
                    face_shape=face_shapes[i % len(face_shapes)],
                    skin_type=skin_types[i % len(skin_types)],
                    skin_age=random.randint(22, 35),
                    real_age=random.randint(22, 32),
                    harmony_score=random.randint(60, 90),
                    hydration_score=random.randint(45, 85),
                    pigmentation_score=random.randint(15, 45),
                    acne_score=random.randint(10, 40),
                    aging_score=random.randint(15, 35),
                    elasticity_score=random.randint(55, 80),
                    hf_acne_severity=severities[i % len(severities)],
                    hf_skin_type=skin_types[i % len(skin_types)],
                    hf_undertone=undertones[i % len(undertones)],
                    hf_acne_confidence=round(random.uniform(0.6, 0.99), 2),
                    hf_skin_type_confidence=round(random.uniform(0.7, 0.99), 2),
                    hf_undertone_confidence=round(random.uniform(0.65, 0.99), 2),
                    facial_zones={
                        'forehead': {'oiliness': random.randint(2, 5), 'pores': random.randint(1, 4)},
                        'nose':     {'oiliness': random.randint(3, 5), 'pores': random.randint(2, 5)},
                        'cheeks':   {'oiliness': random.randint(1, 3), 'pores': random.randint(1, 3)},
                        'chin':     {'oiliness': random.randint(2, 4), 'pores': random.randint(1, 4)},
                    },
                    qa_age=random.randint(22, 32),
                    qa_water_intake=random.choice(['low', 'moderate', 'high']),
                    qa_sleep_hours=random.choice(['<6', '6-8', '>8']),
                    qa_stress_level=random.choice(['low', 'moderate', 'high']),
                    qa_diet=random.choice(['balanced', 'oily', 'sugary']),
                    qa_outdoor_hours=random.choice(['low', 'moderate', 'high']),
                    qa_skin_concerns=random.sample(['acne', 'pigmentation', 'dryness', 'aging', 'dullness'], k=2),
                    qa_completed=True,
                )
                created += 1
        self.stdout.write(f'  Scan Results: {created} created')

    def _create_diagnostic(self, customers):
        """Create diagnostic sessions and habit data"""
        from apps.diagnostic.models import (
            DiagnosticSession, SmartDiagSession, HabitCategory, HabitLog
        )

        habit_cats_data = [
            {'slug': 'drink-water',    'title': 'Drink 8 Glasses of Water', 'icon': '💧', 'color_class': 'blue',   'points': 10, 'order': 1},
            {'slug': 'apply-spf',      'title': 'Apply SPF Every Morning',  'icon': '☀️', 'color_class': 'yellow', 'points': 15, 'order': 2},
            {'slug': 'night-routine',  'title': 'Complete Night Routine',   'icon': '🌙', 'color_class': 'purple', 'points': 20, 'order': 3},
            {'slug': 'eat-fruits-veg', 'title': 'Eat Fruits & Vegetables',  'icon': '🥗', 'color_class': 'green',  'points': 10, 'order': 4},
        ]
        habit_cats = []
        for h in habit_cats_data:
            obj, _ = HabitCategory.objects.get_or_create(slug=h['slug'], defaults=h)
            habit_cats.append(obj)

        skin_types = ['oily', 'dry', 'combination', 'normal', 'sensitive']
        concerns   = ['acne', 'pigmentation', 'dryness', 'aging', 'dullness']
        d_created = 0

        for (user, _) in customers:
            if not DiagnosticSession.objects.filter(user=user).exists():
                DiagnosticSession.objects.create(
                    user=user,
                    selected_categories=random.sample(concerns, k=2),
                    skin_type=random.choice(skin_types),
                    concern_1=random.choice(concerns),
                    concern_2=random.choice(concerns),
                    budget=random.choice(['low', 'mid', 'high']),
                    water_intake=random.randint(4, 9),
                    sleep_hours=random.randint(5, 8),
                    stress_level=random.randint(2, 8),
                    recommended_tier=random.choice(['normal', 'medium', 'vip']),
                    completed=True,
                )
                d_created += 1

            if not SmartDiagSession.objects.filter(user=user).exists():
                SmartDiagSession.objects.create(
                    user=user,
                    primary_goal=random.choice(['glow', 'acne', 'aging', 'hydration']),
                    answers={'skin_type': random.choice(skin_types), 'concerns': random.sample(concerns, 2)},
                    analysis={'severity': 'mild', 'recommendations': ['niacinamide', 'spf50', 'gentle cleanser']},
                    severity=random.choice(['minimal', 'mild', 'moderate']),
                    top_concern_cat=random.choice(concerns),
                    completed=True,
                )

            if not HabitLog.objects.filter(user=user).exists():
                for habit in habit_cats:
                    HabitLog.objects.create(
                        user=user, habit=habit,
                        points_earned=habit.points,
                        notes='',
                    )

        self.stdout.write(f'  Diagnostic Sessions: {d_created} created')
        self.stdout.write(f'  Habit Categories: {len(habit_cats)} ready')

    def _create_crm_leads(self, employees):
        """Create 5 CRM leads assigned to employees"""
        from apps.employee.models import Lead

        leads_data = [
            {'name': 'Pooja Nair',    'phone': '9012345678', 'email': 'pooja@gmail.com',
             'city': 'Kochi',       'source': 'instagram', 'stage': 'interested',
             'skin_concern': 'Acne and pigmentation',       'budget': '1000-2500'},
            {'name': 'Sakshi Gupta',  'phone': '9112233445', 'email': 'sakshi@yahoo.com',
             'city': 'Jaipur',      'source': 'website',   'stage': 'product_shared',
             'skin_concern': 'Dry skin and anti-aging',     'budget': '2500+'},
            {'name': 'Tanu Sharma',   'phone': '9223344556', 'email': 'tanu@gmail.com',
             'city': 'Chandigarh',  'source': 'referral',  'stage': 'new',
             'skin_concern': 'Oily skin and large pores',   'budget': '500-1000'},
            {'name': 'Anita Bose',    'phone': '9334455667', 'email': 'anita@outlook.com',
             'city': 'Kolkata',     'source': 'facebook',  'stage': 'contacted',
             'skin_concern': 'Dark circles and dullness',   'budget': '1000-2500'},
            {'name': 'Nisha Reddy',   'phone': '9445566778', 'email': 'nisha@gmail.com',
             'city': 'Hyderabad',   'source': 'whatsapp',  'stage': 'demo_given',
             'skin_concern': 'Pigmentation and uneven tone','budget': '2500+'},
        ]
        created = 0
        for i, ld in enumerate(leads_data):
            emp = employees[i % len(employees)]
            _, new = Lead.objects.get_or_create(
                phone=ld['phone'],
                defaults={
                    'name':          ld['name'],
                    'email':         ld['email'],
                    'city':          ld['city'],
                    'source':        ld['source'],
                    'stage':         ld['stage'],
                    'skin_concern':  ld['skin_concern'],
                    'budget':        ld['budget'],
                    'assigned_to':   emp,
                    'created_by':    emp,
                    'follow_up_date': date.today() + timedelta(days=random.randint(1, 7)),
                    'notes': 'Reached out via social media. Interested in full skincare routine.',
                }
            )
            if new:
                created += 1
        self.stdout.write(f'  CRM Leads: {created} created')

    def _create_support_tickets(self, customers, employees):
        """Create 5 support tickets with replies"""
        from apps.employee.models import SupportTicket, TicketReply

        tickets_data = [
            {'subject': 'My order has not arrived after 10 days',
             'description': 'I placed an order 10 days ago and tracking shows it is still in transit.',
             'channel': 'chat',     'priority': 'high',   'status': 'open'},
            {'subject': 'Wrong shade of foundation sent',
             'description': 'I ordered Maybelline Fit Me Shade 220 but received Shade 120.',
             'channel': 'email',    'priority': 'medium', 'status': 'in_progress'},
            {'subject': 'How do I track my daily routine streak?',
             'description': 'I can see the habit log section but cannot find my streak history.',
             'channel': 'portal',   'priority': 'low',    'status': 'resolved'},
            {'subject': 'Coupon code LUMINA20 is not working at checkout',
             'description': 'Applied LUMINA20 but it says invalid. My cart total is Rs 850.',
             'channel': 'whatsapp', 'priority': 'medium', 'status': 'open'},
            {'subject': 'Product arrived damaged — serum bottle cracked',
             'description': 'The COSRX Snail Mucin Essence arrived with a cracked pump. Need replacement.',
             'channel': 'email',    'priority': 'high',   'status': 'in_progress'},
        ]
        replies_text = [
            'Thank you for reaching out! We are looking into this and will update you within 24 hours.',
            'We apologise for the inconvenience. A replacement has been arranged for you.',
            'You can view your streak in the Dashboard under Progress. Let us know if you need help.',
            'Please ensure the coupon has not expired and your cart meets the minimum order value.',
            'We are so sorry to hear that! Please share a photo and we will arrange an immediate replacement.',
        ]
        created = 0
        for i, td in enumerate(tickets_data):
            cust_user, c_data = customers[i % len(customers)]
            emp = employees[i % len(employees)]
            ticket, new = SupportTicket.objects.get_or_create(
                customer=cust_user, subject=td['subject'],
                defaults={
                    'customer_name':  f'{cust_user.first_name} {cust_user.last_name}',
                    'customer_email': cust_user.email,
                    'customer_phone': c_data['phone'],
                    'description':    td['description'],
                    'channel':        td['channel'],
                    'priority':       td['priority'],
                    'status':         td['status'],
                    'assigned_to':    emp,
                    'resolution':     'Under investigation.' if td['status'] == 'in_progress' else '',
                }
            )
            if new:
                TicketReply.objects.create(
                    ticket=ticket,
                    author=emp,
                    message=replies_text[i],
                    is_internal=False,
                )
                created += 1
        self.stdout.write(f'  Support Tickets: {created} created')

    def _create_salary_and_leaves(self, employees, admin_user):
        """Create 3 months salary records and 2 leave requests per employee"""
        from apps.admin_panel.models import SalaryRecord, EmployeeLeave

        now = timezone.now()
        sal_created = 0
        for user in employees:
            basic = Decimal(str(random.choice([28000, 35000, 42000, 52000])))
            for offset in range(3):
                mo = (now.month - offset - 1) % 12 + 1
                yr = now.year if (now.month - offset) > 0 else now.year - 1
                _, new = SalaryRecord.objects.get_or_create(
                    employee=user, month=mo, year=yr,
                    defaults={
                        'basic_salary': basic,
                        'hra':          basic * Decimal('0.4'),
                        'allowances':   Decimal('3000'),
                        'incentives':   Decimal(str(random.randint(0, 5000))),
                        'deductions':   Decimal('2000'),
                        'tax_deducted': basic * Decimal('0.05'),
                        'net_salary':   basic + basic * Decimal('0.4') + Decimal('3000')
                                        - Decimal('2000') - basic * Decimal('0.05'),
                        'status':       'paid',
                        'created_by':   admin_user,
                    }
                )
                if new:
                    sal_created += 1

        leave_reasons = [
            'Family function in hometown',
            'Medical appointment — follow-up checkup',
            'Personal work — document submission',
            'Sick — fever and cold',
            'Attending sibling wedding',
        ]
        leave_created = 0
        for user in employees:
            if EmployeeLeave.objects.filter(employee=user).count() >= 2:
                continue
            for i in range(2):
                from_d = date.today() - timedelta(days=random.randint(5, 45))
                EmployeeLeave.objects.create(
                    employee=user,
                    leave_type=random.choice(['casual', 'sick', 'earned']),
                    from_date=from_d,
                    to_date=from_d + timedelta(days=random.randint(1, 2)),
                    days=random.randint(1, 2),
                    reason=random.choice(leave_reasons),
                    status=random.choice(['approved', 'approved', 'pending']),
                    approved_by=admin_user,
                )
                leave_created += 1

        self.stdout.write(f'  Salary Records: {sal_created} created')
        self.stdout.write(f'  Leave Requests: {leave_created} created')

    def _create_attendance(self, employees, admin_user):
        """Create attendance records for last 7 working days"""
        from apps.employee.models import EmployeeAttendance

        statuses = ['present', 'present', 'present', 'present', 'half', 'wfh']
        created = 0
        for user in employees:
            for day_offset in range(1, 8):
                day = date.today() - timedelta(days=day_offset)
                if day.weekday() >= 5:
                    continue
                _, new = EmployeeAttendance.objects.get_or_create(
                    employee=user, date=day,
                    defaults={
                        'status':    random.choice(statuses),
                        'check_in':  dtime(9,  random.randint(0, 30)),
                        'check_out': dtime(18, random.randint(0, 30)),
                        'marked_by': admin_user,
                    }
                )
                if new:
                    created += 1
        self.stdout.write(f'  Attendance Records: {created} created')

    def _create_sales_targets(self, employees):
        """Create daily sales targets for last 5 working days"""
        from apps.employee.models import SalesTarget

        created = 0
        for user in employees:
            for day_offset in range(5):
                day = date.today() - timedelta(days=day_offset)
                if day.weekday() >= 5:
                    continue
                target   = Decimal(str(random.choice([10000, 15000, 20000])))
                achieved = (target * Decimal(str(round(random.uniform(0.55, 1.25), 2)))).quantize(Decimal('0.01'))
                _, new = SalesTarget.objects.get_or_create(
                    employee=user, date=day,
                    defaults={'target': target, 'achieved': achieved}
                )
                if new:
                    created += 1
        self.stdout.write(f'  Sales Targets: {created} created')

    def _create_progress(self, customers):
        """Create daily routine logs and weekly check-ins per customer"""
        from apps.progress.models import DailyRoutineLog, WeeklyCheckin

        d_created = 0
        w_created = 0
        for (user, _) in customers:
            for day_offset in range(1, 6):
                day = date.today() - timedelta(days=day_offset)
                _, new = DailyRoutineLog.objects.get_or_create(
                    user=user, log_date=day,
                    defaults={
                        'am_done':       random.choice([True, True, False]),
                        'pm_done':       random.choice([True, False]),
                        'water_glasses': random.randint(4, 10),
                        'spf_applied':   random.choice([True, True, False]),
                        'skin_rating':   random.randint(3, 5),
                    }
                )
                if new:
                    d_created += 1

            _, new = WeeklyCheckin.objects.get_or_create(
                user=user, week_number=1,
                defaults={
                    'week_start':        date.today() - timedelta(days=7),
                    'overall_rating':    random.randint(3, 5),
                    'hydration_rating':  random.randint(3, 5),
                    'acne_rating':       random.randint(3, 5),
                    'brightness_rating': random.randint(3, 5),
                    'products_used':     ['COSRX Snail Mucin', 'Laneige Mask', 'SPF 50'],
                    'new_concerns':      'Slight dryness on cheeks',
                    'has_selfie':        False,
                }
            )
            if new:
                w_created += 1

        self.stdout.write(f'  Daily Routine Logs: {d_created} created')
        self.stdout.write(f'  Weekly Check-ins: {w_created} created')

    def _create_coupons(self):
        """Create 5 coupons of different types"""
        from apps.coupons.models import Coupon

        coupons_data = [
            {'code': 'LUMINA20',  'coupon_type': 'percent', 'discount_value': 20,
             'description': '20% off for all customers',     'scope': 'all',
             'min_order_value': 500, 'max_uses': 100, 'max_uses_per_user': 1, 'is_active': True},
            {'code': 'WELCOME50', 'coupon_type': 'fixed',   'discount_value': 50,
             'description': 'Rs 50 off on first order',      'scope': 'all',
             'min_order_value': 300, 'max_uses': 500, 'max_uses_per_user': 1, 'is_active': True},
            {'code': 'KBEAUTY15', 'coupon_type': 'percent', 'discount_value': 15,
             'description': '15% off on K-Beauty range',     'scope': 'korean',
             'min_order_value': 800, 'max_uses': 50,  'max_uses_per_user': 2, 'is_active': True,
             'tier_required': 'medium'},
            {'code': 'VIPDEAL30', 'coupon_type': 'percent', 'discount_value': 30,
             'description': 'VIP exclusive 30% discount',    'scope': 'all',
             'min_order_value': 1000,'max_uses': 20,  'max_uses_per_user': 1, 'is_active': True,
             'tier_required': 'vip'},
            {'code': 'FREESHIP',  'coupon_type': 'free_ship','discount_value': 0,
             'description': 'Free shipping on any order',    'scope': 'all',
             'min_order_value': 200, 'max_uses': 200, 'max_uses_per_user': 3, 'is_active': True},
        ]
        created = 0
        for c in coupons_data:
            _, new = Coupon.objects.get_or_create(
                code=c['code'],
                defaults={k: v for k, v in c.items() if k != 'code'}
            )
            if new:
                created += 1
        self.stdout.write(f'  Coupons: {created} created')

    def _create_admin_tasks(self, admin_user, employees):
        """Create 5 admin tasks assigned to employees"""
        from apps.admin_panel.models import AdminTask

        tasks_data = [
            {'title': 'Review Q3 marketing campaign results',
             'description': 'Analyse conversion rates, leads generated, and ROI for Q3 campaigns.',
             'priority': 'high',   'status': 'in_progress'},
            {'title': 'Update product catalogue with new K-Beauty arrivals',
             'description': 'Add 15 new COSRX and Innisfree products with correct SKUs and images.',
             'priority': 'medium', 'status': 'todo'},
            {'title': 'Onboard 2 new support agents',
             'description': 'Prepare training documents and system access for new hires.',
             'priority': 'high',   'status': 'todo'},
            {'title': 'Monthly salary processing',
             'description': 'Process all employee salaries and upload bank transfer receipts.',
             'priority': 'urgent', 'status': 'done'},
            {'title': 'Audit and clean up inactive customer accounts',
             'description': 'Identify accounts with no activity for 6+ months and send re-engagement emails.',
             'priority': 'low',    'status': 'todo'},
        ]
        created = 0
        for i, t in enumerate(tasks_data):
            _, new = AdminTask.objects.get_or_create(
                title=t['title'],
                defaults={
                    'description': t['description'],
                    'priority':    t['priority'],
                    'status':      t['status'],
                    'assigned_to': employees[i % len(employees)],
                    'created_by':  admin_user,
                    'due_date':    date.today() + timedelta(days=random.randint(2, 14)),
                }
            )
            if new:
                created += 1
        self.stdout.write(f'  Admin Tasks: {created} created')

    def _create_campaigns(self, employees):
        """Create 4 marketing campaigns"""
        from apps.employee.models import Campaign

        camps_data = [
            {'name': 'Monsoon Glow Campaign',       'type': 'instagram', 'status': 'active',
             'description': 'Target oily-skin users with monsoon skincare tips and product bundles.',
             'target_audience': 'Age 18-30, oily skin, Tier Normal/Medium',
             'budget': Decimal('25000'), 'spent': Decimal('18500'),
             'leads_generated': 45, 'conversions': 12, 'revenue': Decimal('38000')},
            {'name': 'VIP Re-engagement Email Blast', 'type': 'email',  'status': 'completed',
             'description': 'Re-engage VIP users who have not ordered in the last 60 days.',
             'target_audience': 'VIP tier, inactive 60+ days',
             'budget': Decimal('5000'),  'spent': Decimal('4800'),
             'leads_generated': 0,  'conversions': 8,  'revenue': Decimal('24000')},
            {'name': 'K-Beauty Awareness WhatsApp',  'type': 'whatsapp','status': 'scheduled',
             'description': 'Introduce the Korean skincare range to new sign-ups via WhatsApp broadcast.',
             'target_audience': 'New users registered in last 30 days',
             'budget': Decimal('8000'),  'spent': Decimal('0'),
             'leads_generated': 0,  'conversions': 0,  'revenue': Decimal('0')},
            {'name': 'Festive Season Referral Drive', 'type': 'referral','status': 'draft',
             'description': 'Give existing users a special referral bonus during the festive season.',
             'target_audience': 'All active users',
             'budget': Decimal('15000'), 'spent': Decimal('0'),
             'leads_generated': 0,  'conversions': 0,  'revenue': Decimal('0')},
        ]
        created = 0
        for i, c in enumerate(camps_data):
            _, new = Campaign.objects.get_or_create(
                name=c['name'],
                defaults={
                    'type':             c['type'],
                    'status':           c['status'],
                    'description':      c['description'],
                    'target_audience':  c['target_audience'],
                    'budget':           c['budget'],
                    'spent':            c['spent'],
                    'leads_generated':  c['leads_generated'],
                    'conversions':      c['conversions'],
                    'revenue':          c['revenue'],
                    'created_by':       employees[i % len(employees)],
                }
            )
            if new:
                created += 1
        self.stdout.write(f'  Campaigns: {created} created')

    def _create_company_settings(self):
        """Create company settings singleton"""
        from apps.admin_panel.models import CompanySettings

        if not CompanySettings.objects.exists():
            CompanySettings.objects.create(
                company_name='Lumina AI Beauty',
                company_email='hello@lumina.app',
                support_email='support@lumina.app',
                hr_email='hr@lumina.app',
                sales_email='sales@lumina.app',
                marketing_email='marketing@lumina.app',
                phone='+91 98765 43210',
                address='Level 5, Tech Park, Whitefield',
                city='Bangalore', state='Karnataka', pincode='560066',
                gstin='29AABCL1234M1Z5',
                website='https://lumina.app',
                currency='INR', timezone='Asia/Kolkata',
            )
            self.stdout.write('  Company Settings: created')
        else:
            self.stdout.write('  Company Settings: already exists')

    def _create_admin_activity(self, admin_user):
        """Create admin activity log entries"""
        from apps.admin_panel.models import AdminActivity

        if AdminActivity.objects.count() >= 5:
            self.stdout.write('  Admin Activity: already seeded')
            return
        activities = [
            {'action': 'login',  'module': 'auth',      'description': 'Admin suhani logged in from Bangalore'},
            {'action': 'create', 'module': 'employees', 'description': 'Created new employee: janvi_u'},
            {'action': 'update', 'module': 'orders',    'description': 'Updated order status to Shipped'},
            {'action': 'approve','module': 'leaves',    'description': 'Approved casual leave for priya_emp'},
            {'action': 'export', 'module': 'reports',   'description': 'Exported monthly sales report PDF'},
        ]
        for a in activities:
            AdminActivity.objects.create(
                admin=admin_user, action=a['action'],
                module=a['module'], description=a['description'],
                ip_address='103.21.58.14',
            )
        self.stdout.write(f'  Admin Activity: {len(activities)} created')

    def _create_quick_prompts(self):
        """Create quick chat prompts"""
        from apps.chat.models import QuickPrompt

        prompts = [
            {'prompt_text': 'I have acne on my forehead and cheeks',  'category': 'acne',         'order': 1},
            {'prompt_text': 'My skin feels very dry and tight',       'category': 'dryness',      'order': 2},
            {'prompt_text': 'I have dark circles under my eyes',      'category': 'dark_circles', 'order': 3},
            {'prompt_text': 'Help me build a Korean skincare routine', 'category': 'routine',      'order': 4},
            {'prompt_text': 'What foundation shade matches my skin?',  'category': 'makeup',       'order': 5},
        ]
        created = 0
        for p in prompts:
            _, new = QuickPrompt.objects.get_or_create(
                prompt_text=p['prompt_text'],
                defaults={'category': p['category'], 'order': p['order'], 'active': True}
            )
            if new:
                created += 1
        self.stdout.write(f'  Quick Prompts: {created} created')

