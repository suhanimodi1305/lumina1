"""
Hair Diagnosis wizard — one question per page, 6 steps.
"""
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import HairSession

TOTAL_STEPS = 6


def _get_or_create_session(request):
    """Return existing HairSession from Django session or create new."""
    sid = request.session.get('hair_session_id')
    if sid:
        try:
            return HairSession.objects.get(id=sid)
        except HairSession.DoesNotExist:
            pass
    sess = HairSession.objects.create(
        user=request.user if request.user.is_authenticated else None,
        session_key=request.session.session_key or '',
    )
    request.session['hair_session_id'] = str(sess.id)
    return sess


def _compute_plan(sess):
    """Simple rule-based plan recommendation."""
    severe_concerns = {'hair_loss', 'baldness', 'thinning'}
    concerns_set = set(sess.hair_concerns or [])
    stage = sess.severity_stage or ''

    if stage == 'stage4' or len(concerns_set & severe_concerns) >= 2:
        return 'premium'
    if stage in ('stage3', 'stage2') or sess.scalp_condition in ('oily_dandruff', 'itchy_flaky'):
        return 'advanced'
    return 'basic'


# ── VIEWS ─────────────────────────────────────────────────────────────────────

def start(request):
    """Intro / landing page — creates a fresh session and redirects to Q1."""
    sess = HairSession.objects.create(
        user=request.user if request.user.is_authenticated else None,
        session_key=request.session.session_key or '',
    )
    request.session['hair_session_id'] = str(sess.id)
    return redirect('hair:question', step=1)


def restart(request):
    """Clear session and restart from the beginning."""
    if 'hair_session_id' in request.session:
        del request.session['hair_session_id']
    return redirect('hair:start')


def question(request, step):
    """Render the question page for the given step (1–6)."""
    if step < 1 or step > TOTAL_STEPS:
        return redirect('hair:start')

    sess = _get_or_create_session(request)

    context = {
        'step':        step,
        'total_steps': TOTAL_STEPS,
        'session_id':  str(sess.id),
        'sess':        sess,
        'progress_pct': int((step - 1) / TOTAL_STEPS * 100),
    }

    # Step-specific template data
    if step == 1:
        context['concerns'] = HAIR_CONCERNS
    elif step == 2:
        context['scalp_options'] = SCALP_OPTIONS
    elif step == 3:
        context['root_symptoms'] = ROOT_SYMPTOMS
    elif step == 4:
        context['hair_types']    = HAIR_TYPES
        context['hair_textures'] = HAIR_TEXTURES
    elif step == 5:
        context['severity_stages'] = SEVERITY_STAGES
    elif step == 6:
        pass  # personal details — no data list needed

    return render(request, f'hair/step_{step}.html', context)


@require_POST
def save_step(request, step):
    """AJAX or form POST — saves one step's data and redirects to next step."""
    sess = _get_or_create_session(request)

    if step == 1:
        concerns = request.POST.getlist('hair_concerns')
        if not concerns:
            # JSON body fallback
            try:
                data = json.loads(request.body)
                concerns = data.get('hair_concerns', [])
            except Exception:
                concerns = []
        sess.hair_concerns = concerns
        sess.save(update_fields=['hair_concerns'])

    elif step == 2:
        sess.scalp_condition = request.POST.get('scalp_condition', '')
        sess.save(update_fields=['scalp_condition'])

    elif step == 3:
        symptoms = request.POST.getlist('root_symptoms')
        sess.root_symptoms = symptoms
        sess.save(update_fields=['root_symptoms'])

    elif step == 4:
        sess.hair_type    = request.POST.get('hair_type', '')
        sess.hair_texture = request.POST.get('hair_texture', '')
        sess.save(update_fields=['hair_type', 'hair_texture'])

    elif step == 5:
        sess.severity_stage = request.POST.get('severity_stage', '')
        sess.save(update_fields=['severity_stage'])

    elif step == 6:
        sess.first_name    = request.POST.get('first_name', '').strip()
        sess.gender        = request.POST.get('gender', '')
        sess.water_intake  = request.POST.get('water_intake', '')
        sess.sleep_quality = request.POST.get('sleep_quality', '')
        sess.recommended_plan = _compute_plan(sess)
        sess.completed = True
        sess.save()
        return redirect('hair:result', session_id=sess.id)

    # Go to next step
    return redirect('hair:question', step=step + 1)


def result(request, session_id):
    """Final result page showing the personalised hair plan."""
    sess = get_object_or_404(HairSession, id=session_id)

    plans = {
        'basic': {
            'name': 'Essential Hair Care',
            'badge': '🌿 Basic',
            'badge_class': 'basic',
            'tagline': 'Natural & budget-friendly care',
            'price': '₹299 – ₹999 / month',
            'features': [
                'Personalised shampoo & oil recommendations',
                'Scalp care routine (7-day plan)',
                'Diet tips for hair health',
                'AI Hair Consultant access',
                'Earn loyalty points on every purchase',
            ],
        },
        'advanced': {
            'name': 'Advanced Hair Therapy',
            'badge': '💜 Advanced',
            'badge_class': 'advanced',
            'tagline': 'Clinical-grade formulations',
            'price': '₹999 – ₹2,999 / month',
            'strike': 'Retail: ₹3,999+',
            'features': [
                'Clinically tested anti-hair-loss serums',
                'Customised scalp treatment protocol',
                'Priority AI consultant sessions',
                'Exclusive member pricing on all products',
                '2× Loyalty points multiplier',
            ],
        },
        'premium': {
            'name': 'Premium Hair Revival',
            'badge': '👑 Premium',
            'badge_class': 'premium',
            'tagline': 'Medical-grade + trichologist protocols',
            'price': '₹2,999 – No Limit',
            'features': [
                'Medical-grade hair growth protocols',
                'PRP-grade topical actives',
                'Unlimited AI trichologist sessions',
                '3× Loyalty points multiplier',
                'VIP-exclusive product access',
            ],
            'locked_feature': '1-on-1 Trichologist Consultation',
        },
    }

    concern_labels = {c['value']: c['label'] for c in HAIR_CONCERNS}

    return render(request, 'hair/result.html', {
        'sess':           sess,
        'plans':          plans,
        'rec_plan':       plans[sess.recommended_plan],
        'plan_keys':      ['basic', 'advanced', 'premium'],
        'concern_labels': concern_labels,
    })


# ── DATA CONSTANTS ─────────────────────────────────────────────────────────────

HAIR_CONCERNS = [
    {'value': 'hair_loss',      'label': 'Hair Loss',        'icon': '🪮', 'desc': 'Excessive shedding or thinning'},
    {'value': 'dandruff',       'label': 'Dandruff',         'icon': '❄️', 'desc': 'Flaky, itchy scalp'},
    {'value': 'dry_frizzy',     'label': 'Dry & Frizzy',     'icon': '💨', 'desc': 'Rough, unmanageable strands'},
    {'value': 'oily_scalp',     'label': 'Oily Scalp',       'icon': '💧', 'desc': 'Greasy roots, flat hair'},
    {'value': 'breakage',       'label': 'Breakage',         'icon': '⚡', 'desc': 'Snapping, split ends'},
    {'value': 'thinning',       'label': 'Thinning',         'icon': '🔍', 'desc': 'Reduced volume & density'},
    {'value': 'baldness',       'label': 'Bald Patches',     'icon': '⭕', 'desc': 'Patchy or receding areas'},
    {'value': 'slow_growth',    'label': 'Slow Growth',      'icon': '🐌', 'desc': 'Hair that won\'t grow long'},
]

SCALP_OPTIONS = [
    {'value': 'normal',        'label': 'Healthy & Normal',    'icon': '✅', 'desc': 'No notable issues'},
    {'value': 'dry_tight',     'label': 'Dry & Tight',         'icon': '🏜️', 'desc': 'Feels tight, some flaking'},
    {'value': 'oily_dandruff', 'label': 'Oily with Dandruff',  'icon': '💧', 'desc': 'Greasy + yellow/white flakes'},
    {'value': 'itchy_flaky',   'label': 'Itchy & Flaky',       'icon': '🔥', 'desc': 'Constant itch, white flakes'},
    {'value': 'sensitive',     'label': 'Sensitive / Reactive','icon': '🌸', 'desc': 'Reacts to products easily'},
    {'value': 'combination',   'label': 'Combination',         'icon': '☯️', 'desc': 'Oily roots, dry ends'},
]

ROOT_SYMPTOMS = [
    {'value': 'stress',         'label': '🧠 Stress',              'desc': 'High mental or work stress'},
    {'value': 'poor_diet',      'label': '🍟 Poor Diet',           'desc': 'Low nutrition, junk food'},
    {'value': 'hormonal',       'label': '🔄 Hormonal Issues',     'desc': 'PCOS, thyroid, menopause'},
    {'value': 'low_water',      'label': '💧 Low Water Intake',    'desc': 'Drinking less than 6 glasses/day'},
    {'value': 'poor_sleep',     'label': '😴 Poor Sleep',          'desc': 'Less than 6 hours regularly'},
    {'value': 'dandruff_inf',   'label': '❄️ Dandruff / Infection','desc': 'Scalp infections or persistent dandruff'},
    {'value': 'heat_damage',    'label': '🔥 Heat / Chemical',     'desc': 'Frequent styling, colouring, relaxers'},
    {'value': 'family_history', 'label': '🧬 Family History',      'desc': 'Genetic hair thinning in family'},
    {'value': 'pollution',      'label': '🌫️ Pollution',           'desc': 'High pollution / hard water exposure'},
    {'value': 'medications',    'label': '💊 Medications',         'desc': 'Side effect from medicines'},
]

HAIR_TYPES = [
    {'value': 'straight', 'label': 'Straight',  'icon': '|'},
    {'value': 'wavy',     'label': 'Wavy',       'icon': '〜'},
    {'value': 'curly',    'label': 'Curly',      'icon': '🌀'},
    {'value': 'coily',    'label': 'Coily/Kinky','icon': '➰'},
]

HAIR_TEXTURES = [
    {'value': 'fine',    'label': 'Fine',   'desc': 'Thin, delicate strands'},
    {'value': 'medium',  'label': 'Medium', 'desc': 'Average thickness'},
    {'value': 'coarse',  'label': 'Coarse', 'desc': 'Thick, strong strands'},
]

SEVERITY_STAGES = [
    {
        'value': 'stage1',
        'label': 'Stage 1',
        'sublabel': 'Mild',
        'detail': 'Slight / Minimal',
        'desc': 'Minor shedding or occasional dryness. Easy to manage with targeted care.',
        'icon': '🟢',
        'color': '#22c55e',
    },
    {
        'value': 'stage2',
        'label': 'Stage 2',
        'sublabel': 'Moderate',
        'detail': 'Noticeable · Growing',
        'desc': 'Consistent shedding or visible scalp dryness. Needs active treatment.',
        'icon': '🟡',
        'color': '#f59e0b',
    },
    {
        'value': 'stage3',
        'label': 'Stage 3',
        'sublabel': 'Significant',
        'detail': 'Visible · Persistent',
        'desc': 'Clear thinning or dense dandruff. Requires clinical-grade formulations.',
        'icon': '🟠',
        'color': '#f97316',
    },
    {
        'value': 'stage4',
        'label': 'Stage 4',
        'sublabel': 'Severe',
        'detail': 'Deep · Persistent',
        'desc': 'Significant hair loss, wide partings, or bald patches. Medical approach needed.',
        'icon': '🔴',
        'color': '#ef4444',
    },
]
