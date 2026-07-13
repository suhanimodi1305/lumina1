"""
Progress Tracking views.
Covers: daily routine log, weekly check-in, milestone tracker, analytics.
"""
import json
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Sum
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import DailyRoutineLog, WeeklyCheckin, ScanMilestone


# ─────────────────────────────────────────────────────────────────────────────
# PROGRESS DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def progress_home(request):
    """Main progress tracking hub — shows all modules at a glance."""
    today = date.today()

    # Today's routine log
    today_log, _ = DailyRoutineLog.objects.get_or_create(
        user=request.user, log_date=today
    )

    # Last 7 days routine completion
    week_ago = today - timedelta(days=6)
    week_logs = DailyRoutineLog.objects.filter(
        user=request.user, log_date__gte=week_ago
    ).order_by('log_date')
    week_dates = [(week_ago + timedelta(days=i)) for i in range(7)]
    week_data = {log.log_date: log for log in week_logs}
    week_grid = [
        {
            'date':     d,
            'label':    d.strftime('%a'),
            'log':      week_data.get(d),
            'is_today': d == today,
        }
        for d in week_dates
    ]

    # Streak calculation
    streak = 0
    check_day = today
    while True:
        log = DailyRoutineLog.objects.filter(
            user=request.user, log_date=check_day, am_done=True
        ).first()
        if log:
            streak += 1
            check_day -= timedelta(days=1)
        else:
            break

    # Milestone tracker
    milestone, _ = ScanMilestone.objects.get_or_create(
        user=request.user,
        defaults={'started_at': timezone.now()},
    )
    # Auto-link Day 0 scan if not done yet
    if milestone.scan_day0 is None:
        from apps.scanner.models import ScanResult
        first_scan = ScanResult.objects.filter(
            user=request.user, is_demo=False
        ).order_by('created_at').first()
        if first_scan:
            milestone.scan_day0    = first_scan
            milestone.score_day0   = first_scan.harmony_score
            milestone.save(update_fields=['scan_day0', 'score_day0'])

    # Weekly check-ins (most recent first, used as a list in template)
    weekly_checkins = WeeklyCheckin.objects.filter(
        user=request.user
    ).order_by('-week_number')

    # Points summary
    try:
        total_points = request.user.profile.loyalty_points
    except Exception:
        total_points = 0

    # Score chart data (milestones)
    chart_labels = ['Day 0', 'Day 14', 'Day 30', 'Day 60', 'Day 90']
    chart_scores = [
        milestone.score_day0, milestone.score_day14,
        milestone.score_day30, milestone.score_day60, milestone.score_day90,
    ]

    return render(request, 'progress/home.html', {
        'today_log':       today_log,
        'week_grid':       week_grid,
        'streak':          streak,
        'milestone':       milestone,
        'weekly_checkins': weekly_checkins,
        'total_points':    total_points,
        'chart_labels':    json.dumps(chart_labels),
        'chart_scores':    json.dumps(chart_scores),
        'today':           today,
    })


# ─────────────────────────────────────────────────────────────────────────────
# DAILY ROUTINE LOG
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def daily_log(request):
    """Show today's premium routine dashboard."""
    today = date.today()
    log, _ = DailyRoutineLog.objects.get_or_create(user=request.user, log_date=today)

    # Last 14 days for history panel
    history = DailyRoutineLog.objects.filter(
        user=request.user,
        log_date__gte=today - timedelta(days=13),
    ).order_by('-log_date')

    # ── Streak calculation ────────────────────────────────────────
    streak = 0
    check_day = today
    while True:
        streak_log = DailyRoutineLog.objects.filter(
            user=request.user, log_date=check_day, am_done=True
        ).first()
        if streak_log:
            streak += 1
            check_day -= timedelta(days=1)
        else:
            break

    # ── Milestone / next scan ─────────────────────────────────────
    milestone = None
    days_to_scan = 3
    last_score = None
    score_delta = 0
    try:
        milestone, _ = ScanMilestone.objects.get_or_create(
            user=request.user,
            defaults={'started_at': timezone.now()},
        )
        next_day = milestone.next_milestone_day
        if next_day is not None:
            days_elapsed = milestone.days_since_start
            days_to_scan = max(0, next_day - days_elapsed)
        # Last scored milestone
        for attr, score_attr in [
            ('scan_day90', 'score_day90'), ('scan_day60', 'score_day60'),
            ('scan_day30', 'score_day30'), ('scan_day14', 'score_day14'),
            ('scan_day0',  'score_day0'),
        ]:
            if getattr(milestone, attr) is not None:
                last_score = getattr(milestone, score_attr)
                break
    except Exception:
        pass

    # Skin score display (use scan score if available, else skin_rating×20)
    if last_score:
        skin_score = last_score
        score_delta = 3  # placeholder; real delta needs two scores
    else:
        skin_score = log.skin_rating * 20

    # ── Loyalty points ────────────────────────────────────────────
    total_points = 0
    try:
        total_points = request.user.profile.loyalty_points
    except Exception:
        pass

    # ── Skin goal from latest SkinSession ────────────────────────
    skin_goal = 'Healthy Glow'
    skin_type = 'Combination'
    try:
        from apps.skin.models import SkinSession
        latest_session = SkinSession.objects.filter(
            user=request.user, completed=True
        ).order_by('-created_at').first()
        if latest_session:
            skin_goal = latest_session.top_priority or latest_session.primary_concern or skin_goal
            skin_goal = skin_goal.replace('_', ' ').title()
            skin_type = (latest_session.skin_type_result or 'Combination').title()
    except Exception:
        pass

    # ── Overall routine completion percentage ────────────────────
    am_steps_total = 5
    pm_steps_total = 6
    am_completed = am_steps_total if log.am_done else 0
    pm_completed = pm_steps_total if log.pm_done else 0
    overall_pct = round(
        ((am_completed + pm_completed) / (am_steps_total + pm_steps_total)) * 100
    )

    # ── Last 7 days for streak display ───────────────────────────
    week_ago = today - timedelta(days=6)
    week_logs = DailyRoutineLog.objects.filter(
        user=request.user, log_date__gte=week_ago
    )
    week_data = {l.log_date: l for l in week_logs}
    week_grid = []
    for i in range(7):
        d = week_ago + timedelta(days=i)
        l = week_data.get(d)
        week_grid.append({
            'date': d,
            'label': d.strftime('%a'),
            'short_date': d.strftime('%d'),
            'done': l.am_done if l else False,
            'is_today': d == today,
        })

    # ── Featured products (top 8 for recommendations carousel) ──
    featured_products = []
    try:
        from apps.products.models import Product
        featured_products = list(
            Product.objects.filter(is_featured=True, product_range='korean')
            .order_by('?')[:8]
        )
        if len(featured_products) < 4:
            featured_products = list(Product.objects.order_by('?')[:8])
    except Exception:
        pass

    # ── SPF skipped yesterday reminder ───────────────────────────
    yesterday = today - timedelta(days=1)
    spf_skipped_yesterday = False
    try:
        yest_log = DailyRoutineLog.objects.filter(
            user=request.user, log_date=yesterday
        ).first()
        spf_skipped_yesterday = yest_log is not None and not yest_log.spf_applied
    except Exception:
        pass

    # ── Points to next reward ─────────────────────────────────────
    next_reward_threshold = ((total_points // 200) + 1) * 200
    points_to_next = next_reward_threshold - total_points

    return render(request, 'progress/daily_log.html', {
        'log':                    log,
        'today':                  today,
        'history':                history,
        'streak':                 streak,
        'milestone':              milestone,
        'skin_score':             skin_score,
        'score_delta':            score_delta,
        'skin_goal':              skin_goal,
        'skin_type':              skin_type,
        'overall_pct':            overall_pct,
        'am_steps_total':         am_steps_total,
        'pm_steps_total':         pm_steps_total,
        'am_completed':           am_completed,
        'pm_completed':           pm_completed,
        'week_grid':              week_grid,
        'total_points':           total_points,
        'points_to_next':         points_to_next,
        'days_to_scan':           days_to_scan,
        'featured_products':      featured_products,
        'spf_skipped_yesterday':  spf_skipped_yesterday,
    })


@login_required
@require_POST
def save_daily_log(request):
    """AJAX POST — save today's routine log."""
    today = date.today()
    log, _ = DailyRoutineLog.objects.get_or_create(user=request.user, log_date=today)

    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST.dict()

    session_type = data.get('session', 'am')  # 'am' or 'pm'
    now = timezone.now()

    if session_type == 'am':
        log.am_done      = True
        log.am_notes     = str(data.get('notes', ''))[:300]
        log.am_logged_at = now
    elif session_type == 'pm':
        log.pm_done      = True
        log.pm_notes     = str(data.get('notes', ''))[:300]
        log.pm_logged_at = now

    log.water_glasses = min(int(data.get('water_glasses', 0) or 0), 20)
    log.spf_applied   = bool(data.get('spf_applied', False))
    log.skin_rating   = max(1, min(5, int(data.get('skin_rating', 3) or 3)))
    log.save()

    # Award loyalty points
    pts = log.points_earned
    if pts > 0:
        try:
            profile = request.user.profile
            # Only award once per session per day
            if session_type == 'am' and log.am_done:
                profile.loyalty_points += 10
                profile.save(update_fields=['loyalty_points'])
            elif session_type == 'pm' and log.pm_done:
                profile.loyalty_points += 10
                profile.save(update_fields=['loyalty_points'])
        except Exception:
            pass

    # Create notification if full day complete
    if log.am_done and log.pm_done:
        from apps.notifications.models import Notification
        already = Notification.objects.filter(
            user=request.user,
            notif_type='achievement',
            created_at__date=today,
        ).exists()
        if not already:
            Notification.create_for_user(
                user=request.user,
                notif_type='achievement',
                title='Full Routine Complete! 🎉',
                message=f'You completed both your AM and PM routines on {today.strftime("%d %b")}. +20 points!',
                icon='🌟',
            )

    return JsonResponse({
        'ok':        True,
        'am_done':   log.am_done,
        'pm_done':   log.pm_done,
        'pts_earned': log.points_earned,
    })


# ─────────────────────────────────────────────────────────────────────────────
# WEEKLY CHECK-IN
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def weekly_checkin(request):
    """Show or submit the weekly check-in form."""
    milestone, _ = ScanMilestone.objects.get_or_create(
        user=request.user,
        defaults={'started_at': timezone.now()},
    )
    week_number = max(1, (milestone.days_since_start // 7) + 1)
    week_start  = (timezone.now() - timedelta(days=timezone.now().weekday())).date()

    # Check if already submitted this week
    existing = WeeklyCheckin.objects.filter(
        user=request.user, week_number=week_number
    ).first()

    if request.method == 'POST':
        if existing:
            messages.info(request, "You've already submitted this week's check-in.")
            return redirect('progress:weekly_checkin')

        checkin = WeeklyCheckin(
            user=request.user,
            week_number=week_number,
            week_start=week_start,
        )
        checkin.overall_rating   = max(1, min(5, int(request.POST.get('overall_rating', 3) or 3)))
        checkin.hydration_rating = max(1, min(5, int(request.POST.get('hydration_rating', 3) or 3)))
        checkin.acne_rating      = max(1, min(5, int(request.POST.get('acne_rating', 3) or 3)))
        checkin.brightness_rating= max(1, min(5, int(request.POST.get('brightness_rating', 3) or 3)))
        checkin.new_concerns     = request.POST.get('new_concerns', '')[:500]
        checkin.notes            = request.POST.get('notes', '')[:1000]
        checkin.has_selfie       = bool(request.POST.get('has_selfie'))
        checkin.products_used    = request.POST.getlist('products_used')

        # Compute delta from last week
        prev = WeeklyCheckin.objects.filter(
            user=request.user, week_number=week_number - 1
        ).first()
        if prev:
            checkin.overall_delta = checkin.overall_rating - prev.overall_rating

        checkin.save()

        # Award points
        try:
            profile = request.user.profile
            profile.loyalty_points += 25
            profile.save(update_fields=['loyalty_points'])
        except Exception:
            pass

        # Notification
        from apps.notifications.models import Notification
        Notification.create_for_user(
            user=request.user,
            notif_type='weekly_checkin',
            title=f'Week {week_number} Check-in Complete! ✅',
            message=f'You rated your skin {checkin.overall_rating}/5 this week. Keep it up!',
            icon='📋',
            action_url='/progress/',
            action_label='View Progress',
        )

        messages.success(request, f'Week {week_number} check-in saved! +25 points.')
        return redirect('progress:progress_home')

    # Previous check-ins for history sidebar
    history = WeeklyCheckin.objects.filter(user=request.user).order_by('-week_number')[:8]

    return render(request, 'progress/weekly_checkin.html', {
        'week_number': week_number,
        'week_start':  week_start,
        'existing':    existing,
        'history':     history,
    })


# ─────────────────────────────────────────────────────────────────────────────
# MILESTONE TRACKER
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def milestone_tracker(request):
    """Day 0 / 14 / 30 / 60 / 90 scan milestone overview."""
    milestone, _ = ScanMilestone.objects.get_or_create(
        user=request.user,
        defaults={'started_at': timezone.now()},
    )

    # Auto-link Day 0
    if milestone.scan_day0 is None:
        from apps.scanner.models import ScanResult
        first_scan = ScanResult.objects.filter(
            user=request.user, is_demo=False
        ).order_by('created_at').first()
        if first_scan:
            milestone.scan_day0  = first_scan
            milestone.score_day0 = first_scan.harmony_score
            milestone.save(update_fields=['scan_day0', 'score_day0'])

    days_elapsed = milestone.days_since_start

    milestones_data = [
        {
            'day':        0,
            'label':      'Day 0 — Baseline',
            'icon':       '📸',
            'scan':       milestone.scan_day0,
            'score':      milestone.score_day0,
            'unlocked':   True,
            'done':       milestone.scan_day0 is not None,
            'due_in':     None,
        },
        {
            'day':        14,
            'label':      'Day 14 — First Check',
            'icon':       '🔍',
            'scan':       milestone.scan_day14,
            'score':      milestone.score_day14,
            'unlocked':   days_elapsed >= 12,
            'done':       milestone.scan_day14 is not None,
            'due_in':     max(0, 14 - days_elapsed),
        },
        {
            'day':        30,
            'label':      'Day 30 — Monthly Report',
            'icon':       '📊',
            'scan':       milestone.scan_day30,
            'score':      milestone.score_day30,
            'unlocked':   days_elapsed >= 28,
            'done':       milestone.scan_day30 is not None,
            'due_in':     max(0, 30 - days_elapsed),
        },
        {
            'day':        60,
            'label':      'Day 60 — Optimisation',
            'icon':       '⚡',
            'scan':       milestone.scan_day60,
            'score':      milestone.score_day60,
            'unlocked':   days_elapsed >= 58,
            'done':       milestone.scan_day60 is not None,
            'due_in':     max(0, 60 - days_elapsed),
        },
        {
            'day':        90,
            'label':      'Day 90 — Transformation',
            'icon':       '🏆',
            'scan':       milestone.scan_day90,
            'score':      milestone.score_day90,
            'unlocked':   days_elapsed >= 88,
            'done':       milestone.scan_day90 is not None,
            'due_in':     max(0, 90 - days_elapsed),
        },
    ]

    return render(request, 'progress/milestone_tracker.html', {
        'milestone':       milestone,
        'milestones_data': milestones_data,
        'days_elapsed':    days_elapsed,
        'transformation':  milestone.transformation_pct,
    })


@login_required
@require_POST
def link_scan_to_milestone(request):
    """AJAX POST — link a scan to the next pending milestone."""
    scan_id = request.POST.get('scan_id') or request.POST.get('scan_id')
    try:
        from apps.scanner.models import ScanResult
        scan = ScanResult.objects.get(id=scan_id, user=request.user)
    except Exception:
        return JsonResponse({'ok': False, 'error': 'Scan not found.'})

    milestone, _ = ScanMilestone.objects.get_or_create(
        user=request.user,
        defaults={'started_at': timezone.now()},
    )

    next_day = milestone.next_milestone_day
    if next_day is None:
        return JsonResponse({'ok': False, 'error': 'All milestones complete!'})

    field_map = {0: 'scan_day0', 14: 'scan_day14', 30: 'scan_day30',
                 60: 'scan_day60', 90: 'scan_day90'}
    score_map = {0: 'score_day0', 14: 'score_day14', 30: 'score_day30',
                 60: 'score_day60', 90: 'score_day90'}

    setattr(milestone, field_map[next_day], scan)
    setattr(milestone, score_map[next_day], scan.harmony_score)
    milestone.save()

    # Award bonus points for milestone completion
    pts_map = {0: 0, 14: 50, 30: 100, 60: 150, 90: 300}
    pts = pts_map.get(next_day, 0)
    if pts:
        try:
            profile = request.user.profile
            profile.loyalty_points += pts
            profile.save(update_fields=['loyalty_points'])
        except Exception:
            pass

        from apps.notifications.models import Notification
        Notification.create_for_user(
            user=request.user,
            notif_type='achievement',
            title=f'Day {next_day} Milestone Complete! 🎯',
            message=f'You completed your Day {next_day} progress scan. +{pts} bonus points!',
            icon='🏆',
            action_url='/progress/milestones/',
            action_label='View Milestones',
        )

    return JsonResponse({'ok': True, 'milestone_day': next_day, 'pts_awarded': pts})


# ─────────────────────────────────────────────────────────────────────────────
# ANALYTICS (user-facing)
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def analytics(request):
    """User-facing analytics — scan history, routine consistency, progress charts."""
    from apps.scanner.models import ScanResult

    scans = ScanResult.objects.filter(user=request.user, is_demo=False).order_by('created_at')
    total_scans = scans.count()

    # Scan score history for chart
    scan_chart_labels = [s.created_at.strftime('%d %b') for s in scans]
    scan_chart_scores = {
        'harmony':      [s.harmony_score for s in scans],
        'hydration':    [s.hydration_score for s in scans],
        'pigmentation': [s.pigmentation_score for s in scans],
        'acne':         [s.acne_score for s in scans],
    }

    # Routine consistency last 30 days
    thirty_ago = date.today() - timedelta(days=29)
    logs_30 = DailyRoutineLog.objects.filter(
        user=request.user, log_date__gte=thirty_ago
    ).order_by('log_date')
    routine_labels = [(thirty_ago + timedelta(days=i)).strftime('%d') for i in range(30)]
    log_map  = {l.log_date: l for l in logs_30}
    routine_am_data = []
    routine_pm_data = []
    for i in range(30):
        d = thirty_ago + timedelta(days=i)
        l = log_map.get(d)
        routine_am_data.append(1 if (l and l.am_done) else 0)
        routine_pm_data.append(1 if (l and l.pm_done) else 0)

    am_pct = round(sum(routine_am_data) / 30 * 100)
    pm_pct = round(sum(routine_pm_data) / 30 * 100)

    # Weekly check-in history
    checkins = WeeklyCheckin.objects.filter(user=request.user).order_by('week_number')[:12]
    checkin_labels = [f'W{c.week_number}' for c in checkins]
    checkin_scores = [c.overall_rating for c in checkins]

    # Total routine logs
    total_logs = DailyRoutineLog.objects.filter(user=request.user).count()
    full_days  = DailyRoutineLog.objects.filter(user=request.user, am_done=True, pm_done=True).count()

    # Streak
    streak = 0
    check_day = date.today()
    while True:
        if DailyRoutineLog.objects.filter(user=request.user, log_date=check_day, am_done=True).exists():
            streak += 1
            check_day -= timedelta(days=1)
        else:
            break

    return render(request, 'progress/analytics.html', {
        'total_scans':       total_scans,
        'scan_chart_labels': json.dumps(scan_chart_labels),
        'scan_chart_scores': json.dumps(scan_chart_scores),
        'routine_labels':    json.dumps(routine_labels),
        'routine_am_data':   json.dumps(routine_am_data),
        'routine_pm_data':   json.dumps(routine_pm_data),
        'am_pct':            am_pct,
        'pm_pct':            pm_pct,
        'checkin_labels':    json.dumps(checkin_labels),
        'checkin_scores':    json.dumps(checkin_scores),
        'total_logs':        total_logs,
        'full_days':         full_days,
        'streak':            streak,
    })
