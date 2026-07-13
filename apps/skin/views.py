"""
Skin AI Beauty Consultation wizard — 12 steps, one question group per page.
Attractive multiple-choice design with conditional logic.
"""
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from .models import SkinSession

TOTAL_STEPS = 12

# ── Step metadata ──────────────────────────────────────────────────────────────

STEP_META = {
    1:  {'title': 'About You',        'icon': '👤', 'sub': 'Tell us a little about yourself'},
    2:  {'title': 'Skin Type',        'icon': '💧', 'sub': 'How does your skin behave day-to-day?'},
    3:  {'title': 'Acne & Breakouts', 'icon': '🔬', 'sub': 'Let\'s understand your breakout patterns'},
    4:  {'title': 'Pigmentation',     'icon': '☀️', 'sub': 'Any uneven tone or dark marks?'},
    5:  {'title': 'Sensitive Skin',   'icon': '🌸', 'sub': 'Does your skin react easily?'},
    6:  {'title': 'Aging & Hydration','icon': '⏳', 'sub': 'Signs of aging or dryness?'},
    7:  {'title': 'Daily Hydration',  'icon': '💦', 'sub': 'How much water do you drink?'},
    8:  {'title': 'Lifestyle',        'icon': '🏃', 'sub': 'Your daily habits affect your skin deeply'},
    9:  {'title': 'Food & Diet',      'icon': '🥗', 'sub': 'Diet is the foundation of skin health'},
    10: {'title': 'Skincare Routine', 'icon': '🧴', 'sub': 'Your current products and budget'},
    11: {'title': 'Makeup & Prefs',   'icon': '💄', 'sub': 'Makeup habits and product preferences'},
    12: {'title': 'Medical Info',     'icon': '⚕️', 'sub': 'Important health context for safe recommendations'},
}

# ── Step 1 data ────────────────────────────────────────────────────────────────

AGE_OPTIONS = [
    ('under18', 'Under 18', '🧒'),
    ('18_24',   '18 – 24',  '🧑'),
    ('25_34',   '25 – 34',  '👤'),
    ('35_44',   '35 – 44',  '🧔'),
    ('45_54',   '45 – 54',  '👩'),
    ('55plus',  '55+',      '🧓'),
]

GENDER_OPTIONS = [
    ('Female',            'Female',            '👩'),
    ('Male',              'Male',              '👨'),
    ('Non-binary',        'Non-binary',        '🌈'),
    ('Prefer not to say', 'Prefer not to say', '🤐'),
]

CLIMATE_OPTIONS = [
    {'value': 'tropical',  'label': 'Tropical',   'icon': '🌴', 'desc': 'Hot & humid year-round'},
    {'value': 'dry',       'label': 'Dry / Arid', 'icon': '🏜️', 'desc': 'Low humidity, hot or cold'},
    {'value': 'temperate', 'label': 'Temperate',  'icon': '🌤️', 'desc': 'Mild seasons'},
    {'value': 'cold',      'label': 'Cold',        'icon': '❄️', 'desc': 'Cold winters, cool summers'},
    {'value': 'humid',     'label': 'Humid',       'icon': '💧', 'desc': 'High humidity throughout'},
]

# ── Step 2 data ────────────────────────────────────────────────────────────────

FACE_FEEL_OPTIONS = [
    {'value': 'tight',       'label': 'Very dry & tight', 'icon': '🏜️', 'desc': 'Feels stretched, rough'},
    {'value': 'normal',      'label': 'Comfortable',      'icon': '✅',  'desc': 'Not tight, not oily'},
    {'value': 'oily',        'label': 'Slightly oily',    'icon': '💧', 'desc': 'Bit of shine on nose/forehead'},
    {'value': 'combination', 'label': 'Very oily',        'icon': '💦', 'desc': 'Greasy all over quickly'},
]

OILINESS_ZONE_OPTIONS = [
    {'value': 'forehead',  'label': 'Forehead',      'icon': '🙆', 'desc': 'Hairline / brow area'},
    {'value': 'nose',      'label': 'Nose (T-zone)', 'icon': '👃', 'desc': 'Bridge and tip of nose'},
    {'value': 'chin',      'label': 'Chin',           'icon': '😏', 'desc': 'Chin and lower jaw'},
    {'value': 'tzone',     'label': 'Entire T-zone',  'icon': '☯️', 'desc': 'Forehead + nose + chin'},
    {'value': 'afternoon', 'label': 'Entire face',    'icon': '😅', 'desc': 'All areas get oily'},
    {'value': 'never',     'label': 'Doesn\'t oily',  'icon': '🌵', 'desc': 'My skin stays dry'},
]

# ── Step 3 data ────────────────────────────────────────────────────────────────

ACNE_TYPE_OPTIONS = [
    {'value': 'whiteheads',   'label': 'Whiteheads',   'icon': '⚪'},
    {'value': 'blackheads',   'label': 'Blackheads',   'icon': '⚫'},
    {'value': 'pimples',      'label': 'Red pimples',  'icon': '🔴'},
    {'value': 'painful_acne', 'label': 'Painful cysts','icon': '😣'},
    {'value': 'acne_scars',   'label': 'Acne scars',   'icon': '🔶'},
    {'value': 'cystic_acne',  'label': 'Cystic acne',  'icon': '🧱'},
    {'value': 'redness',      'label': 'Redness',      'icon': '🌹'},
    {'value': 'itching',      'label': 'Itching',      'icon': '🤚'},
    {'value': 'burning',      'label': 'Burning',      'icon': '🔥'},
]

ACNE_LOCATION_OPTIONS = [
    {'value': 'forehead', 'label': 'Forehead', 'icon': '🙆'},
    {'value': 'nose',     'label': 'Nose',     'icon': '👃'},
    {'value': 'cheeks',   'label': 'Cheeks',   'icon': '😊'},
    {'value': 'chin',     'label': 'Chin',     'icon': '😏'},
    {'value': 'jawline',  'label': 'Jawline',  'icon': '🧔'},
    {'value': 'neck',     'label': 'Neck',     'icon': '🧣'},
    {'value': 'back',     'label': 'Back',     'icon': '🔙'},
    {'value': 'chest',    'label': 'Chest',    'icon': '👕'},
]

# ── Step 4 data ────────────────────────────────────────────────────────────────

PIGMENTATION_OPTIONS = [
    {'value': 'dark_spots',        'label': 'Dark Spots',        'icon': '🟤'},
    {'value': 'melasma',           'label': 'Melasma',           'icon': '🌑'},
    {'value': 'uneven_tone',       'label': 'Uneven Skin Tone',  'icon': '🎭'},
    {'value': 'freckles',          'label': 'Freckles',          'icon': '🟠'},
    {'value': 'sun_spots',         'label': 'Sun Spots',         'icon': '☀️'},
    {'value': 'hyperpigmentation', 'label': 'Hyperpigmentation', 'icon': '🔴'},
]

# ── Step 5 data ────────────────────────────────────────────────────────────────

SENSITIVITY_OPTIONS = [
    {'value': 'redness',          'label': 'Becomes red easily', 'icon': '🌹'},
    {'value': 'cosmetic_allergy', 'label': 'Allergic to cosmetics', 'icon': '🚫'},
    {'value': 'burning',          'label': 'Burning after skincare', 'icon': '🔥'},
    {'value': 'itching',          'label': 'Itching / Hives',    'icon': '🤚'},
    {'value': 'rosacea',          'label': 'Rosacea symptoms',   'icon': '🌺'},
]

# ── Step 6 data ────────────────────────────────────────────────────────────────

AGING_OPTIONS = [
    {'value': 'fine_lines',      'label': 'Fine Lines',        'icon': '〰️'},
    {'value': 'wrinkles',        'label': 'Wrinkles',          'icon': '📉'},
    {'value': 'loose_skin',      'label': 'Loose / Sagging',   'icon': '🫧'},
    {'value': 'under_eye_lines', 'label': 'Under-Eye Lines',   'icon': '👁️'},
    {'value': 'neck_wrinkles',   'label': 'Neck Wrinkles',     'icon': '📐'},
]

HYDRATION_OPTIONS = [
    {'value': 'dry_feeling',   'label': 'Skin feels dry / tight', 'icon': '🏜️'},
    {'value': 'patchy_makeup', 'label': 'Makeup becomes patchy',  'icon': '💄'},
    {'value': 'dry_lips',      'label': 'Lips often dry',         'icon': '💋'},
    {'value': 'flaky_skin',    'label': 'Flaky / Peeling skin',   'icon': '❄️'},
]

# ── Step 7 data ────────────────────────────────────────────────────────────────

WATER_OPTIONS = [
    {'value': 'lt1L',  'label': 'Less than 1 L',   'icon': '🏜️', 'desc': 'Very low — skin will suffer'},
    {'value': '1to2L', 'label': '1 – 2 L',          'icon': '💧', 'desc': 'Below recommended'},
    {'value': '2to3L', 'label': '2 – 3 L',          'icon': '✅', 'desc': 'Good daily intake'},
    {'value': 'gt3L',  'label': 'More than 3 L',    'icon': '💦', 'desc': 'Excellent hydration'},
]

# ── Step 8 data ────────────────────────────────────────────────────────────────

SLEEP_OPTIONS = [
    {'value': 'lt6',  'label': 'Less than 6 hrs', 'icon': '😴'},
    {'value': '6to8', 'label': '6 – 8 hrs',        'icon': '🌙'},
    {'value': 'gt8',  'label': 'More than 8 hrs',  'icon': '☀️'},
]

EXERCISE_OPTIONS = [
    {'value': 'none',       'label': 'None',      'icon': '🛋️'},
    {'value': 'occasional', 'label': 'Occasional', 'icon': '🚶'},
    {'value': 'regular',    'label': 'Regular',    'icon': '🏃'},
    {'value': 'daily',      'label': 'Daily',      'icon': '🏋️'},
]

ALCOHOL_OPTIONS = [
    {'value': 'none',       'label': 'None',         'icon': '🚫'},
    {'value': 'occasional', 'label': 'Occasionally', 'icon': '🍷'},
    {'value': 'regular',    'label': 'Regularly',    'icon': '🍺'},
]

# ── Step 9 data ────────────────────────────────────────────────────────────────

FOOD_OPTIONS = [
    {'value': 'spicy',      'label': 'Spicy Food',  'icon': '🌶️', 'desc': 'Can trigger inflammation & acne'},
    {'value': 'dairy',      'label': 'Dairy',       'icon': '🥛', 'desc': 'Linked to hormonal acne'},
    {'value': 'sugar',      'label': 'Sugar / Sweets','icon': '🍬','desc': 'Spikes insulin, worsens acne'},
    {'value': 'fruits',     'label': 'Fruits',      'icon': '🍎', 'desc': 'Antioxidants — great for skin'},
    {'value': 'vegetables', 'label': 'Vegetables',  'icon': '🥦', 'desc': 'Vitamins & minerals for glow'},
    {'value': 'protein',    'label': 'Protein',     'icon': '🥚', 'desc': 'Supports collagen production'},
]

# ── Step 10 data ───────────────────────────────────────────────────────────────

ROUTINE_ITEMS = [
    {'value': 'morning_cleanser', 'label': 'Morning Cleanser',  'icon': '🧼'},
    {'value': 'moisturizer',      'label': 'Moisturizer',       'icon': '💧'},
    {'value': 'sunscreen',        'label': 'Sunscreen / SPF',   'icon': '☀️'},
    {'value': 'night_routine',    'label': 'Night Routine',     'icon': '🌙'},
    {'value': 'retinol',          'label': 'Retinol',           'icon': '⚗️'},
    {'value': 'vitamin_c',        'label': 'Vitamin C Serum',   'icon': '🍊'},
    {'value': 'niacinamide',      'label': 'Niacinamide',       'icon': '🔬'},
    {'value': 'exfoliation',      'label': 'Exfoliation',       'icon': '✨'},
]

# ── Step 11 data ───────────────────────────────────────────────────────────────

MAKEUP_ITEMS = [
    {'value': 'foundation',    'label': 'Foundation',    'icon': '🫙'},
    {'value': 'concealer',     'label': 'Concealer',     'icon': '💛'},
    {'value': 'primer',        'label': 'Primer',        'icon': '🧴'},
    {'value': 'setting_spray', 'label': 'Setting Spray', 'icon': '💨'},
    {'value': 'blush',         'label': 'Blush',         'icon': '🌸'},
    {'value': 'bronzer',       'label': 'Bronzer',       'icon': '🟤'},
    {'value': 'highlighter',   'label': 'Highlighter',   'icon': '✨'},
    {'value': 'eyeshadow',     'label': 'Eyeshadow',     'icon': '👁️'},
    {'value': 'eyeliner',      'label': 'Eyeliner',      'icon': '🖊️'},
    {'value': 'mascara',       'label': 'Mascara',       'icon': '🪄'},
    {'value': 'lipstick',      'label': 'Lipstick',      'icon': '💋'},
    {'value': 'lip_liner',     'label': 'Lip Liner',     'icon': '📝'},
]

PRODUCT_PREFS = [
    {'value': 'korean',       'label': 'Korean Skincare',        'icon': '🇰🇷'},
    {'value': 'organic',      'label': 'Organic / Natural',      'icon': '🌿'},
    {'value': 'drugstore',    'label': 'Drugstore / Affordable', 'icon': '💊'},
    {'value': 'premium',      'label': 'Premium / Luxury',       'icon': '💎'},
    {'value': 'makeup',       'label': 'Makeup',                 'icon': '💄'},
    {'value': 'derma',        'label': 'Dermatologist-Recommended','icon': '👩‍⚕️'},
]

# ── Step 12 data ───────────────────────────────────────────────────────────────

MEDICAL_CONDITIONS = [
    {'value': 'pregnant',     'label': 'Pregnant',      'icon': '🤰'},
    {'value': 'breastfeeding','label': 'Breastfeeding', 'icon': '👶'},
    {'value': 'pcos',         'label': 'PCOS',          'icon': '🔄'},
    {'value': 'thyroid',      'label': 'Thyroid Issues','icon': '🦋'},
    {'value': 'diabetes',     'label': 'Diabetes',      'icon': '💉'},
]

SKIN_MEDS = [
    {'value': 'skin_medication', 'label': 'Prescription skin medication', 'icon': '💊'},
    {'value': 'isotretinoin',    'label': 'Isotretinoin (Accutane)',       'icon': '⚗️'},
    {'value': 'steroids',        'label': 'Steroid creams',               'icon': '🧴'},
    {'value': 'no_meds',         'label': 'No skin medications',          'icon': '✅'},
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_or_create_session(request):
    sid = request.session.get('skin_session_id')
    if sid:
        try:
            return SkinSession.objects.get(id=sid)
        except SkinSession.DoesNotExist:
            pass
    sess = SkinSession.objects.create(
        user=request.user if request.user.is_authenticated else None,
        session_key=request.session.session_key or '',
    )
    request.session['skin_session_id'] = str(sess.id)
    return sess


def _mark_checked(items, checked_values):
    """Return items list with a 'checked' key added."""
    for item in items:
        item['checked'] = item['value'] in checked_values
    return items


# ── Views ─────────────────────────────────────────────────────────────────────

def start(request):
    """Skip intro — go straight to the Face Scanner."""
    return redirect('scanner:upload')


def begin(request):
    """Create a new session and start the questionnaire (used by 'Skip Scan' button)."""
    sess = SkinSession.objects.create(
        user=request.user if request.user.is_authenticated else None,
        session_key=request.session.session_key or '',
    )
    request.session['skin_session_id'] = str(sess.id)
    return redirect('skin:question', step=1)


def restart(request):
    if 'skin_session_id' in request.session:
        del request.session['skin_session_id']
    return redirect('skin:start')


def question(request, step):
    if step < 1 or step > TOTAL_STEPS:
        return redirect('skin:start')

    sess = _get_or_create_session(request)
    ctx = {
        'step':         step,
        'total_steps':  TOTAL_STEPS,
        'sess':         sess,
        'progress_pct': int((step - 1) / TOTAL_STEPS * 100),
        'meta':         STEP_META[step],
    }

    if step == 1:
        ctx['age_options']    = AGE_OPTIONS
        ctx['gender_options'] = GENDER_OPTIONS
        ctx['climate_options'] = CLIMATE_OPTIONS

    elif step == 2:
        ctx['face_feel_options']     = FACE_FEEL_OPTIONS
        ctx['oiliness_zone_options'] = OILINESS_ZONE_OPTIONS

    elif step == 3:
        current = [k for k, v in {
            'pimples': sess.has_pimples, 'whiteheads': sess.has_whiteheads,
            'blackheads': sess.has_blackheads, 'painful_acne': sess.has_painful_acne,
            'acne_scars': sess.has_acne_scars, 'redness': sess.has_redness,
            'itching': sess.has_itching, 'burning': sess.has_burning,
            'cystic_acne': sess.has_cystic_acne,
        }.items() if v]
        ctx['acne_type_options']     = _mark_checked([dict(o) for o in ACNE_TYPE_OPTIONS], current)
        ctx['acne_location_options'] = ACNE_LOCATION_OPTIONS

    elif step == 4:
        ctx['pigmentation_options'] = PIGMENTATION_OPTIONS

    elif step == 5:
        ctx['sensitivity_options'] = SENSITIVITY_OPTIONS

    elif step == 6:
        ctx['aging_options']     = AGING_OPTIONS
        ctx['hydration_options'] = HYDRATION_OPTIONS

    elif step == 7:
        ctx['water_options'] = WATER_OPTIONS

    elif step == 8:
        ctx['sleep_options']    = SLEEP_OPTIONS
        ctx['exercise_options'] = EXERCISE_OPTIONS
        ctx['alcohol_options']  = ALCOHOL_OPTIONS

    elif step == 9:
        ctx['food_options'] = FOOD_OPTIONS

    elif step == 10:
        checked_routine = [
            'morning_cleanser' if sess.morning_cleanser else None,
            'moisturizer'      if sess.moisturizer      else None,
            'sunscreen'        if sess.sunscreen        else None,
            'night_routine'    if sess.night_routine    else None,
            'retinol'          if sess.uses_retinol     else None,
            'vitamin_c'        if sess.uses_vitamin_c   else None,
            'niacinamide'      if sess.uses_niacinamide else None,
            'exfoliation'      if sess.uses_exfoliation else None,
        ]
        checked_routine = [v for v in checked_routine if v]
        ctx['routine_items'] = _mark_checked([dict(o) for o in ROUTINE_ITEMS], checked_routine)

    elif step == 11:
        checked_makeup = [
            'foundation'    if sess.wears_foundation    else None,
            'concealer'     if sess.wears_concealer     else None,
            'primer'        if sess.wears_primer        else None,
            'setting_spray' if sess.wears_setting_spray else None,
        ]
        checked_makeup = [v for v in checked_makeup if v]
        ctx['makeup_items']   = _mark_checked([dict(o) for o in MAKEUP_ITEMS], checked_makeup)
        ctx['product_prefs']  = PRODUCT_PREFS

    elif step == 12:
        checked_medical = [
            'pregnant'     if sess.is_pregnant        else None,
            'breastfeeding'if sess.is_breastfeeding   else None,
            'pcos'         if sess.has_pcos           else None,
            'thyroid'      if sess.has_thyroid        else None,
            'diabetes'     if sess.has_diabetes       else None,
        ]
        checked_medical = [v for v in checked_medical if v]
        checked_meds = [
            'skin_medication' if sess.on_skin_medication else None,
            'isotretinoin'    if sess.uses_isotretinoin  else None,
            'steroids'        if sess.uses_steroids      else None,
        ]
        checked_meds = [v for v in checked_meds if v]
        ctx['medical_conditions'] = _mark_checked([dict(o) for o in MEDICAL_CONDITIONS], checked_medical)
        ctx['skin_meds']          = _mark_checked([dict(o) for o in SKIN_MEDS], checked_meds)

    return render(request, f'skin/step_{step}.html', ctx)


@require_POST
def save_step(request, step):
    sess = _get_or_create_session(request)

    if step == 1:
        age_map = {'under18': 16, '18_24': 21, '25_34': 29, '35_44': 39, '45_54': 49, '55plus': 58}
        sess.age        = age_map.get(request.POST.get('age_group', ''), 25)
        sess.age_group  = request.POST.get('age_group', '')
        sess.gender     = request.POST.get('gender', '')
        sess.climate    = request.POST.get('climate', '')
        sess.occupation = request.POST.get('occupation', '')
        sess.save(update_fields=['age', 'gender', 'climate', 'occupation'])

    elif step == 2:
        oiliness = request.POST.get('oiliness_timing', '')
        # Map new zone options back to original timing values
        zone_to_timing = {
            'forehead': 'afternoon', 'nose': 'afternoon', 'chin': 'afternoon',
            'tzone': 'afternoon', 'afternoon': 'afternoon', 'never': 'never',
        }
        sess.face_feel_after_wash = request.POST.get('face_feel_after_wash', '')
        sess.oiliness_timing      = zone_to_timing.get(oiliness, oiliness)
        sess.pores_visible        = request.POST.get('pores_visible', '')
        sess.skin_peels           = request.POST.get('skin_peels', '')
        sess.save(update_fields=['face_feel_after_wash', 'oiliness_timing', 'pores_visible', 'skin_peels'])

    elif step == 3:
        acne_level = request.POST.get('acne_level', 'none')
        symptoms   = request.POST.getlist('acne_symptoms')
        if acne_level == 'none':
            symptoms = []
        sess.has_pimples      = 'pimples' in symptoms or acne_level in ('few', 'moderate')
        sess.has_whiteheads   = 'whiteheads' in symptoms
        sess.has_blackheads   = 'blackheads' in symptoms
        sess.has_painful_acne = 'painful_acne' in symptoms or acne_level == 'severe'
        sess.has_acne_scars   = 'acne_scars' in symptoms
        sess.has_redness      = 'redness' in symptoms
        sess.has_itching      = 'itching' in symptoms
        sess.has_burning      = 'burning' in symptoms
        sess.has_cystic_acne  = 'cystic_acne' in symptoms or acne_level == 'severe'
        sess.acne_severity    = {'none': 'none', 'few': 'mild', 'moderate': 'moderate', 'severe': 'severe'}.get(acne_level, 'none')
        sess.save(update_fields=[
            'has_pimples','has_whiteheads','has_blackheads','has_painful_acne',
            'has_acne_scars','has_redness','has_itching','has_burning',
            'has_cystic_acne','acne_severity',
        ])

    elif step == 4:
        sess.pigmentation_concerns = request.POST.getlist('pigmentation_concerns')
        sess.save(update_fields=['pigmentation_concerns'])

    elif step == 5:
        sess.sensitivity_symptoms = request.POST.getlist('sensitivity_symptoms')
        sess.save(update_fields=['sensitivity_symptoms'])

    elif step == 6:
        sess.aging_concerns  = request.POST.getlist('aging_concerns')
        sess.hydration_issues = request.POST.getlist('hydration_issues')
        sess.save(update_fields=['aging_concerns', 'hydration_issues'])

    elif step == 7:
        # Map new water options to old keys
        water_map = {'lt1L': 'lt4', '1to2L': '4to6', '2to3L': '7to8', 'gt3L': 'gt8'}
        raw = request.POST.get('water_intake', '')
        sess.water_intake = water_map.get(raw, raw)
        sess.save(update_fields=['water_intake'])

    elif step == 8:
        sess.sleep_hours  = request.POST.get('sleep_hours', '')
        sess.stress_level = request.POST.get('stress_level', '')
        sess.exercise     = request.POST.get('exercise', '')
        sess.smoking      = request.POST.get('smoking') == 'yes'
        sess.alcohol      = request.POST.get('alcohol', '')
        sess.save(update_fields=['sleep_hours','stress_level','exercise','smoking','alcohol'])

    elif step == 9:
        sess.food_habits = request.POST.getlist('food_habits')
        sess.save(update_fields=['food_habits'])

    elif step == 10:
        routine = request.POST.getlist('routine_items')
        sess.morning_cleanser = 'morning_cleanser' in routine
        sess.moisturizer      = 'moisturizer'      in routine
        sess.sunscreen        = 'sunscreen'        in routine
        sess.night_routine    = 'night_routine'    in routine
        sess.uses_retinol     = 'retinol'          in routine
        sess.uses_vitamin_c   = 'vitamin_c'        in routine
        sess.uses_niacinamide = 'niacinamide'      in routine
        sess.uses_exfoliation = 'exfoliation'      in routine
        sess.save(update_fields=[
            'morning_cleanser','moisturizer','sunscreen','night_routine',
            'uses_retinol','uses_vitamin_c','uses_niacinamide','uses_exfoliation',
        ])

    elif step == 11:
        makeup = request.POST.getlist('makeup_items')
        sess.wears_foundation    = 'foundation'    in makeup
        sess.wears_concealer     = 'concealer'     in makeup
        sess.wears_primer        = 'primer'        in makeup
        sess.wears_setting_spray = 'setting_spray' in makeup
        sess.sleeps_with_makeup  = request.POST.get('sleeps_with_makeup', '')
        sess.save(update_fields=[
            'wears_foundation','wears_concealer','wears_primer',
            'wears_setting_spray','sleeps_with_makeup',
        ])

    elif step == 12:
        medical = request.POST.getlist('medical_conditions')
        sess.is_pregnant        = 'pregnant'     in medical
        sess.is_breastfeeding   = 'breastfeeding'in medical
        sess.has_pcos           = 'pcos'         in medical
        sess.has_thyroid        = 'thyroid'      in medical
        sess.has_diabetes       = 'diabetes'     in medical
        sess.on_skin_medication = 'skin_medication' in medical
        sess.uses_isotretinoin  = 'isotretinoin'    in medical
        sess.uses_steroids      = 'steroids'        in medical
        sess.known_allergies    = request.POST.get('known_allergies', '').strip()
        sess.skin_type_result   = sess.compute_skin_type()
        sess.acne_severity      = sess.compute_acne_severity()
        sess.completed          = True
        sess.save()
        return redirect('skin:result', session_id=sess.id)

    if step < TOTAL_STEPS:
        sess.current_step = step + 1
        sess.save(update_fields=['current_step'])
        return redirect('skin:question', step=step + 1)

    return redirect('skin:result', session_id=sess.id)


def result(request, session_id):
    sess = get_object_or_404(SkinSession, id=session_id)
    skin_type = sess.skin_type_result or sess.compute_skin_type()

    # Ingredient recommendations
    ingredients = {
        'oily':        ['Niacinamide', 'Salicylic Acid (BHA)', 'Hyaluronic Acid', 'Zinc PCA', 'AHA toner'],
        'dry':         ['Hyaluronic Acid', 'Ceramides', 'Shea Butter', 'Peptides', 'Glycerin'],
        'combination': ['Niacinamide', 'Hyaluronic Acid', 'BHA (T-zone)', 'Ceramides', 'Vitamin C'],
        'sensitive':   ['Centella Asiatica', 'Aloe Vera', 'Ceramides', 'Allantoin', 'Oat Extract'],
        'normal':      ['Vitamin C', 'Retinol', 'Niacinamide', 'SPF 50', 'Hyaluronic Acid'],
    }
    avoid = {
        'oily':        ['Heavy oils', 'Coconut oil', 'Thick creams', 'Alcohol-based toners (dehydrating)'],
        'dry':         ['Alcohol-based products', 'Harsh physical scrubs', 'Sulfates', 'AHAs without moisturiser'],
        'combination': ['Heavy fragrance', 'Over-exfoliation', 'Pore-clogging oils'],
        'sensitive':   ['Fragrance', 'Parabens', 'Physical scrubs', 'Retinol (start slow)', 'Strong AHAs'],
        'normal':      ['Heavy fragrance products', 'Skipping SPF'],
    }

    # Routine
    routines = {
        'oily':        (['Gel cleanser', 'BHA toner', 'Niacinamide serum', 'Oil-free moisturiser', 'SPF 50'],
                        ['Foam cleanser', 'Salicylic acid treatment', 'Lightweight gel moisturiser']),
        'dry':         (['Cream cleanser', 'Hydrating toner', 'Hyaluronic acid serum', 'Rich moisturiser', 'SPF 30'],
                        ['Cleansing balm', 'Essence', 'Peptide serum', 'Ceramide cream']),
        'combination': (['Balancing cleanser', 'Niacinamide toner', 'Vitamin C serum', 'Light moisturiser', 'SPF 50'],
                        ['Double cleanse', 'AHA/BHA toner', 'Retinol (2×/week)', 'Moisturiser']),
        'sensitive':   (['Gentle cleanser', 'Centella toner', 'Aloe gel', 'Ceramide moisturiser', 'SPF 30+'],
                        ['Micellar water', 'Calming essence', 'Ceramide night cream']),
        'normal':      (['Gentle cleanser', 'Toner', 'Vitamin C serum', 'Moisturiser', 'SPF 50'],
                        ['Oil cleanser', 'Face wash', 'Retinol (3×/week)', 'Night cream']),
    }
    morning_routine, night_routine = routines.get(skin_type, routines['normal'])
    weekly_routine = ['Clay mask (1×/week — oily zones)', 'Hydrating sheet mask', 'Gentle exfoliation (1–2×/week)']

    # Acne
    acne_products = []
    if sess.acne_severity in ('mild', 'moderate', 'severe'):
        acne_products = ['Salicylic acid cleanser', 'Benzoyl peroxide 2.5% spot treatment', 'Niacinamide 10% serum']
    if sess.acne_severity == 'severe' or sess.has_cystic_acne:
        acne_products.append('⚠️ Consult a dermatologist for cystic/severe acne')

    pigment_products = []
    if sess.pigmentation_concerns:
        pigment_products = ['Vitamin C serum (AM)', 'Niacinamide serum', 'Brightening toner', 'SPF 50+ (non-negotiable)']

    needs_derm = any([
        sess.has_cystic_acne, sess.acne_severity == 'severe',
        sess.uses_isotretinoin, sess.on_skin_medication, sess.has_pcos, sess.has_thyroid,
    ])

    skin_labels = {'oily': 'Oily', 'dry': 'Dry', 'combination': 'Combination', 'normal': 'Normal', 'sensitive': 'Sensitive'}
    acne_labels = {'none': 'No Acne 🎉', 'mild': 'Mild Acne', 'moderate': 'Moderate Acne', 'severe': 'Severe Acne'}

    # AI confidence (simple rule-based score)
    score = 85 + min(10, len(sess.skin_concerns or []) * 2)
    if sess.completed: score = min(95, score + 3)

    return render(request, 'skin/result.html', {
        'sess': sess, 'skin_type': skin_type,
        'skin_type_label': skin_labels.get(skin_type, 'Normal'),
        'acne_label':      acne_labels.get(sess.acne_severity, 'No Acne'),
        'morning_routine': morning_routine, 'night_routine': night_routine,
        'weekly_routine':  weekly_routine,
        'acne_products':   acne_products, 'pigment_products': pigment_products,
        'needs_derm':      needs_derm,
        'recommended_ingredients': ingredients.get(skin_type, ingredients['normal']),
        'avoid_ingredients':       avoid.get(skin_type, []),
        'ai_confidence':   score,
    })
