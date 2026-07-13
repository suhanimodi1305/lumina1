"""
Diagnostic app views — Wizard, Result, Marketing Portal, Admin Panel, Log & Earn
"""
import json
import uuid
from datetime import date, timedelta

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.memberships.models import UserProfile
from apps.products.models import Product
from .models import DiagnosticSession, HabitCategory, HabitLog, ReferralClick


# ── helpers ──────────────────────────────────────────────────────────────────

CATEGORIES = [
    {'value': 'makeup',    'label': 'Makeup',             'icon': '💄',
     'desc': 'Foundation, lipstick, eye looks'},
    {'value': 'korean',    'label': 'Korean Skincare',    'icon': '🧴',
     'desc': 'Glass skin, K-beauty routines'},
    {'value': 'ayurvedic', 'label': 'Ayurvedic',          'icon': '🌿',
     'desc': 'Herbal & natural wellness'},
    {'value': 'pharmacy',  'label': 'Pharmacy / Clinical','icon': '🧪',
     'desc': 'OTC treatments & derma-grade'},
]

SKIN_TYPES = [
    {'value': 'oily',        'label': 'Oily',        'icon': '💦'},
    {'value': 'dry',         'label': 'Dry',         'icon': '🏜️'},
    {'value': 'combination', 'label': 'Combination', 'icon': '☯️'},
    {'value': 'normal',      'label': 'Normal',      'icon': '✅'},
]


def _compute_tier(budget, water, sleep, stress):
    """Simple rule-based tier recommendation."""
    if budget == 'high' and water >= 7 and sleep >= 7:
        return 'vip'
    if budget == 'mid' or (4 <= water <= 7):
        return 'medium'
    return 'normal'


def _staff_or_marketing(user):
    if user.is_staff or user.is_superuser:
        return True
    try:
        return user.profile.staff_role in ('marketing', 'admin')
    except Exception:
        return False


def _get_or_create_session(request):
    """Return existing DiagnosticSession from Django session or create new."""
    sid = request.session.get('diag_session_id')
    if sid:
        try:
            return DiagnosticSession.objects.get(id=sid)
        except DiagnosticSession.DoesNotExist:
            pass
    sess = DiagnosticSession.objects.create(
        user=request.user if request.user.is_authenticated else None,
        session_key=request.session.session_key or '',
    )
    request.session['diag_session_id'] = str(sess.id)
    return sess


# ── WIZARD ───────────────────────────────────────────────────────────────────

def wizard(request):
    """Redirect to the new AI Consultation flow."""
    return redirect('skin:start')


def quiz(request):
    """Page 2 — questions (skin profile + lifestyle). Receives categories via GET."""
    # If somehow accessed directly without categories, restart
    cats = request.GET.getlist('categories')
    session_id = request.GET.get('session_id', '')

    if not cats or not session_id:
        return redirect('diagnostic:wizard')

    # Validate session exists
    try:
        sess = DiagnosticSession.objects.get(id=session_id)
    except (DiagnosticSession.DoesNotExist, Exception):
        return redirect('diagnostic:wizard')

    # Save selected categories to session model early
    sess.selected_categories = cats
    sess.save(update_fields=['selected_categories'])

    return render(request, 'diagnostic/quiz.html', {
        'session_id': session_id,
        'selected_categories': cats,
        'skin_types': SKIN_TYPES,
        'categories': CATEGORIES,
    })


def wizard_step(request):
    """POST — receives all wizard data and computes result."""
    if request.method != 'POST':
        return redirect('diagnostic:wizard')

    sess = _get_or_create_session(request)

    # Parse step data
    cats   = request.POST.getlist('categories')
    skin   = request.POST.get('skin_type', 'normal')
    concern = request.POST.get('primary_concern', '')
    budget = request.POST.get('budget', 'low')
    water  = int(request.POST.get('water_intake', 5))
    sleep  = int(request.POST.get('sleep_hours', 6))
    stress = int(request.POST.get('stress_level', 5))

    # Save to session model
    sess.selected_categories = cats
    sess.skin_type   = skin
    sess.concern_1   = concern
    sess.budget      = budget
    sess.water_intake = water
    sess.sleep_hours  = sleep
    sess.stress_level = stress
    sess.recommended_tier = _compute_tier(budget, water, sleep, stress)
    sess.completed = True
    sess.save()

    # Mark referral as converted if applicable
    ref = request.session.get('diag_ref', '')
    if ref:
        ReferralClick.objects.filter(referral_code=ref, converted=False).update(converted=True)

    return redirect('diagnostic:result', session_id=sess.id)


# ── RESULT ────────────────────────────────────────────────────────────────────

def result(request, session_id):
    sess = get_object_or_404(DiagnosticSession, id=session_id)

    # Build tier package context
    normal_pkg = {
        'tier': 'normal',
        'badge_label': '🟢 Normal',
        'title': 'Essential Skincare',
        'subtitle': 'Local & budget-friendly brands',
        'price': 'From ₹99 – ₹999',
        'strike': None,
        'features': [
            'Best local brand picks for your concern',
            'Easily available at pharmacies & online',
            'Dermatologist-approved OTC formulas',
            'AI chat support included',
            'Log & Earn points on every purchase',
        ],
        'cta': 'Shop Normal Plan',
        'cta_url': '/products/?product_range=ayurvedic',
    }
    medium_pkg = {
        'tier': 'medium',
        'badge_label': '💜 Plus',
        'title': 'Advanced Skincare',
        'subtitle': 'Mid-market brands at lower prices',
        'price': 'From ₹500 – ₹2,499',
        'strike': 'Regular retail: ₹2,999+',
        'features': [
            'Established brand alternatives',
            'Clinically proven formulations',
            'Priority AI consultant access',
            'Exclusive member pricing',
            '2× Log & Earn points',
        ],
        'cta': 'Upgrade to Plus',
        'cta_url': '/membership/upgrade/',
    }
    vip_pkg = {
        'tier': 'vip',
        'badge_label': '👑 VIP',
        'title': 'Premium Collection',
        'subtitle': 'Top-tier global brands — exclusive pricing',
        'price': '₹1,500 – No Limit',
        'strike': None,
        'features': [
            'Premium international brands',
            'VIP member exclusive pricing',
            'Unlimited AI consultant sessions',
            '3× Log & Earn points multiplier',
        ],
        'locked_feature': '1-on-1 Doctor Live Chat',
        'cta': 'Go VIP',
        'cta_url': '/membership/upgrade/',
    }

    referral_code = ''
    if request.user.is_authenticated:
        try:
            referral_code = request.user.profile.referral_code
        except Exception:
            pass

    next_steps = [
        {'icon': '🛍️', 'label': 'Browse Products',   'url': '/products/',            'desc': 'Shop products matched to your skin type and concern'},
        {'icon': '💬', 'label': 'AI Consultant',      'url': '/chat/',                'desc': 'Get personalised advice from your AI skin doctor'},
        {'icon': '🏆', 'label': 'Log & Earn Points',  'url': '/diagnostic/log-earn/', 'desc': 'Build healthy habits and earn loyalty rewards'},
    ]

    return render(request, 'diagnostic/result.html', {
        'sess': sess,
        'normal_pkg': normal_pkg,
        'medium_pkg': medium_pkg,
        'vip_pkg': vip_pkg,
        'referral_code': referral_code,
        'next_steps': next_steps,
    })


# ── MARKETING PORTAL ──────────────────────────────────────────────────────────

@login_required
def marketing_portal(request):
    if not _staff_or_marketing(request.user):
        return render(request, 'diagnostic/marketing.html', {'access_denied': True}, status=403)

    total_starts   = DiagnosticSession.objects.count()
    total_complete = DiagnosticSession.objects.filter(completed=True).count()
    conversion_rate = round((total_complete / total_starts * 100) if total_starts else 0, 1)
    total_clicks   = ReferralClick.objects.count()

    # Tier breakdown
    tier_counts = {}
    for t in ('normal', 'medium', 'vip'):
        tier_counts[t] = DiagnosticSession.objects.filter(
            completed=True, recommended_tier=t).count()

    # Percentage for progress bars
    tier_pcts = {}
    for t, c in tier_counts.items():
        tier_pcts[t] = round((c / total_complete * 100) if total_complete else 0)

    recent = DiagnosticSession.objects.filter(completed=True).order_by('-created_at')[:20]

    referral_code = ''
    try:
        referral_code = request.user.profile.referral_code
    except Exception:
        pass

    ref_clicks = ReferralClick.objects.filter(referral_code=referral_code).count()
    ref_converts = ReferralClick.objects.filter(
        referral_code=referral_code, converted=True).count()

    return render(request, 'diagnostic/marketing.html', {
        'total_starts':    total_starts,
        'total_complete':  total_complete,
        'conversion_rate': conversion_rate,
        'total_clicks':    total_clicks,
        'tier_counts':     tier_counts,
        'tier_pcts':       tier_pcts,
        'recent':          recent,
        'referral_code':   referral_code,
        'ref_clicks':      ref_clicks,
        'ref_converts':    ref_converts,
    })


# ── ADMIN PANEL ───────────────────────────────────────────────────────────────

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def admin_panel(request):
    today = date.today()

    sessions    = DiagnosticSession.objects.select_related('user').order_by('-created_at')[:50]
    total_sess  = DiagnosticSession.objects.count()
    complete    = DiagnosticSession.objects.filter(completed=True).count()
    comp_rate   = round((complete / total_sess * 100) if total_sess else 0, 1)

    # Most popular category
    from collections import Counter
    all_cats = []
    for s in DiagnosticSession.objects.values_list('selected_categories', flat=True):
        if s:
            all_cats.extend(s)
    cat_counter = Counter(all_cats)
    top_cat = cat_counter.most_common(1)[0][0] if cat_counter else 'N/A'

    # Habits today
    habit_logs_today = HabitLog.objects.filter(logged_at__date=today).count()
    recent_habits    = HabitLog.objects.select_related('user', 'habit').order_by('-logged_at')[:30]

    # Active users (habit log in last 7 days)
    since = timezone.now() - timedelta(days=7)
    active_users = HabitLog.objects.filter(logged_at__gte=since).values('user').distinct().count()

    # Points today
    from django.db.models import Sum
    points_today = HabitLog.objects.filter(
        logged_at__date=today).aggregate(total=Sum('points_earned'))['total'] or 0

    # Product counts per category
    product_counts = {
        'makeup':    Product.objects.filter(product_range='makeup').count(),
        'korean':    Product.objects.filter(product_range='korean').count(),
        'ayurvedic': Product.objects.filter(product_range='ayurvedic').count(),
        'pharmacy':  Product.objects.filter(product_range='pharmacy').count(),
    }

    habits = HabitCategory.objects.all()

    return render(request, 'diagnostic/admin_panel.html', {
        'sessions':       sessions,
        'total_sess':     total_sess,
        'comp_rate':      comp_rate,
        'top_cat':        top_cat,
        'habit_logs_today': habit_logs_today,
        'active_users':   active_users,
        'points_today':   points_today,
        'recent_habits':  recent_habits,
        'product_counts': product_counts,
        'habits':         habits,
    })


@login_required
def logs_fragment(request):
    """AJAX fragment — returns only habit log table rows (auto-refresh)."""
    if not request.user.is_staff:
        return HttpResponseForbidden()
    recent = HabitLog.objects.select_related('user', 'habit').order_by('-logged_at')[:30]
    return render(request, 'diagnostic/_logs_fragment.html', {'recent_habits': recent})


# ── LOG & EARN ────────────────────────────────────────────────────────────────

@login_required
def log_earn(request):
    today = date.today()
    habits = HabitCategory.objects.all()

    user_logs_today = HabitLog.objects.filter(
        user=request.user, logged_at__date=today
    ).select_related('habit')

    logged_slugs = set(l.habit.slug for l in user_logs_today)

    from django.db.models import Sum
    points_today = user_logs_today.aggregate(total=Sum('points_earned'))['total'] or 0

    all_logs = HabitLog.objects.filter(user=request.user).select_related('habit')[:50]

    # Streak: consecutive days with ≥1 log
    streak = 0
    check_day = today
    while True:
        if HabitLog.objects.filter(user=request.user, logged_at__date=check_day).exists():
            streak += 1
            check_day -= timedelta(days=1)
        else:
            break

    try:
        user_points = request.user.profile.loyalty_points
        current_tier = request.user.profile.effective_tier
    except Exception:
        user_points = 0
        current_tier = 'normal'

    # Tier progress
    if current_tier == 'normal':
        tier_goal = 500
        next_tier = 'Medium'
    elif current_tier == 'medium':
        tier_goal = 1500
        next_tier = 'VIP'
    else:
        tier_goal = None
        next_tier = None

    tier_progress_pct = min(100, round((user_points / tier_goal * 100) if tier_goal else 100))

    # Leaderboard — top 10 by loyalty_points
    leaderboard = UserProfile.objects.select_related('user').order_by('-loyalty_points')[:10]

    # Daily goal: 50 pts
    daily_goal = 50
    ring_pct = min(1.0, points_today / daily_goal)
    ring_offset = round(283 - (283 * ring_pct))

    return render(request, 'diagnostic/log_earn.html', {
        'habits':          habits,
        'logged_slugs':    logged_slugs,
        'user_logs_today': user_logs_today,
        'all_logs':        all_logs,
        'points_today':    points_today,
        'streak':          streak,
        'user_points':     user_points,
        'current_tier':    current_tier,
        'tier_goal':       tier_goal,
        'next_tier':       next_tier,
        'tier_progress_pct': tier_progress_pct,
        'leaderboard':     leaderboard,
        'daily_goal':      daily_goal,
        'ring_offset':     ring_offset,
        'points_today':    points_today,
    })


@login_required
@require_POST
def log_habit_ajax(request):
    """AJAX POST — log a habit and award points."""
    try:
        data = json.loads(request.body)
        slug = data.get('habit_slug', '')
    except Exception:
        slug = request.POST.get('habit_slug', '')

    habit = get_object_or_404(HabitCategory, slug=slug)

    today = date.today()
    already = HabitLog.objects.filter(
        user=request.user, habit=habit, logged_at__date=today
    ).exists()

    if already:
        return JsonResponse({'ok': False, 'message': 'Already logged today!'})

    # VIP gets 3× points, medium gets 2×
    try:
        tier = request.user.profile.effective_tier
    except Exception:
        tier = 'normal'

    multiplier = 3 if tier == 'vip' else 2 if tier == 'medium' else 1
    pts = habit.points * multiplier

    HabitLog.objects.create(user=request.user, habit=habit, points_earned=pts)

    # Add to profile loyalty points
    try:
        profile = request.user.profile
        profile.loyalty_points += pts
        profile.save(update_fields=['loyalty_points'])
        total_points = profile.loyalty_points
    except Exception:
        total_points = pts

    from django.db.models import Sum
    points_today = HabitLog.objects.filter(
        user=request.user, logged_at__date=today
    ).aggregate(total=Sum('points_earned'))['total'] or 0

    return JsonResponse({
        'ok': True,
        'points_earned': pts,
        'total_points':  total_points,
        'points_today':  points_today,
        'message':       f'+{pts} pts — {habit.title} logged! {habit.icon}',
        'daily_goal_reached': points_today >= 50,
    })


# ── SMART DIAGNOSTIC QUIZ ─────────────────────────────────────────────────────

from .models import SmartDiagSession
from . import smart_quiz as sq


def _get_or_create_smart_session(request):
    """Return existing SmartDiagSession or create new one."""
    sid = request.session.get('smart_diag_id')
    if sid:
        try:
            return SmartDiagSession.objects.get(id=sid)
        except SmartDiagSession.DoesNotExist:
            pass
    sess = SmartDiagSession.objects.create(
        user=request.user if request.user.is_authenticated else None,
        session_key=request.session.session_key or '',
    )
    request.session['smart_diag_id'] = str(sess.id)
    return sess


def smart_start(request):
    """Create fresh SmartDiagSession and redirect to step 1."""
    if 'smart_diag_id' in request.session:
        del request.session['smart_diag_id']
    sess = SmartDiagSession.objects.create(
        user=request.user if request.user.is_authenticated else None,
        session_key=request.session.session_key or '',
    )
    request.session['smart_diag_id'] = str(sess.id)
    return redirect('diagnostic:smart_question', step=1)


def smart_question(request, step):
    """Render one smart-quiz step. Conditions evaluated against saved answers."""
    sess = _get_or_create_smart_session(request)
    answers = sess.answers or {}

    step_def, total_steps = sq.get_step_by_position(answers, step)
    if step_def is None:
        # Past the last step — compute and redirect to result
        return redirect('diagnostic:smart_finish', session_id=sess.id)

    progress_pct = int((step - 1) / total_steps * 100)

    # Flatten all questions from the step into a single list for the template
    return render(request, 'diagnostic/smart_question.html', {
        'step':          step,
        'total_steps':   total_steps,
        'progress_pct':  progress_pct,
        'step_def':      step_def,
        'answers':       answers,
        'sess':          sess,
        'is_last':       sq.is_last_step(answers, step),
    })


@require_POST
def smart_save(request, step):
    """Save answers for one step, advance to next or finish."""
    sess = _get_or_create_smart_session(request)
    answers = dict(sess.answers or {})

    # Merge POST data — multi-select fields become lists, single → string
    for key in request.POST:
        if key == 'csrfmiddlewaretoken':
            continue
        values = request.POST.getlist(key)
        answers[key] = values if len(values) > 1 else (values[0] if values else '')

    sess.answers = answers
    sess.save(update_fields=['answers'])

    # Re-evaluate active steps with the updated answers
    if sq.is_last_step(answers, step):
        return redirect('diagnostic:smart_finish', session_id=sess.id)

    return redirect('diagnostic:smart_question', step=step + 1)


def smart_finish(request, session_id):
    """Compute analysis, save, redirect to result."""
    sess = get_object_or_404(SmartDiagSession, id=session_id)
    if not sess.completed:
        answers = sess.answers or {}
        analysis = sq.compute_analysis(answers)
        cats = analysis.get('categories', [])
        sess.analysis    = analysis
        sess.severity    = analysis.get('severity', '')
        sess.top_concern_cat = cats[0] if cats else ''
        sess.primary_goal = answers.get('skin_concerns', [''])[0] if isinstance(
            answers.get('skin_concerns'), list) else ''
        sess.completed   = True
        sess.save()
    return redirect('diagnostic:smart_result', session_id=sess.id)


def smart_result(request, session_id):
    """Render the full personalised AI analysis result page."""
    sess = get_object_or_404(SmartDiagSession, id=session_id)
    analysis = sess.analysis or {}
    answers  = sess.answers or {}

    # Get the user's latest scan to link to scan results from this page
    latest_scan = None
    if request.user.is_authenticated:
        from apps.scanner.models import ScanResult
        latest_scan = ScanResult.objects.filter(
            user=request.user, is_demo=False
        ).order_by('-created_at').first()

    return render(request, 'diagnostic/smart_result.html', {
        'sess':        sess,
        'answers':     answers,
        'analysis':    analysis,
        'latest_scan': latest_scan,
    })
