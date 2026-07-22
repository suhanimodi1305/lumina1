"""
Management command: python manage.py seed_all

Seeds the entire Lumina database with realistic demo data for:
  - 1 superuser (admin)
  - 3 employee (staff) users with profiles, attendance, salary, leaves
  - 4 customer users with profiles, orders, scans, reviews, notifications
  - Products (8), Blog posts (4), Coupons (4), Blog categories (4)
  - Diagnostic sessions, Habit categories/logs, Support tickets, CRM leads
  - Chat conversations, Notifications, Progress logs

Run: python manage.py seed_all
Re-runnable: skips already-existing records safely.
"""
import random
from datetime import timedelta, date, time as dtime
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

# ── Sample data pools ─────────────────────────────────────────────────────────

ADMIN_USER = dict(username='admin', email='admin@lumina.com',
                  password='Admin@1234', first_name='Admin', last_name='Lumina',
                  is_staff=True, is_superuser=True)

EMPLOYEES = [
    dict(username='priya_emp',  first_name='Priya',  last_name='Sharma',
         email='priya@lumina.in',  password='Lumina@2024', is_staff=True,
         designation='Skin Consultant', department='Customer Care',
         phone='9876543210', city='Mumbai', joining_date=date(2023, 1, 15)),
    dict(username='rahul_emp',  first_name='Rahul',  last_name='Verma',
         email='rahul@lumina.in',  password='Lumina@2024', is_staff=True,
         designation='Sales Executive', department='Sales',
         phone='9123456780', city='Delhi', joining_date=date(2022, 6, 1)),
    dict(username='sneha_emp',  first_name='Sneha',  last_name='Patel',
         email='sneha@lumina.in',  password='Lumina@2024', is_staff=True,
         designation='Marketing Manager', department='Marketing',
         phone='9988776655', city='Bangalore', joining_date=date(2021, 9, 20)),
]

CUSTOMERS = [
    dict(username='suhani',   first_name='Suhani', last_name='',
         email='suhani@example.com', password='Lumina@2025', city='Delhi',
         phone='9870005555', tier='vip'),
    dict(username='aanya_k',  first_name='Aanya',  last_name='Kapoor',
         email='aanya@gmail.com',   password='User@1234', city='Mumbai',
         phone='9870001111', tier='vip'),
    dict(username='meera_s',  first_name='Meera',  last_name='Singh',
         email='meera@gmail.com',   password='User@1234', city='Delhi',
         phone='9870002222', tier='medium'),
    dict(username='divya_r',  first_name='Divya',  last_name='Rao',
         email='divya@gmail.com',   password='User@1234', city='Hyderabad',
         phone='9870003333', tier='normal'),
    dict(username='kavya_m',  first_name='Kavya',  last_name='Mehta',
         email='kavya@gmail.com',   password='User@1234', city='Bangalore',
         phone='9870004444', tier='normal'),
]

PRODUCTS = [
    dict(name='Laneige Water Sleeping Mask', brand='Laneige', category='mask',
         product_range='korean', sku='LAN-WSM-001', price=1850,
         description='Overnight hydration mask with mineral water and beta-glucan.',
         key_ingredients='Mineral Water, Beta-Glucan, Evening Primrose Extract',
         suitable_for_skin_types=['dry', 'combination', 'normal']),
    dict(name='COSRX Snail Mucin Essence', brand='COSRX', category='essence',
         product_range='korean', sku='COS-SME-002', price=1299,
         description='96% snail secretion filtrate for repair and hydration.',
         key_ingredients='Snail Secretion Filtrate, Panthenol, Sodium Hyaluronate',
         suitable_for_skin_types=['all']),
    dict(name='Some By Mi AHA BHA PHA Toner', brand='Some By Mi', category='toner',
         product_range='korean', sku='SBM-ABP-003', price=999,
         description='Exfoliating toner with triple acids to unclog pores.',
         key_ingredients='AHA, BHA, PHA, Tea Tree, Niacinamide',
         suitable_for_skin_types=['oily', 'combination']),
    dict(name='Innisfree Green Tea Serum', brand='Innisfree', category='serum',
         product_range='korean', sku='INF-GTS-004', price=1150,
         description='Antioxidant serum with Jeju green tea extracts.',
         key_ingredients='Green Tea Extract, Hyaluronic Acid, EGF',
         suitable_for_skin_types=['oily', 'combination', 'normal']),
    dict(name='Maybelline Fit Me Foundation', brand='Maybelline', category='foundation',
         product_range='makeup', sku='MAY-FMF-005', price=549,
         description='Natural finish foundation with SPF 18 for all skin types.',
         key_ingredients='SPF 18, Poreless Formula, Natural Pigments',
         suitable_for_skin_types=['all']),
    dict(name='MAC Ruby Woo Lipstick', brand='MAC', category='lipstick',
         product_range='makeup', sku='MAC-RWL-006', price=1850,
         description='Iconic matte vivid red lipstick with long-wear formula.',
         key_ingredients='Vitamin E, Jojoba Oil, Mica',
         suitable_for_skin_types=['all']),
    dict(name='Biotique Bio Neem Purifying Face Wash', brand='Biotique',
         category='cleanser', product_range='ayurvedic', sku='BIO-NNF-007', price=199,
         description='Ayurvedic neem face wash for oily and acne-prone skin.',
         key_ingredients='Neem Extract, Tulsi, Turmeric',
         suitable_for_skin_types=['oily', 'combination']),
    dict(name='Neutrogena Hydro Boost Water Gel', brand='Neutrogena',
         category='moisturizer', product_range='korean', sku='NEU-HBW-008', price=899,
         description='Oil-free gel moisturizer with hyaluronic acid.',
         key_ingredients='Hyaluronic Acid, Dimethicone, Glycerin',
         suitable_for_skin_types=['oily', 'combination', 'normal']),
]

BLOG_CATEGORIES = [
    dict(name='Skincare Tips', slug='skincare-tips', icon='✨', order=1,
         description='Expert advice for healthy, glowing skin'),
    dict(name='K-Beauty', slug='k-beauty', icon='🇰🇷', order=2,
         description='Korean beauty trends and product reviews'),
    dict(name='Makeup Tutorials', slug='makeup-tutorials', icon='💄', order=3,
         description='Step-by-step makeup guides for every occasion'),
    dict(name='Ingredients Guide', slug='ingredients-guide', icon='🧪', order=4,
         description='Deep dives into skincare ingredients and what they do'),
]

BLOG_POSTS = [
    dict(title='The Ultimate Guide to Korean Skincare Routine',
         slug='ultimate-guide-korean-skincare-routine',
         category_slug='k-beauty',
         excerpt='Learn the famous 10-step K-beauty routine and how to adapt it for Indian skin.',
         content='''<h2>What is K-Beauty?</h2>
<p>Korean skincare has taken the world by storm. The focus is on layering lightweight products for deep hydration and a glass-skin effect.</p>
<h2>The 10-Step Routine</h2>
<ol>
<li><strong>Oil Cleanser</strong> – Remove SPF and makeup gently.</li>
<li><strong>Water-Based Cleanser</strong> – Deep cleanse without stripping moisture.</li>
<li><strong>Exfoliator</strong> – Use 2-3 times a week for cell turnover.</li>
<li><strong>Toner</strong> – Hydrate and balance pH levels.</li>
<li><strong>Essence</strong> – Concentrated hydration with snail mucin or fermented ingredients.</li>
<li><strong>Serums/Ampoules</strong> – Target specific concerns like acne or pigmentation.</li>
<li><strong>Sheet Mask</strong> – Weekly deep treatment.</li>
<li><strong>Eye Cream</strong> – Gently tap around the orbital bone.</li>
<li><strong>Moisturizer</strong> – Lock in all layers.</li>
<li><strong>SPF (AM only)</strong> – The most important step.</li>
</ol>
<p>You don't need all 10 steps every day. Start with 4-5 and build gradually.</p>''',
         status='published', is_featured=True, reading_time=7),
    dict(title='Niacinamide vs Vitamin C: Which One Should You Use?',
         slug='niacinamide-vs-vitamin-c',
         category_slug='ingredients-guide',
         excerpt='Two of the most popular brightening ingredients explained — and when to use each.',
         content='''<h2>Niacinamide (Vitamin B3)</h2>
<p>Niacinamide is a multitasker: it reduces pore size, controls sebum, brightens dark spots, and strengthens the skin barrier. It's gentle enough for daily use and suits all skin types — especially oily and acne-prone.</p>
<h2>Vitamin C (Ascorbic Acid)</h2>
<p>Vitamin C is a powerful antioxidant that neutralizes free radicals, boosts collagen, and fades hyperpigmentation. It works best in the morning under SPF. However, it can be unstable and irritating in high concentrations.</p>
<h2>Can You Use Both?</h2>
<p>Yes! Use Vitamin C in the morning and Niacinamide in the evening, or alternate them. Older advice said they cancel each other out — modern formulations have debunked this.</p>
<h2>Recommendation</h2>
<p>If you're a beginner, start with Niacinamide at 10%. Add Vitamin C (10-15%) once your skin is accustomed to actives.</p>''',
         status='published', is_featured=False, reading_time=5),
    dict(title='Skincare Routine for Acne-Prone Skin in Indian Climate',
         slug='skincare-routine-acne-prone-indian-climate',
         category_slug='skincare-tips',
         excerpt='Beat humidity, sweat, and breakouts with this dermatologist-inspired routine for Indian skin.',
         content='''<h2>Why Indian Climate Makes Acne Worse</h2>
<p>High humidity increases sebum production. Combined with pollution and heat, this clogs pores and leads to frequent breakouts.</p>
<h2>Morning Routine</h2>
<ul>
<li>Gentle gel cleanser (avoid creamy formulas)</li>
<li>Niacinamide 10% serum</li>
<li>Oil-free moisturizer</li>
<li>Mineral SPF 50 (non-comedogenic)</li>
</ul>
<h2>Evening Routine</h2>
<ul>
<li>Double cleanse (oil cleanser + gel cleanser)</li>
<li>BHA toner (salicylic acid 2%) 3x per week</li>
<li>Spot treatment (benzoyl peroxide or tea tree)</li>
<li>Light gel moisturizer</li>
</ul>
<h2>Key Tips</h2>
<p>Change pillowcase weekly. Avoid touching your face. Stay hydrated. Limit dairy if you notice a connection with breakouts.</p>''',
         status='published', is_featured=True, reading_time=6),
    dict(title='How to Pick the Right Foundation Shade for Indian Skin Tones',
         slug='right-foundation-shade-indian-skin',
         category_slug='makeup-tutorials',
         excerpt='A complete guide to understanding undertones and finding your perfect foundation match.',
         content='''<h2>Understanding Undertones</h2>
<p>Indian skin tones range from fair to deep, but the key to a perfect foundation match is your undertone — not just your skin tone.</p>
<ul>
<li><strong>Warm undertone</strong>: Yellow, peachy, golden hints. Veins appear greenish.</li>
<li><strong>Cool undertone</strong>: Pink, red, bluish hints. Veins appear blue/purple.</li>
<li><strong>Neutral</strong>: Mix of both. Veins appear blue-green.</li>
<li><strong>Olive</strong>: Greenish-grey undertone common in South Asian skin.</li>
</ul>
<h2>How to Test in Store</h2>
<p>Always swatch on your jawline, not your hand. Step outside to check in natural light. The right shade disappears into your skin.</p>
<h2>Best Brands for Indian Skin</h2>
<p>Maybelline Fit Me, L\'Oreal True Match, Fenty Beauty Pro Filt\'r, MAC Studio Fix, and Nykaa Cosmetics all offer shades for warm and olive undertones.</p>''',
         status='published', is_featured=False, reading_time=5),
]

ADDRESSES = [
    dict(address_line1='12 Rose Garden Apts, MG Road', city='Mumbai',    state='Maharashtra', pincode='400001'),
    dict(address_line1='45 Andheri West, Near Station', city='Delhi',     state='Delhi',       pincode='110001'),
    dict(address_line1='33 Salt Lake, Sector V',        city='Hyderabad', state='Telangana',   pincode='500033'),
    dict(address_line1='Plot 8, Jubilee Hills Rd 36',   city='Bangalore', state='Karnataka',   pincode='560001'),
]

HABIT_CATEGORIES = [
    dict(slug='drink-water',    title='Drink 8 Glasses of Water', icon='💧',
         color_class='blue',   points=10, order=1,
         description='Hydration is the foundation of glowing skin'),
    dict(slug='apply-spf',      title='Apply SPF Every Morning',  icon='☀️',
         color_class='yellow', points=15, order=2,
         description='SPF is the most important anti-aging step'),
    dict(slug='night-routine',  title='Complete Night Routine',   icon='🌙',
         color_class='purple', points=20, order=3,
         description='Nighttime is when skin repairs itself'),
    dict(slug='eat-fruits-veg', title='Eat Fruits & Vegetables',  icon='🥗',
         color_class='green',  points=10, order=4,
         description='Antioxidants from food protect your skin'),
]

QUICK_PROMPTS = [
    dict(prompt_text='I have acne on my forehead and cheeks',  category='acne',        order=1),
    dict(prompt_text='My skin feels very dry and tight',       category='dryness',     order=2),
    dict(prompt_text='I have dark circles under my eyes',      category='dark_circles',order=3),
    dict(prompt_text='Help me build a Korean skincare routine',category='routine',     order=4),
    dict(prompt_text='What foundation shade matches my skin?', category='makeup',      order=5),
    dict(prompt_text='I have oily skin and large pores',       category='oiliness',    order=6),
]


class Command(BaseCommand):
    help = 'Seeds the entire Lumina database with demo data for all sections'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\n== Lumina Full Database Seeder ==\n'))
        now = timezone.now()

        # ── Step 1: Core reference data ───────────────────────────────────────
        products     = self._seed_products()
        blog_cats    = self._seed_blog_categories()
        habit_cats   = self._seed_habit_categories()
        self._seed_quick_prompts()
        self._seed_coupons()
        skin_concerns = self._seed_skin_concerns()

        # ── Step 2: Users ─────────────────────────────────────────────────────
        admin_user   = self._seed_admin()
        employees    = self._seed_employees(admin_user)
        customers    = self._seed_customers()

        # ── Step 3: Admin panel data ──────────────────────────────────────────
        self._seed_departments(admin_user, employees)
        self._seed_salary_and_leaves(employees, admin_user)
        self._seed_admin_tasks(admin_user, employees)
        self._seed_company_settings()
        self._seed_admin_activity(admin_user, employees)

        # ── Step 4: Customer data ─────────────────────────────────────────────
        self._seed_orders(customers, products)
        self._seed_blog_posts(blog_cats, admin_user)
        self._seed_notifications(customers)
        self._seed_habit_logs(customers, habit_cats)
        self._seed_diagnostic_sessions(customers)
        self._seed_leads(employees, customers)
        self._seed_support_tickets(customers, employees, products)
        self._seed_attendance(employees, admin_user)
        self._seed_sales_targets(employees)
        self._seed_progress_logs(customers)

        self.stdout.write(self.style.SUCCESS('\n✓ All demo data seeded successfully!\n'))
        self.stdout.write('  Login credentials:')
        self.stdout.write('    Admin   → admin / Admin@1234')
        self.stdout.write('    Staff   → priya_emp, rahul_emp, sneha_emp / Lumina@2024')
        self.stdout.write('    Customers → aanya_k, meera_s, divya_r, kavya_m / User@1234\n')

    # ─────────────────────────────────────────────────────────────────────────
    # REFERENCE DATA
    # ─────────────────────────────────────────────────────────────────────────

    def _seed_products(self):
        from apps.products.models import Product
        created, objs = 0, []
        for p in PRODUCTS:
            obj, new = Product.objects.get_or_create(
                sku=p['sku'],
                defaults=dict(
                    name=p['name'], brand=p['brand'],
                    category=p['category'], product_range=p['product_range'],
                    price=Decimal(str(p['price'])),
                    description=p.get('description', ''),
                    key_ingredients=p.get('key_ingredients', ''),
                    suitable_for_skin_types=p.get('suitable_for_skin_types', ['all']),
                    targets=[], shades_available=[], is_featured=created < 4,
                )
            )
            objs.append(obj)
            if new: created += 1
        self.stdout.write(f'  Products       : {created} created, {len(objs)-created} existed')
        return objs

    def _seed_skin_concerns(self):
        from apps.products.models import SkinConcern
        concerns_data = [
            dict(name='Acne',         slug='acne',         description='Pimples, blackheads, whiteheads', icon='🔴'),
            dict(name='Pigmentation', slug='pigmentation', description='Dark spots and uneven tone',       icon='🟤'),
            dict(name='Dryness',      slug='dryness',      description='Dehydration and flaking',          icon='💧'),
            dict(name='Aging',        slug='aging',        description='Fine lines and wrinkles',          icon='⏳'),
            dict(name='Dullness',     slug='dullness',     description='Lack of radiance and glow',        icon='⭐'),
        ]
        created, objs = 0, []
        for c in concerns_data:
            obj, new = SkinConcern.objects.get_or_create(slug=c['slug'], defaults=c)
            objs.append(obj)
            if new: created += 1
        self.stdout.write(f'  Skin Concerns  : {created} created, {len(objs)-created} existed')
        return objs

    def _seed_blog_categories(self):
        from apps.blog.models import BlogCategory
        created, objs = 0, []
        for c in BLOG_CATEGORIES:
            obj, new = BlogCategory.objects.get_or_create(slug=c['slug'], defaults=c)
            objs.append(obj)
            if new: created += 1
        self.stdout.write(f'  Blog Categories: {created} created, {len(objs)-created} existed')
        return {o.slug: o for o in objs}

    def _seed_habit_categories(self):
        from apps.diagnostic.models import HabitCategory
        created, objs = 0, []
        for c in HABIT_CATEGORIES:
            obj, new = HabitCategory.objects.get_or_create(slug=c['slug'], defaults=c)
            objs.append(obj)
            if new: created += 1
        self.stdout.write(f'  Habit Categories: {created} created, {len(objs)-created} existed')
        return objs

    def _seed_quick_prompts(self):
        from apps.chat.models import QuickPrompt
        created = 0
        for qp in QUICK_PROMPTS:
            _, new = QuickPrompt.objects.get_or_create(
                prompt_text=qp['prompt_text'],
                defaults=dict(category=qp['category'], order=qp['order'], active=True)
            )
            if new: created += 1
        self.stdout.write(f'  Quick Prompts  : {created} created')

    def _seed_coupons(self):
        from apps.coupons.models import Coupon
        coupons_data = [
            dict(code='LUMINA20',   coupon_type='percent', discount_value=20, description='20% off for all customers',
                 scope='all', min_order_value=500, max_uses=100, max_uses_per_user=1, is_active=True),
            dict(code='WELCOME50',  coupon_type='fixed',   discount_value=50, description='₹50 off on first order',
                 scope='all', min_order_value=300, max_uses=500, max_uses_per_user=1, is_active=True),
            dict(code='KBEAUTY15',  coupon_type='percent', discount_value=15, description='15% off on K-Beauty range',
                 scope='korean', min_order_value=800, max_uses=50, max_uses_per_user=2, is_active=True,
                 tier_required='medium'),
            dict(code='VIPDEAL30',  coupon_type='percent', discount_value=30, description='VIP exclusive 30% discount',
                 scope='all', min_order_value=1000, max_uses=20, max_uses_per_user=1, is_active=True,
                 tier_required='vip'),
        ]
        created = 0
        for c in coupons_data:
            _, new = Coupon.objects.get_or_create(
                code=c['code'],
                defaults={k: v for k, v in c.items() if k != 'code'}
            )
            if new: created += 1
        self.stdout.write(f'  Coupons        : {created} created')

    # ─────────────────────────────────────────────────────────────────────────
    # USERS
    # ─────────────────────────────────────────────────────────────────────────

    def _seed_admin(self):
        user, new = User.objects.get_or_create(
            username=ADMIN_USER['username'],
            defaults=dict(email=ADMIN_USER['email'], first_name=ADMIN_USER['first_name'],
                          last_name=ADMIN_USER['last_name'], is_staff=True, is_superuser=True)
        )
        if new:
            user.set_password(ADMIN_USER['password'])
            user.save()
        self.stdout.write(f'  Admin user     : {"created" if new else "exists"} ({user.username})')
        return user

    def _seed_employees(self, admin_user):
        from apps.memberships.models import UserProfile
        objs = []
        created = 0
        for e in EMPLOYEES:
            user, new = User.objects.get_or_create(
                username=e['username'],
                defaults=dict(first_name=e['first_name'], last_name=e['last_name'],
                              email=e['email'], is_staff=True, is_active=True)
            )
            if new:
                user.set_password(e['password'])
                user.save()
                created += 1
            # Ensure UserProfile exists (signals may create it)
            UserProfile.objects.get_or_create(
                user=user,
                defaults=dict(tier='normal', staff_role='admin' if 'manager' in e['designation'].lower() else 'marketing',
                              onboarding_complete=True)
            )
            objs.append((user, e))
        self.stdout.write(f'  Employees      : {created} created, {len(objs)-created} existed')
        return objs

    def _seed_customers(self):
        from apps.memberships.models import UserProfile
        objs = []
        created = 0
        for c in CUSTOMERS:
            user, new = User.objects.get_or_create(
                username=c['username'],
                defaults=dict(first_name=c['first_name'], last_name=c['last_name'],
                              email=c['email'], is_active=True)
            )
            if new:
                user.set_password(c['password'])
                user.save()
                created += 1
            UserProfile.objects.get_or_create(
                user=user,
                defaults=dict(tier=c['tier'], loyalty_points=random.randint(50, 800),
                              onboarding_complete=True)
            )
            objs.append((user, c))
        self.stdout.write(f'  Customers      : {created} created, {len(objs)-created} existed')
        return objs

    # ─────────────────────────────────────────────────────────────────────────
    # ADMIN PANEL DATA
    # ─────────────────────────────────────────────────────────────────────────

    def _seed_departments(self, admin_user, employees):
        from apps.admin_panel.models import Department, EmployeeProfile
        depts_data = [
            dict(name='Customer Care', code='CC',  description='Customer support and satisfaction'),
            dict(name='Sales',         code='SLS', description='Sales and revenue generation'),
            dict(name='Marketing',     code='MKT', description='Marketing and brand campaigns'),
            dict(name='Operations',    code='OPS', description='Day-to-day operations management'),
        ]
        depts = {}
        created = 0
        for d in depts_data:
            dept, new = Department.objects.get_or_create(name=d['name'], defaults=d)
            depts[d['name']] = dept
            if new: created += 1
        self.stdout.write(f'  Departments    : {created} created')

        # Create EmployeeProfiles
        ep_created = 0
        for (user, e_data) in employees:
            dept = depts.get(e_data.get('department'))
            _, new = EmployeeProfile.objects.get_or_create(
                user=user,
                defaults=dict(
                    department=dept,
                    designation=e_data.get('designation', 'Staff'),
                    joining_date=e_data.get('joining_date'),
                    status='active',
                    phone=e_data.get('phone', ''),
                    city=e_data.get('city', ''),
                    country='India',
                    shift='morning',
                    experience_years=random.randint(1, 6),
                )
            )
            if new: ep_created += 1
        self.stdout.write(f'  Emp Profiles   : {ep_created} created')

    def _seed_salary_and_leaves(self, employees, admin_user):
        from apps.admin_panel.models import SalaryRecord, EmployeeLeave
        now = timezone.now()
        sal_created = 0
        for (user, _) in employees:
            basic = Decimal(str(random.choice([25000, 35000, 45000, 55000])))
            for month_offset in range(3):  # last 3 months
            # compute month/year
                mo = (now.month - month_offset - 1) % 12 + 1
                yr = now.year if now.month - month_offset > 0 else now.year - 1
                _, new = SalaryRecord.objects.get_or_create(
                    employee=user, month=mo, year=yr,
                    defaults=dict(
                        basic_salary=basic,
                        hra=basic * Decimal('0.4'),
                        allowances=Decimal('3000'),
                        incentives=Decimal(str(random.randint(0, 5000))),
                        deductions=Decimal('2000'),
                        tax_deducted=basic * Decimal('0.05'),
                        net_salary=basic + basic * Decimal('0.4') + Decimal('3000') - Decimal('2000') - basic * Decimal('0.05'),
                        status='paid',
                        created_by=admin_user,
                    )
                )
                if new: sal_created += 1

        leave_reasons = [
            'Family function',
            'Medical appointment',
            'Personal work',
            'Sick – fever and cold',
        ]
        leave_created = 0
        for (user, _) in employees:
            if EmployeeLeave.objects.filter(employee=user).exists():
                continue
            for i in range(2):
                from_d = date.today() - timedelta(days=random.randint(5, 40))
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
        self.stdout.write(f'  Salary Records : {sal_created} created')
        self.stdout.write(f'  Leave Records  : {leave_created} created')

    def _seed_admin_tasks(self, admin_user, employees):
        from apps.admin_panel.models import AdminTask
        if AdminTask.objects.exists():
            self.stdout.write('  Admin Tasks    : already seeded')
            return
        tasks = [
            dict(title='Review Q3 marketing campaign results', priority='high',   status='in_progress',
                 description='Analyse conversion rates, leads generated, and ROI for Q3 campaigns.'),
            dict(title='Update product catalogue with new K-Beauty arrivals', priority='medium', status='todo',
                 description='Add 15 new COSRX and Innisfree products with correct SKUs and images.'),
            dict(title='Onboard 2 new support agents', priority='high',   status='todo',
                 description='Prepare training documents and system access for new hires.'),
            dict(title='Monthly salary processing — June 2025', priority='urgent', status='done',
                 description='Process all employee salaries and upload bank transfer receipts.'),
        ]
        for i, t in enumerate(tasks):
            assigned = employees[i % len(employees)][0] if employees else admin_user
            AdminTask.objects.create(
                title=t['title'], description=t['description'],
                priority=t['priority'], status=t['status'],
                assigned_to=assigned, created_by=admin_user,
                due_date=date.today() + timedelta(days=random.randint(2, 14)),
            )
        self.stdout.write(f'  Admin Tasks    : {len(tasks)} created')

    def _seed_company_settings(self):
        from apps.admin_panel.models import CompanySettings
        if CompanySettings.objects.exists():
            self.stdout.write('  Company Settings: already exists')
            return
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

    def _seed_admin_activity(self, admin_user, employees):
        from apps.admin_panel.models import AdminActivity
        if AdminActivity.objects.exists():
            self.stdout.write('  Admin Activity : already seeded')
            return
        activities = [
            dict(action='login',  module='auth',      description='Admin logged in from Bangalore'),
            dict(action='create', module='employees', description='Created new employee: priya_emp'),
            dict(action='update', module='orders',    description='Updated order OD260621 status to Shipped'),
            dict(action='approve',module='leaves',    description='Approved casual leave for rahul_emp'),
            dict(action='export', module='reports',   description='Exported monthly sales report PDF'),
        ]
        for a in activities:
            AdminActivity.objects.create(
                admin=admin_user, action=a['action'], module=a['module'],
                description=a['description'], ip_address='103.21.58.14',
            )
        self.stdout.write(f'  Admin Activity : {len(activities)} created')

    # ─────────────────────────────────────────────────────────────────────────
    # CUSTOMER DATA
    # ─────────────────────────────────────────────────────────────────────────

    def _seed_orders(self, customers, products):
        from apps.orders.models import Order, OrderItem, OrderStatusLog
        count = 0
        statuses = ['delivered', 'delivered', 'shipped', 'confirmed', 'cancelled']
        payment_methods = ['upi', 'card', 'cod', 'upi']

        for (user, c_data) in customers:
            if Order.objects.filter(user=user).exists():
                continue
            addr = random.choice(ADDRESSES)
            for _ in range(random.randint(2, 4)):
                status  = random.choice(statuses)
                payment = random.choice(payment_methods)
                order = Order.objects.create(
                    user=user,
                    full_name=f'{user.first_name} {user.last_name}',
                    phone=c_data['phone'],
                    email=user.email,
                    address_line1=addr['address_line1'],
                    city=addr['city'], state=addr['state'], pincode=addr['pincode'],
                    payment_method=payment,
                    payment_status='paid' if payment != 'cod' else 'pending',
                    status=status,
                    delivery_charge=Decimal('0') if random.random() > 0.3 else Decimal('49'),
                    discount=Decimal(str(random.choice([0, 0, 50, 100]))),
                    estimated_delivery=date.today() + timedelta(days=random.randint(2, 7)),
                )
                chosen = random.sample(products, k=random.randint(1, 3))
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
                    'delivered': [('confirmed', 'Payment confirmed', addr['city']),
                                  ('shipped',   'Shipped via Delhivery', 'Mumbai Hub'),
                                  ('delivered', 'Package delivered', addr['city'])],
                    'shipped':   [('confirmed', 'Payment confirmed', addr['city']),
                                  ('shipped',   'In transit', 'Mumbai Hub')],
                    'confirmed': [('confirmed', 'Order placed and confirmed', addr['city'])],
                    'cancelled': [('pending',   'Order placed', addr['city']),
                                  ('cancelled', 'Cancelled by customer', addr['city'])],
                }
                for s, msg, loc in flow.get(status, [('pending', 'Order placed', addr['city'])]):
                    OrderStatusLog.objects.create(order=order, status=s, message=msg, location=loc)
                count += 1
        self.stdout.write(f'  Orders         : {count} created')

    def _seed_blog_posts(self, blog_cats, admin_user):
        from apps.blog.models import BlogPost
        created = 0
        for p in BLOG_POSTS:
            cat = blog_cats.get(p['category_slug'])
            _, new = BlogPost.objects.get_or_create(
                slug=p['slug'],
                defaults=dict(
                    title=p['title'], category=cat, excerpt=p['excerpt'],
                    content=p['content'], status=p['status'],
                    is_featured=p.get('is_featured', False),
                    reading_time=p.get('reading_time', 5),
                    author=admin_user,
                    author_name='Lumina Team',
                    published_at=timezone.now() - timedelta(days=random.randint(1, 30)),
                    tags='skincare,beauty,skin,tips',
                    view_count=random.randint(50, 800),
                )
            )
            if new: created += 1
        self.stdout.write(f'  Blog Posts     : {created} created')

    def _seed_notifications(self, customers):
        from apps.notifications.models import Notification
        notif_data = [
            dict(notif_type='tier_upgrade',     title='You\'ve been upgraded to VIP!',
                 message='Congratulations! Your loyalty points have unlocked VIP tier benefits.', icon='🌟'),
            dict(notif_type='scan_reminder',    title='Time for your Day-30 Scan',
                 message='It\'s been 30 days since your first scan. Take a new scan to see your progress!', icon='📸'),
            dict(notif_type='points_earned',    title='You earned 150 points!',
                 message='You earned 150 loyalty points for completing your weekly check-in.', icon='⭐'),
            dict(notif_type='routine_reminder', title='Don\'t forget your night routine!',
                 message='Completing your PM routine earns you 10 points. Keep the streak going!', icon='🌙'),
        ]
        created = 0
        for (user, _) in customers:
            if user.notifications.exists():
                continue
            for nd in notif_data[:random.randint(2, 4)]:
                Notification.objects.create(user=user, **nd, is_read=random.choice([True, False]))
                created += 1
        self.stdout.write(f'  Notifications  : {created} created')

    def _seed_habit_logs(self, customers, habit_cats):
        from apps.diagnostic.models import HabitLog
        created = 0
        for (user, _) in customers:
            if HabitLog.objects.filter(user=user).exists():
                continue
            for i in range(random.randint(3, 6)):
                habit = random.choice(habit_cats)
                HabitLog.objects.create(
                    user=user, habit=habit,
                    points_earned=habit.points,
                    notes='',
                )
                created += 1
        self.stdout.write(f'  Habit Logs     : {created} created')

    def _seed_diagnostic_sessions(self, customers):
        from apps.diagnostic.models import DiagnosticSession, SmartDiagSession
        created = 0
        skin_types = ['oily', 'dry', 'combination', 'normal', 'sensitive']
        concerns   = ['acne', 'pigmentation', 'dryness', 'aging', 'dullness']
        for (user, _) in customers:
            if DiagnosticSession.objects.filter(user=user).exists():
                continue
            DiagnosticSession.objects.create(
                user=user,
                selected_categories=random.sample(concerns, k=2),
                skin_type=random.choice(skin_types),
                concern_1=random.choice(concerns),
                concern_2=random.choice(concerns),
                budget=random.choice(['low', 'mid', 'high']),
                water_intake=random.randint(3, 9),
                sleep_hours=random.randint(5, 8),
                stress_level=random.randint(3, 8),
                recommended_tier=random.choice(['normal', 'medium', 'vip']),
                completed=True,
            )
            SmartDiagSession.objects.create(
                user=user,
                primary_goal=random.choice(['glow', 'acne', 'aging', 'hydration']),
                answers={'skin_type': random.choice(skin_types), 'concerns': random.sample(concerns, 2)},
                analysis={'severity': 'mild', 'recommendations': ['niacinamide', 'spf50', 'gentle cleanser']},
                severity=random.choice(['minimal', 'mild', 'moderate']),
                top_concern_cat=random.choice(concerns),
                completed=True,
            )
            created += 2
        self.stdout.write(f'  Diag Sessions  : {created} created')

    def _seed_leads(self, employees, customers):
        from apps.employee.models import Lead
        if Lead.objects.exists():
            self.stdout.write('  CRM Leads      : already seeded')
            return
        leads_data = [
            dict(name='Pooja Nair',    phone='9012345678', email='pooja@gmail.com',    city='Kochi',
                 source='instagram', stage='interested',     skin_concern='Acne and pigmentation'),
            dict(name='Sakshi Gupta',  phone='9112233445', email='sakshi@yahoo.com',   city='Jaipur',
                 source='website',   stage='product_shared', skin_concern='Dry skin and anti-aging'),
            dict(name='Tanu Sharma',   phone='9223344556', email='tanu@gmail.com',     city='Chandigarh',
                 source='referral',  stage='new',             skin_concern='Oily skin and large pores'),
            dict(name='Anita Bose',    phone='9334455667', email='anita@outlook.com',  city='Kolkata',
                 source='facebook',  stage='contacted',       skin_concern='Dark circles and dullness'),
        ]
        emp_users = [u for (u, _) in employees]
        for ld in leads_data:
            Lead.objects.create(
                **ld,
                budget=random.choice(['500-1000', '1000-2500', '2500+']),
                assigned_to=random.choice(emp_users),
                created_by=emp_users[0],
                follow_up_date=date.today() + timedelta(days=random.randint(1, 7)),
            )
        self.stdout.write(f'  CRM Leads      : {len(leads_data)} created')

    def _seed_support_tickets(self, customers, employees, products):
        from apps.employee.models import SupportTicket, TicketReply
        if SupportTicket.objects.exists():
            self.stdout.write('  Support Tickets: already seeded')
            return
        tickets_data = [
            dict(subject='My order has not arrived after 10 days',
                 description='I placed order OD001 on June 1st. The tracking shows it\'s in transit but nothing received.',
                 channel='chat', priority='high', status='open'),
            dict(subject='Wrong shade of foundation sent',
                 description='I ordered Maybelline Fit Me in Shade 220, but received Shade 120. Please help.',
                 channel='email', priority='medium', status='in_progress'),
            dict(subject='How do I track my daily routine streak?',
                 description='I can see the habit log section but I\'m not sure how to view my streak history.',
                 channel='portal', priority='low', status='resolved'),
            dict(subject='Coupon code LUMINA20 is not working at checkout',
                 description='I tried applying LUMINA20 but it says "invalid or expired". My cart total is ₹850.',
                 channel='whatsapp', priority='medium', status='open'),
        ]
        emp_users = [u for (u, _) in employees]
        for i, td in enumerate(tickets_data):
            cust_user, c_data = customers[i % len(customers)]
            ticket = SupportTicket.objects.create(
                customer=cust_user,
                customer_name=f'{cust_user.first_name} {cust_user.last_name}',
                customer_email=cust_user.email,
                customer_phone=c_data['phone'],
                assigned_to=emp_users[i % len(emp_users)],
                resolution='Issue being investigated.' if td['status'] == 'in_progress' else '',
                **td,
            )
            TicketReply.objects.create(
                ticket=ticket,
                author=emp_users[i % len(emp_users)],
                message='Thank you for reaching out! We\'re looking into this and will update you within 24 hours.',
                is_internal=False,
            )
        self.stdout.write(f'  Support Tickets: {len(tickets_data)} created with replies')

    def _seed_attendance(self, employees, admin_user):
        from apps.employee.models import EmployeeAttendance
        created = 0
        statuses = ['present', 'present', 'present', 'present', 'half', 'wfh']
        for (user, _) in employees:
            for day_offset in range(1, 8):  # last 7 days
                day = date.today() - timedelta(days=day_offset)
                if day.weekday() >= 5:  # skip weekends
                    continue
                _, new = EmployeeAttendance.objects.get_or_create(
                    employee=user, date=day,
                    defaults=dict(
                        status=random.choice(statuses),
                        check_in=dtime(9, random.randint(0, 30)),
                        check_out=dtime(18, random.randint(0, 30)),
                        marked_by=admin_user,
                    )
                )
                if new: created += 1
        self.stdout.write(f'  Attendance     : {created} records created')

    def _seed_sales_targets(self, employees):
        from apps.employee.models import SalesTarget
        created = 0
        for (user, _) in employees:
            for day_offset in range(7):
                day = date.today() - timedelta(days=day_offset)
                if day.weekday() >= 5:
                    continue
                target = Decimal(str(random.choice([10000, 15000, 20000])))
                achieved = target * Decimal(str(round(random.uniform(0.5, 1.2), 2)))
                _, new = SalesTarget.objects.get_or_create(
                    employee=user, date=day,
                    defaults=dict(target=target, achieved=achieved.quantize(Decimal('0.01')))
                )
                if new: created += 1
        self.stdout.write(f'  Sales Targets  : {created} records created')

    def _seed_progress_logs(self, customers):
        from apps.progress.models import DailyRoutineLog, WeeklyCheckin
        d_created, w_created = 0, 0
        for (user, _) in customers:
            # Daily logs — last 5 days
            for day_offset in range(1, 6):
                day = date.today() - timedelta(days=day_offset)
                _, new = DailyRoutineLog.objects.get_or_create(
                    user=user, log_date=day,
                    defaults=dict(
                        am_done=random.choice([True, True, False]),
                        pm_done=random.choice([True, False]),
                        water_glasses=random.randint(4, 10),
                        spf_applied=random.choice([True, True, False]),
                        skin_rating=random.randint(3, 5),
                    )
                )
                if new: d_created += 1

            # Weekly check-in
            _, new = WeeklyCheckin.objects.get_or_create(
                user=user, week_number=1,
                defaults=dict(
                    week_start=date.today() - timedelta(days=7),
                    overall_rating=random.randint(3, 5),
                    hydration_rating=random.randint(3, 5),
                    acne_rating=random.randint(3, 5),
                    brightness_rating=random.randint(3, 5),
                    products_used=['COSRX Snail Mucin', 'Laneige Mask', 'SPF 50'],
                    new_concerns='Slight dryness on cheeks',
                    has_selfie=False,
                )
            )
            if new: w_created += 1

        self.stdout.write(f'  Progress Logs  : {d_created} daily, {w_created} weekly created')
