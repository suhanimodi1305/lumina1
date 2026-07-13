"""
Management command: python manage.py seed_crm_data

Seeds realistic demo data for:
  - CRM Opportunities (linked to existing Leads)
  - Call Logs (inbound, outbound, follow-ups)
  - Callback Requests (customer-initiated)
  - Marketing Campaigns
  - Internal Notes
  - Sales Targets
"""
import random
from datetime import timedelta, date, time

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from apps.employee.models import (
    Lead, Opportunity, CallLog, CallbackRequest,
    Campaign, InternalNote, SalesTarget, EmployeeAttendance,
)


# ── Data pools ────────────────────────────────────────────────────────────────

OPPORTUNITY_TITLES = [
    "Korean Skincare Starter Kit Bundle",
    "VIP Membership Upgrade - Annual Plan",
    "Bridal Skincare Package",
    "Anti-Aging Routine Consultation",
    "Custom Foundation Shade Matching",
    "Bulk Order - Office Gift Hampers",
    "Monthly Skincare Subscription",
    "Pigmentation Treatment Kit",
    "Hydration & Glow Pack (Summer)",
    "Men's Skincare Essentials Bundle",
    "Teen Acne Care Package",
    "Luxury Korean Spa Kit",
    "Sensitive Skin Protocol Package",
    "Maternity Safe Skincare Bundle",
]

CUSTOMER_NAMES = [
    "Aanya Kapoor", "Meera Singh", "Divya Rao", "Kavya Mehta", "Riya Joshi",
    "Preethi Nair", "Ananya Gupta", "Sonali Bose", "Nisha Verma", "Pooja Reddy",
    "Shweta Malhotra", "Deepika Iyer", "Sunita Jain", "Madhuri Das", "Leela Pillai",
    "Ramesh Kumar", "Vikram Shah", "Arjun Patel", "Nikhil Sharma", "Rohit Aggarwal",
]

PHONES = [
    "9876543210", "9845012345", "9123456780", "8765432109", "7890123456",
    "9988776655", "8877665544", "9900112233", "9012345678", "8901234567",
    "9811223344", "9922334455", "8833445566", "7744556677", "9654321098",
]

CALL_NOTES = [
    "Customer interested in Korean skincare. Requested product recommendations.",
    "Discussed hydration routine. Interested in Laneige Water Sleeping Mask.",
    "Follow-up on previous inquiry. Will place order this weekend.",
    "Complaint about delayed delivery — escalated to logistics team.",
    "Customer wanted to understand VIP membership benefits.",
    "Interested in anti-ageing products. Sent catalogue link via WhatsApp.",
    "Requested refund for damaged product. Raised ticket.",
    "New inquiry from Instagram DM. Skin type: oily, concern: acne.",
    "Converted! Customer placed order for ₹2,450 bridal kit.",
    "No answer. Will retry tomorrow morning.",
    "Customer happy with recent purchase. Upsold monthly subscription.",
    "Wrong number. Removed from list.",
    "Discussed budget constraints. Will call back next week.",
    "Customer referred by existing VIP member Meera Singh.",
    "Asked about ingredients — emailed full INCI list.",
]

ISSUE_SUMMARIES = [
    "Order not delivered after 7 days",
    "Wrong shade of foundation received",
    "Allergic reaction to COSRX serum",
    "Discount code not applied at checkout",
    "Want to know tracking number for order #LX2024",
    "Requesting callback for VIP membership inquiry",
    "Product seems expired — want to return",
    "Payment deducted but order not confirmed",
    "Want recommendation for oily skin routine",
    "Need help with skin quiz results",
]

CAMPAIGN_DATA = [
    dict(name="Monsoon Hydration Sale", type="email",
         description="Exclusive email blast for monsoon skincare essentials — 20% off hydration range.",
         target_audience="All registered users", budget=15000,
         leads_generated=142, conversions=38, revenue=87400, status="completed"),
    dict(name="Diwali Gifting Hampers - WhatsApp", type="whatsapp",
         description="WhatsApp broadcast to top 500 customers about Diwali gift hampers.",
         target_audience="VIP & PLUS members", budget=8000,
         leads_generated=89, conversions=22, revenue=64800, status="completed"),
    dict(name="New User Welcome SMS", type="sms",
         description="Automated SMS with 15% first-purchase coupon for new registrations.",
         target_audience="New signups last 30 days", budget=3500,
         leads_generated=210, conversions=67, revenue=45200, status="active"),
    dict(name="Instagram Influencer - GRWM Campaign", type="influencer",
         description="Partnering with 3 micro-influencers (50k-200k) for Get Ready With Me posts.",
         target_audience="18-35 women, skincare interested", budget=45000,
         leads_generated=320, conversions=78, revenue=142600, status="completed"),
    dict(name="Referral Rewards Program", type="referral",
         description="Refer a friend and earn 500 loyalty points. Friend gets 10% off first order.",
         target_audience="Existing members", budget=5000,
         leads_generated=55, conversions=31, revenue=38900, status="active"),
    dict(name="Summer Glow Push Campaign", type="push",
         description="Push notification series — 5 messages over 2 weeks for summer skincare.",
         target_audience="App users, last active 30 days", budget=2000,
         leads_generated=198, conversions=44, revenue=29800, status="completed"),
    dict(name="Acne Care Awareness - Oct", type="email",
         description="Educational email series on acne: causes, ingredients, routine.",
         target_audience="Oily/combination skin segment", budget=6000,
         leads_generated=0, conversions=0, revenue=0, status="draft"),
    dict(name="Year-End Mega Sale Campaign", type="email",
         description="Dec 26-31 clearance sale. Up to 40% off on all products.",
         target_audience="All users", budget=20000,
         leads_generated=0, conversions=0, revenue=0, status="scheduled"),
]

NOTE_CONTENTS = [
    "Lead called back — confirmed interested in bridal package. Follow up Friday.",
    "Order ORD-24 delivered but customer reported broken seal. Replacement dispatched.",
    "VIP member Meera Singh referred 3 new customers this week. Add referral bonus.",
    "Priya closed 2 deals today — Korean starter kit and monthly sub. Great day!",
    "Stock alert: COSRX Snail Mucin running low — only 8 units left.",
    "Customer Kavya Mehta wants to return foundation — wrong shade. Initiating refund.",
    "Campaign click rates: Email 28%, WhatsApp 61%, SMS 14%.",
    "New bulk inquiry from corporate: 50 gift hampers for Diwali. Escalated to Rahul.",
    "Skin quiz flow updated — now asks about diet and water intake. Test before launch.",
    "Sneha trained on new CRM lead scoring today — ready to take over lead management.",
]


class Command(BaseCommand):
    help = 'Seeds demo CRM data: Opportunities, Calls, Callbacks, Campaigns, Notes, Targets'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true',
                            help='Clear existing CRM demo data before seeding')

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\n── Lumina CRM Data Seeder ──\n'))

        if options.get('clear'):
            self._clear_data()

        # Get staff users
        staff = list(User.objects.filter(is_staff=True))
        if not staff:
            self.stdout.write(self.style.ERROR(
                'No staff users found. Run seed_demo_data first.'
            ))
            return

        # Get or create a few leads to link to
        leads = list(Lead.objects.all())
        if not leads:
            leads = self._create_sample_leads(staff)

        self._seed_opportunities(leads, staff)
        self._seed_call_logs(staff, leads)
        self._seed_callbacks()
        self._seed_campaigns(staff)
        self._seed_notes(staff, leads)
        self._seed_sales_targets(staff)
        self._seed_attendance(staff)

        self.stdout.write(self.style.SUCCESS('\n✓ CRM demo data seeded successfully!\n'))
        self.stdout.write('  Login with any staff user (password: Lumina@2024)')

    # ── Clear ─────────────────────────────────────────────────────────────────

    def _clear_data(self):
        Opportunity.objects.all().delete()
        CallLog.objects.all().delete()
        CallbackRequest.objects.all().delete()
        Campaign.objects.all().delete()
        InternalNote.objects.all().delete()
        SalesTarget.objects.all().delete()
        self.stdout.write('  Cleared existing CRM data.')

    # ── Sample Leads ──────────────────────────────────────────────────────────

    def _create_sample_leads(self, staff):
        lead_data = [
            dict(name="Ananya Gupta",   phone="9876543210", email="ananya@gmail.com",
                 source="instagram", stage="interested", skin_concern="acne, oily skin",
                 city="Mumbai", budget="1000-2000"),
            dict(name="Sunita Jain",    phone="9845678901", email="sunita@hotmail.com",
                 source="referral",  stage="product_shared", skin_concern="pigmentation",
                 city="Delhi", budget="2000-3000"),
            dict(name="Vikram Shah",    phone="9123456789", email="vikram@outlook.com",
                 source="website",   stage="new", skin_concern="dry skin",
                 city="Bangalore", budget="500-1000"),
            dict(name="Preethi Nair",   phone="8765432109", email="preethi@gmail.com",
                 source="whatsapp",  stage="negotiation", skin_concern="anti-ageing",
                 city="Chennai", budget="3000-5000"),
            dict(name="Rohit Aggarwal", phone="7890123456", email="rohit@yahoo.com",
                 source="cold_call", stage="contacted", skin_concern="dark circles",
                 city="Hyderabad", budget="1500-2500"),
        ]
        leads = []
        created = 0
        for d in lead_data:
            lead, new = Lead.objects.get_or_create(
                phone=d['phone'],
                defaults=dict(
                    name=d['name'], email=d['email'],
                    source=d['source'], stage=d['stage'],
                    skin_concern=d['skin_concern'], city=d['city'],
                    budget=d['budget'],
                    assigned_to=random.choice(staff),
                    created_by=random.choice(staff),
                    follow_up_date=date.today() + timedelta(days=random.randint(1, 7)),
                )
            )
            leads.append(lead)
            if new:
                created += 1
        self.stdout.write(f'  Leads     : {created} created')
        return leads

    # ── Opportunities ─────────────────────────────────────────────────────────

    def _seed_opportunities(self, leads, staff):
        if Opportunity.objects.count() > 5:
            self.stdout.write('  Opps      : already have data, skipping')
            return

        stages = [s[0] for s in Opportunity.STAGE_CHOICES]
        created = 0
        now = timezone.now()

        for i, title in enumerate(OPPORTUNITY_TITLES):
            lead = leads[i % len(leads)]
            stage = stages[i % len(stages)]
            value = random.choice([999, 1500, 2450, 3200, 4800, 6500, 9800, 12000])
            prob  = random.choice([20, 35, 50, 65, 75, 85, 90])
            close_offset = random.randint(7, 45)

            opp = Opportunity(
                lead=lead,
                title=title,
                stage=stage,
                value=value,
                probability=prob,
                assigned_to=random.choice(staff),
                close_date=date.today() + timedelta(days=close_offset),
                notes=f"Opportunity created from lead {lead.lead_id}. "
                      f"Customer expressed interest in {title.lower()}.",
            )
            opp.save()

            # Backdate created_at
            days_ago = random.randint(1, 30)
            Opportunity.objects.filter(pk=opp.pk).update(
                created_at=now - timedelta(days=days_ago)
            )
            created += 1

        self.stdout.write(f'  Opps      : {created} created')

    # ── Call Logs ─────────────────────────────────────────────────────────────

    def _seed_call_logs(self, staff, leads):
        if CallLog.objects.count() > 10:
            self.stdout.write('  Calls     : already have data, skipping')
            return

        directions = [d[0] for d in CallLog.DIRECTION_CHOICES]
        statuses   = [s[0] for s in CallLog.CALL_STATUS_CHOICES]
        now = timezone.now()
        created = 0

        for i in range(40):
            emp    = random.choice(staff)
            lead   = random.choice(leads) if random.random() > 0.3 else None
            direction = random.choice(directions)
            status    = random.choice(statuses)
            name      = lead.name if lead else random.choice(CUSTOMER_NAMES)
            phone     = lead.phone if lead else random.choice(PHONES)

            # More connected calls than no-answer
            if status in ['no_answer', 'busy', 'wrong_number']:
                duration = 0
            else:
                duration = random.randint(30, 840)

            days_ago    = random.randint(0, 30)
            hours_ago   = random.randint(0, 23)
            called_time = now - timedelta(days=days_ago, hours=hours_ago,
                                          minutes=random.randint(0, 59))

            follow_up = None
            if status in ['interested', 'callback_requested'] and random.random() > 0.4:
                follow_up = date.today() + timedelta(days=random.randint(1, 5))

            call = CallLog(
                employee=emp,
                lead=lead,
                customer_name=name,
                phone=phone,
                direction=direction,
                status=status,
                duration_seconds=duration,
                notes=random.choice(CALL_NOTES),
                follow_up_date=follow_up,
                called_at=called_time,
            )
            call.save()
            created += 1

        self.stdout.write(f'  Call logs : {created} created')

    # ── Callback Requests ─────────────────────────────────────────────────────

    def _seed_callbacks(self):
        if CallbackRequest.objects.count() > 3:
            self.stdout.write('  Callbacks : already have data, skipping')
            return

        statuses = ['pending', 'pending', 'pending', 'assigned', 'called', 'resolved']
        times    = ['Morning 9-11 AM', 'Afternoon 2-4 PM', 'Evening 6-8 PM',
                    'Anytime', 'After 7 PM', 'Morning only']
        now = timezone.now()
        created = 0

        for i in range(12):
            name  = CUSTOMER_NAMES[i % len(CUSTOMER_NAMES)]
            phone = PHONES[i % len(PHONES)]
            status = random.choice(statuses)
            is_resolved = status == 'resolved'

            cb = CallbackRequest(
                name=name,
                phone=phone,
                email=f"{name.split()[0].lower()}@gmail.com",
                issue_summary=ISSUE_SUMMARIES[i % len(ISSUE_SUMMARIES)],
                preferred_time=random.choice(times),
                status=status,
                is_resolved=is_resolved,
                resolved_at=now - timedelta(hours=random.randint(1, 24)) if is_resolved else None,
            )
            cb.save()

            # Backdate created_at
            hours_back = random.randint(1, 72)
            CallbackRequest.objects.filter(pk=cb.pk).update(
                created_at=now - timedelta(hours=hours_back)
            )
            created += 1

        self.stdout.write(f'  Callbacks : {created} created')

    # ── Campaigns ─────────────────────────────────────────────────────────────

    def _seed_campaigns(self, staff):
        if Campaign.objects.count() > 2:
            self.stdout.write('  Campaigns : already have data, skipping')
            return

        now = timezone.now()
        created = 0

        for i, data in enumerate(CAMPAIGN_DATA):
            camp = Campaign(
                name=data['name'],
                type=data['type'],
                description=data['description'],
                target_audience=data['target_audience'],
                budget=data['budget'],
                spent=int(data['budget'] * random.uniform(0.6, 1.1)) if data['status'] not in ('draft', 'scheduled') else 0,
                status=data['status'],
                leads_generated=data['leads_generated'],
                conversions=data['conversions'],
                revenue=data['revenue'],
                created_by=random.choice(staff),
            )
            if data['status'] == 'scheduled':
                camp.scheduled_at = now + timedelta(days=random.randint(5, 20))
            elif data['status'] in ('active', 'completed'):
                camp.started_at = now - timedelta(days=random.randint(5, 30))
            if data['status'] == 'completed':
                camp.ended_at = now - timedelta(days=random.randint(1, 10))

            camp.save()

            # Backdate created_at
            days_ago = random.randint(5, 60)
            Campaign.objects.filter(pk=camp.pk).update(
                created_at=now - timedelta(days=days_ago)
            )
            created += 1

        self.stdout.write(f'  Campaigns : {created} created')

    # ── Internal Notes ────────────────────────────────────────────────────────

    def _seed_notes(self, staff, leads):
        if InternalNote.objects.count() > 5:
            self.stdout.write('  Notes     : already have data, skipping')
            return

        tags = [t[0] for t in InternalNote.TAG_CHOICES]
        now  = timezone.now()
        created = 0

        for i, content in enumerate(NOTE_CONTENTS):
            note = InternalNote(
                author=random.choice(staff),
                content=content,
                tag=random.choice(tags),
                lead=leads[i % len(leads)] if i % 3 == 0 else None,
            )
            note.save()
            hours_ago = random.randint(1, 168)  # up to 1 week
            InternalNote.objects.filter(pk=note.pk).update(
                created_at=now - timedelta(hours=hours_ago)
            )
            created += 1

        self.stdout.write(f'  Notes     : {created} created')

    # ── Sales Targets ─────────────────────────────────────────────────────────

    def _seed_sales_targets(self, staff):
        today = date.today()
        created = 0
        for emp in staff:
            for days_back in range(7):
                target_date = today - timedelta(days=days_back)
                target_val  = random.choice([15000, 20000, 25000, 30000])
                # Today: partial achievement
                if days_back == 0:
                    achieved = int(target_val * random.uniform(0.2, 0.75))
                else:
                    achieved = int(target_val * random.uniform(0.5, 1.15))

                SalesTarget.objects.get_or_create(
                    employee=emp, date=target_date,
                    defaults=dict(target=target_val, achieved=achieved)
                )
                created += 1

        self.stdout.write(f'  Targets   : {created} records created/ensured')

    # ── Attendance ────────────────────────────────────────────────────────────

    def _seed_attendance(self, staff):
        today = date.today()
        statuses = ['present', 'present', 'present', 'present', 'half', 'wfh', 'absent']
        created = 0
        for emp in staff:
            for days_back in range(30):
                att_date = today - timedelta(days=days_back)
                # Skip weekends
                if att_date.weekday() >= 5:
                    continue
                status = random.choice(statuses)
                check_in = time(
                    random.randint(9, 10),
                    random.choice([0, 15, 30, 45])
                ) if status in ('present', 'half', 'wfh') else None
                check_out = time(
                    random.randint(17, 19),
                    random.choice([0, 15, 30])
                ) if status == 'present' else None

                _, new = EmployeeAttendance.objects.get_or_create(
                    employee=emp, date=att_date,
                    defaults=dict(
                        status=status,
                        check_in=check_in,
                        check_out=check_out,
                        marked_by=emp,
                    )
                )
                if new:
                    created += 1

        self.stdout.write(f'  Attendance: {created} records created')
