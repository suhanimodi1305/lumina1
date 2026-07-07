"""
Results views for displaying skin analysis results
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from apps.scanner.models import ScanResult
from apps.products.models import SkinConcern, Product
from apps.scanner.mediapipe_face_shape import get_face_shape_makeup_tips, FACE_SHAPE_MAKEUP_GUIDE
import logging
import json

logger = logging.getLogger(__name__)


def _call_groq(prompt, system="You are a helpful assistant. Respond with valid JSON only.", max_tokens=1200):
    """Shared Groq call helper — never surfaces API errors to end users."""
    try:
        from django.conf import settings
        from groq import Groq
        client = Groq(api_key=getattr(settings, 'GROQ_API_KEY', ''))
        response = client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=[
                {'role': 'system', 'content': system},
                {'role': 'user', 'content': prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.3,
        )
        text = response.choices[0].message.content.strip()
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0].strip()
        elif '```' in text:
            text = text.split('```')[1].split('```')[0].strip()
        return json.loads(text)
    except Exception as e:
        # Log internally — never propagate to the view/template
        logger.error(f"Groq call failed: {e}")
        return {}


def _generate_makeup_routine(scan):
    """Generate personalised 8-step makeup routine based on scan data."""
    concerns = ', '.join([c.name for c in scan.detected_concerns.all()[:5]]) or 'none detected'
    prompt = f"""You are a professional makeup artist. Based on these skin analysis results,
give a personalised 8-step makeup routine with EXACT products, shades, and prices in INR.

SKIN DATA:
- Skin type: {scan.skin_type}
- Undertone: {scan.undertone}
- Skin tone: {scan.skin_tone}
- Face shape: {scan.face_shape}
- Acne severity: {scan.hf_acne_severity}
- Main concerns: {concerns}

RULES:
- Choose from: Maybelline, MAC, Fenty Beauty, NYX, Lakme, Sugar, L'Oreal, Huda Beauty, Swiss Beauty
- EXACT product name + shade — NOT generic
- Foundation: warm=NC shade, cool=NW shade, neutral=N shade — matched to skin tone
- Oily: matte/oil-free. Dry: hydrating/dewy. Combination: balanced
- Acne skin: non-comedogenic only

Return ONLY this JSON:
{{
  "step1_moisturizer": {{"product": "exact name", "brand": "brand", "reason": "why for {scan.skin_type} skin", "price_inr": "₹XXX"}},
  "step2_primer": {{"product": "exact name", "brand": "brand", "reason": "why", "price_inr": "₹XXX"}},
  "step3_foundation": {{"product": "exact name + shade", "brand": "brand", "shade": "exact shade code", "reason": "why for {scan.undertone} undertone {scan.skin_tone} tone", "price_inr": "₹XXX"}},
  "step4_concealer": {{"product": "exact name + shade", "brand": "brand", "shade": "shade", "reason": "why", "price_inr": "₹XXX"}},
  "step5_powder": {{"product": "exact name", "brand": "brand", "reason": "why", "price_inr": "₹XXX"}},
  "step6_blush": {{"product": "exact name + shade", "brand": "brand", "shade": "shade name", "reason": "why for {scan.undertone} undertone", "price_inr": "₹XXX"}},
  "step7_eyeshadow": {{"product": "exact palette name", "brand": "brand", "shades": "suggested shades", "reason": "why", "price_inr": "₹XXX"}},
  "step8_lipstick": {{"product": "exact name + shade", "brand": "brand", "shade": "shade name", "reason": "why for {scan.undertone} undertone", "price_inr": "₹XXX"}}
}}"""
    return _call_groq(prompt, system="You are a professional makeup artist. Always respond with valid JSON only.")


def _generate_kbeauty_routine(scan):
    """Generate personalised K-Beauty routine based on scan data."""
    concerns = ', '.join([c.name for c in scan.detected_concerns.all()[:5]]) or 'general skin health'
    prompt = f"""You are a Korean skincare (K-Beauty) specialist. Based on these results,
create a personalised K-Beauty routine with EXACT product recommendations and K-Beauty brand suggestions.

SKIN DATA:
- Skin type: {scan.skin_type}
- Undertone: {scan.undertone}
- Skin tone: {scan.skin_tone}
- Acne severity: {scan.hf_acne_severity}
- Main concerns: {concerns}
- Key focus: {'acne control' if scan.hf_acne_severity in ['moderate','severe'] else 'brightening and hydration' if scan.skin_type == 'dry' else 'pore control and oil balance' if scan.skin_type == 'oily' else 'balancing and glow'}

Give AM and PM routines with steps + specific products from K-Beauty brands.
Brands to use: COSRX, Innisfree, Laneige, Some By Mi, The Ordinary, Klairs, Purito, Cetaphil (for sensitive), La Roche-Posay, Dermalogica, or SAS Global for Korean products.

Return ONLY this JSON:
{{
  "skin_focus": "1 sentence on what this person's skin needs most",
  "morning": [
    {{"step": 1, "name": "Oil/Foam Cleanser", "product": "exact product", "brand": "brand", "reason": "why", "price_inr": "₹XXX"}},
    {{"step": 2, "name": "Toner", "product": "exact product", "brand": "brand", "reason": "why", "price_inr": "₹XXX"}},
    {{"step": 3, "name": "Essence/Serum", "product": "exact product", "brand": "brand", "reason": "why for this concern", "price_inr": "₹XXX"}},
    {{"step": 4, "name": "Moisturiser", "product": "exact product", "brand": "brand", "reason": "why", "price_inr": "₹XXX"}},
    {{"step": 5, "name": "Sunscreen SPF50+", "product": "exact product", "brand": "brand", "reason": "non-negotiable in K-Beauty", "price_inr": "₹XXX"}}
  ],
  "evening": [
    {{"step": 1, "name": "Oil Cleanser", "product": "exact product", "brand": "brand", "reason": "remove SPF/makeup", "price_inr": "₹XXX"}},
    {{"step": 2, "name": "Foam Cleanser", "product": "exact product", "brand": "brand", "reason": "double cleanse", "price_inr": "₹XXX"}},
    {{"step": 3, "name": "Treatment Toner", "product": "exact product", "brand": "brand", "reason": "why for this concern", "price_inr": "₹XXX"}},
    {{"step": 4, "name": "Active Serum", "product": "exact product", "brand": "brand", "reason": "targeted treatment", "price_inr": "₹XXX"}},
    {{"step": 5, "name": "Night Cream", "product": "exact product", "brand": "brand", "reason": "why", "price_inr": "₹XXX"}}
  ],
  "weekly": [
    {{"name": "Exfoliator", "product": "exact product", "brand": "brand", "frequency": "2x/week", "reason": "why", "price_inr": "₹XXX"}},
    {{"name": "Sheet Mask", "product": "exact product", "brand": "brand", "frequency": "3x/week", "reason": "why for this concern", "price_inr": "₹XXX"}}
  ]
}}"""
    return _call_groq(prompt, system="You are a K-Beauty specialist. Always respond with valid JSON only.", max_tokens=1500)


def _parse_vision_data(scan):
    """Extract vision data + generate makeup/kbeauty routines if missing or incomplete."""
    try:
        raw = json.loads(scan.hf_acne_raw or '{}')
    except Exception:
        raw = {}

    makeup_routine  = raw.get('makeup_routine', {})
    kbeauty_routine = raw.get('kbeauty_routine', {})

    # Validate makeup routine has expected keys (not an empty dict or partial result)
    makeup_complete = (
        isinstance(makeup_routine, dict)
        and makeup_routine.get('step3_foundation')  # foundation is the critical step
    )
    # Validate kbeauty routine has morning steps
    kbeauty_complete = (
        isinstance(kbeauty_routine, dict)
        and kbeauty_routine.get('morning')
        and len(kbeauty_routine['morning']) >= 3
    )

    if not makeup_complete:
        logger.info(f"Generating makeup routine for scan {scan.id}…")
        makeup_routine = _generate_makeup_routine(scan)
        # Cache back into hf_acne_raw so we don't regenerate on every page load
        if makeup_routine:
            raw['makeup_routine'] = makeup_routine
            try:
                scan.hf_acne_raw = json.dumps(raw)
                scan.save(update_fields=['hf_acne_raw'])
            except Exception as e:
                logger.error(f"Failed to cache makeup routine: {e}")

    if not kbeauty_complete:
        logger.info(f"Generating K-Beauty routine for scan {scan.id}…")
        kbeauty_routine = _generate_kbeauty_routine(scan)
        if kbeauty_routine:
            raw['kbeauty_routine'] = kbeauty_routine
            try:
                scan.hf_acne_raw = json.dumps(raw)
                scan.save(update_fields=['hf_acne_raw'])
            except Exception as e:
                logger.error(f"Failed to cache kbeauty routine: {e}")

    return {
        'foundation_shade':  raw.get('foundation_shade', ''),
        'foundation_brand':  raw.get('foundation_brand', ''),
        'face_shape_reason': raw.get('face_shape_reason', ''),
        'kbeauty_focus':     raw.get('kbeauty_focus', ''),
        'analysis_notes':    raw.get('analysis_notes', ''),
        'makeup_routine':    makeup_routine,
        'kbeauty_routine':   kbeauty_routine,
    }
# Complete dermatological information for all 12 skin concerns
CONDITION_INFO = {
    'acne': {
        'display': 'Acne',
        'description': 'Active acne is characterized by inflamed papules, pustules, and comedones caused by clogged hair follicles and bacterial infection.',
        'causes': [
            'Excess sebum production clogging hair follicles',
            'Bacterial overgrowth of Cutibacterium acnes',
            'Hormonal fluctuations increasing oil production'
        ],
        'advice': 'Maintain consistent cleansing routine, avoid touching face, use non-comedogenic products, and consider professional treatment for severe cases.',
        'medicine_options': [
            'Clindamycin Phosphate 1% gel (apply twice daily)',
            'Benzoyl Peroxide 2.5% face wash (morning cleanse)',
            'Adapalene 0.1% cream (OTC, apply at night)'
        ],
        'use_ingredients': ['Niacinamide', 'Salicylic Acid BHA', 'Centella Asiatica', 'Tea Tree'],
        'avoid_ingredients': ['Heavy mineral oils', 'Coconut oil', 'Comedogenic silicones', 'Isopropyl myristate'],
        'dermatologist': 'no'
    },
    'dark_circles': {
        'display': 'Dark Circles',
        'description': 'Periorbital hyperpigmentation and vascular pooling under the eyes, often appearing as dark shadowing in the under-eye area.',
        'causes': [
            'Iron deficiency reducing oxygen to under-eye blood vessels',
            'Chronic sleep deprivation increasing vascular pooling',
            'Thin periorbital skin revealing underlying vasculature'
        ],
        'advice': 'Get adequate sleep (7-9 hours), use caffeine-based eye creams, consider cold compresses, and consult a doctor if anemia is suspected.',
        'medicine_options': [
            'Caffeine 0.5% eye gel (apply morning and night)',
            'Vitamin K cream (reduces vascular pigment)',
            'Iron supplement if anaemia confirmed by blood test'
        ],
        'use_ingredients': ['Caffeine', 'Vitamin K', 'Peptides', 'Hyaluronic Acid'],
        'avoid_ingredients': ['Retinol directly under eyes', 'Strong AHAs near eye area'],
        'dermatologist': 'recommended'
    },
    'pigmentation': {
        'display': 'Pigmentation',
        'description': 'Hyperpigmentation manifests as dark spots, melasma, or post-inflammatory marks caused by excess melanin production.',
        'causes': [
            'Chronic UV exposure without SPF protection',
            'Post-inflammatory hyperpigmentation from healed acne',
            'Hormonal changes causing melasma in predisposed individuals'
        ],
        'advice': 'Daily SPF 50+ is mandatory, use brightening serums with vitamin C, avoid picking at skin, and consider professional treatments for stubborn spots.',
        'medicine_options': [
            'Hydroquinone 2% cream (prescription in India, use cautiously)',
            'Azelaic Acid 10% cream (OTC, morning and night)',
            'Kojic Acid + Niacinamide serum'
        ],
        'use_ingredients': ['Vitamin C 15%', 'Niacinamide 10%', 'Alpha Arbutin', 'Azelaic Acid', 'SPF50+'],
        'avoid_ingredients': ['Fragrance-heavy products', 'Alcohol-based toners', 'Unprotected sun exposure'],
        'dermatologist': 'recommended'
    },
    'blackheads': {
        'display': 'Blackheads',
        'description': 'Open comedones where sebum oxidizes upon contact with air, creating characteristic black appearance in pores.',
        'causes': [
            'Excess sebum oxidizing on skin surface turning black',
            'Incomplete daily cleansing allowing oil to set in pores',
            'High-glycemic diet spiking insulin and oil production'
        ],
        'advice': 'Double cleanse daily, use BHA exfoliants 2-3 times weekly, avoid manual extraction, and maintain consistent skincare routine.',
        'medicine_options': [
            'Salicylic Acid 2% BHA cleanser (use daily)',
            'Sulfur 10% clay mask (1-2 times per week)',
            'LHA 0.1% toner pads (3 times per week)'
        ],
        'use_ingredients': ['BHA Salicylic Acid', 'LHA', 'Clay', 'Niacinamide'],
        'avoid_ingredients': ['Heavy creams over T-zone', 'Manual squeezing', 'Pore strips'],
        'dermatologist': 'no'
    },
    'dryness': {
        'display': 'Dryness',
        'description': 'Xerosis characterized by compromised skin barrier, flaking, tightness, and increased trans-epidermal water loss.',
        'causes': [
            'Impaired epidermal barrier increasing trans-epidermal water loss',
            'Low ambient humidity desiccating the stratum corneum',
            'Over-cleansing with harsh sulfate surfactants stripping natural oils'
        ],
        'advice': 'Use gentle cleansers, apply moisturizer on damp skin, use humidifier, avoid hot water, and layer hydrating products.',
        'medicine_options': [
            'Ceramide NP barrier repair cream (apply morning and night)',
            'Glycerin 10% + Hyaluronic Acid serum',
            'Petrolatum ointment as overnight barrier occlusive'
        ],
        'use_ingredients': ['Hyaluronic Acid', 'Ceramides', 'Squalane', 'Glycerin', 'Shea Butter'],
        'avoid_ingredients': ['Sulfate cleansers', 'High-percentage AHAs', 'Alcohol-based toners'],
        'dermatologist': 'no'
    },
    'redness': {
        'display': 'Redness',
        'description': 'Erythema and inflammation indicating compromised barrier function, rosacea, or allergic reaction.',
        'causes': [
            'Compromised skin barrier allowing irritant penetration',
            'Rosacea — a chronic inflammatory vascular condition',
            'Allergen sensitization triggering immune response'
        ],
        'advice': 'Identify and eliminate triggers, use gentle fragrance-free products, apply soothing ingredients, and protect from extreme temperatures.',
        'medicine_options': [
            'Metronidazole 0.75% gel (prescription for rosacea)',
            'Azelaic Acid 15% gel (OTC, anti-inflammatory)',
            'Allantoin 0.5% soothing cream'
        ],
        'use_ingredients': ['Centella Asiatica', 'Guaiazulem', 'Allantoin', 'Green Tea Extract'],
        'avoid_ingredients': ['Fragrance', 'Essential oils', 'High-strength AHAs and BHAs', 'Alcohol-based products'],
        'dermatologist': 'recommended'
    },
    'fine_lines': {
        'display': 'Fine Lines',
        'description': 'Early-stage wrinkles caused by natural collagen degradation, photoaging, and repetitive facial expressions.',
        'causes': [
            'Natural collagen decline beginning at approximately age 25',
            'UV-induced photoaging degrading collagen and elastin fibers',
            'Chronic dehydration reducing dermal volume and plumpness'
        ],
        'advice': 'Daily SPF is critical, use retinoids consistently, stay hydrated, avoid smoking, and consider professional treatments for deeper lines.',
        'medicine_options': [
            'Retinol 0.5% serum (start twice weekly)',
            'Tretinoin 0.025% cream (prescription — most effective)',
            'Peptide complex cream (OTC, use morning and night)'
        ],
        'use_ingredients': ['Retinol', 'Peptides', 'Hyaluronic Acid', 'Vitamin C', 'PDRN'],
        'avoid_ingredients': ['Unprotected sun exposure', 'Smoking', 'Physical scrubbing'],
        'dermatologist': 'no'
    },
    'large_pores': {
        'display': 'Large Pores',
        'description': 'Visibly enlarged pore openings caused by excess sebum, loss of elasticity, and genetic factors.',
        'causes': [
            'Excess sebum production stretching pore openings over time',
            'UV-induced loss of skin elasticity allowing pores to sag',
            'Genetic predisposition determining baseline pore size'
        ],
        'advice': 'Use pore-refining ingredients like niacinamide, exfoliate regularly with BHA, avoid heavy creams on T-zone, and maintain oil control.',
        'medicine_options': [
            'Niacinamide 10% serum (apply twice daily)',
            'Salicylic Acid 2% BHA toner (3 times per week)',
            'Retinol 0.3% gel (apply at night twice weekly)'
        ],
        'use_ingredients': ['Niacinamide', 'Salicylic Acid', 'Retinol', 'Clay'],
        'avoid_ingredients': ['Heavy occlusive creams over oily zones', 'Alcohol-based astringents'],
        'dermatologist': 'no'
    },
    'aging': {
        'display': 'Aging Signs',
        'description': 'Visible signs of skin aging including wrinkles, loss of firmness, and decreased elasticity.',
        'causes': [
            'Intrinsic collagen decline reducing structural support after 25',
            'Extrinsic UV photoaging causing 80% of visible skin aging',
            'Oxidative stress from pollution and free radicals degrading skin'
        ],
        'advice': 'Prevention is key: daily SPF, antioxidants, retinoids, and professional treatments. Lifestyle factors like diet and sleep are crucial.',
        'medicine_options': [
            'Tretinoin 0.05% cream (prescription, gold standard)',
            'PDRN topical serum (stimulates tissue regeneration)',
            'Peptide complex serum (OTC collagen support)'
        ],
        'use_ingredients': ['PDRN', 'Retinol', 'Peptides', 'Vitamin C', 'SPF50+'],
        'avoid_ingredients': ['Unprotected UV exposure', 'Crash dieting', 'Smoking'],
        'dermatologist': 'recommended'
    },
    'oiliness': {
        'display': 'Oiliness',
        'description': 'Excessive sebum production leading to shiny skin, enlarged pores, and increased acne risk.',
        'causes': [
            'Genetically overactive sebaceous glands producing excess sebum',
            'Rebound oil production triggered by over-cleansing',
            'Androgen hormones stimulating increased sebaceous activity'
        ],
        'advice': 'Gentle cleansing only twice daily, use lightweight hydration, apply sebum-regulating ingredients, and avoid over-drying products.',
        'medicine_options': [
            'Niacinamide 10% serum (regulates sebum)',
            'Zinc PCA lotion (reduces oil production)',
            'Salicylic Acid 0.5% daily cleanser'
        ],
        'use_ingredients': ['Niacinamide', 'BHA', 'Zinc', 'Clay', 'Lightweight Hyaluronic Acid'],
        'avoid_ingredients': ['Heavy creams', 'Facial oils', 'Cleansing more than twice daily'],
        'dermatologist': 'no'
    },
    'dullness': {
        'display': 'Dullness',
        'description': 'Lackluster complexion with uneven texture and reduced radiance due to dead cell buildup.',
        'causes': [
            'Buildup of dead skin cells reducing light reflection',
            'Dehydration reducing dermal volume and skin translucency',
            'Poor microcirculation reducing oxygen delivery to skin cells'
        ],
        'advice': 'Regular exfoliation, vitamin C for brightening, adequate hydration, and improved circulation through exercise and massage.',
        'medicine_options': [
            'Vitamin C 15% serum (morning antioxidant + brightener)',
            'Glycolic Acid 8% toner (exfoliates dead cells)',
            'Niacinamide 5% brightening serum'
        ],
        'use_ingredients': ['Vitamin C', 'AHA Glycolic Acid', 'Niacinamide', 'Hyaluronic Acid'],
        'avoid_ingredients': ['Skipping SPF (worsens dullness)', 'Thick heavy creams blocking renewal'],
        'dermatologist': 'no'
    },
    'sensitivity': {
        'display': 'Sensitivity',
        'description': 'Reactive skin that easily becomes irritated, red, or inflamed in response to products or environmental factors.',
        'causes': [
            'Impaired skin barrier allowing penetration of irritants and allergens',
            'Overuse of active ingredients destroying the microbiome',
            'Allergic contact dermatitis from product ingredients'
        ],
        'advice': 'Strip routine to basics, patch test new products, avoid known irritants, and rebuild barrier with ceramides and soothing ingredients.',
        'medicine_options': [
            'Allantoin 0.5% barrier cream',
            'Centella Asiatica 70% extract serum',
            'Ceramide NP repair barrier cream'
        ],
        'use_ingredients': ['Centella Asiatica', 'Allantoin', 'Ceramides', 'Aloe Vera'],
        'avoid_ingredients': ['Fragrance', 'Essential oils', 'AHAs/BHAs during flare', 'All actives during reaction'],
        'dermatologist': 'recommended'
    }
}


def determine_severity(concern_slug, scan):
    """
    Determine severity level based on scan scores
    
    Args:
        concern_slug: The skin concern slug
        scan: ScanResult object
    
    Returns:
        str: 'mild', 'moderate', or 'severe'
    """
    severity_map = {
        'acne': scan.acne_score,
        'blackheads': scan.acne_score,
        'oiliness': scan.acne_score if scan.skin_type == 'oily' else 20,
        'pigmentation': scan.pigmentation_score,
        'dryness': 100 - scan.hydration_score,  # Inverted
        'dark_circles': 100 - scan.hydration_score,
        'redness': scan.acne_score if scan.hf_acne_severity in ['moderate', 'severe'] else 20,
        'large_pores': scan.acne_score if scan.skin_type == 'oily' else 30,
        'aging': scan.aging_score,
        'fine_lines': scan.aging_score,
        'dullness': 100 - scan.harmony_score,
        'sensitivity': 100 - scan.elasticity_score
    }
    
    score = severity_map.get(concern_slug, 30)
    
    if score < 30:
        return 'mild'
    elif score < 60:
        return 'moderate'
    else:
        return 'severe'


def skin_results(request, scan_id):
    """
    Display complete skin analysis results
    """
    # Get scan result
    scan = get_object_or_404(ScanResult, id=scan_id)
    
    logger.info(f"Displaying results for scan {scan_id}")
    
    # Build condition cards with dermatology info and products
    condition_cards = []
    
    for concern in scan.detected_concerns.all():
        # Get condition info
        info = CONDITION_INFO.get(concern.slug, {})
        
        if not info:
            logger.warning(f"No condition info found for {concern.slug}")
            continue
        
        # Determine severity
        severity = determine_severity(concern.slug, scan)
        
        # Query Korean products for this concern (SQLite-safe: filter in Python)
        all_korean_for_concern = list(
            Product.objects.filter(product_range='korean').order_by('-is_featured', 'brand', 'name')
        )
        korean_products = [
            p for p in all_korean_for_concern
            if concern.slug in (p.targets or [])
        ][:3]
        # If no concern-targeted products found, fall back to skin-type matched
        if not korean_products:
            korean_products = [
                p for p in all_korean_for_concern
                if scan.skin_type in (p.suitable_for_skin_types or []) or 'all' in (p.suitable_for_skin_types or [])
            ][:3]
        
        # Build card data
        card = {
            'concern': concern,
            'display': info['display'],
            'description': info['description'],
            'causes': info['causes'],
            'advice': info['advice'],
            'medicine_options': info['medicine_options'],
            'use_ingredients': info['use_ingredients'],
            'avoid_ingredients': info['avoid_ingredients'],
            'dermatologist': info['dermatologist'],
            'severity': severity,
            'korean_products': korean_products
        }
        
        condition_cards.append(card)
    
    # Query makeup products filtered by undertone and skin tone from scan
    def _makeup_qs(category):
        """Return products matching category, preferring undertone/skin-tone match.
        Falls back progressively: undertone+tone → undertone only → any in category.
        """
        qs = Product.objects.filter(product_range='makeup', category=category)
        if not qs.exists():
            return []
        # Best match: undertone + skin_tone
        matched = qs.filter(
            undertone_match=scan.undertone,
            skin_tone_match=scan.skin_tone,
        )
        if matched.exists():
            return list(matched[:6])
        # Second: undertone only
        matched = qs.filter(undertone_match=scan.undertone)
        if matched.exists():
            return list(matched[:6])
        # Third: skin_tone only
        matched = qs.filter(skin_tone_match=scan.skin_tone)
        if matched.exists():
            return list(matched[:6])
        # Final fallback: featured first, then all
        featured = qs.filter(is_featured=True)
        if featured.exists():
            return list(featured[:6])
        return list(qs[:6])

    foundations = _makeup_qs('foundation')
    concealers  = _makeup_qs('concealer')
    blushes     = _makeup_qs('blush')
    lipsticks   = _makeup_qs('lipstick')
    
    # ── K-Beauty products from DB — filtered to this user's skin type & concerns
    # JSONField __contains doesn't work on SQLite — filter in Python instead
    concern_slugs = list(scan.detected_concerns.values_list('slug', flat=True))

    all_korean = list(Product.objects.filter(product_range='korean').order_by('category', 'brand'))

    # Split into concern-matched and skin-type-matched lists
    kbeauty_by_concern = [
        p for p in all_korean
        if concern_slugs and any(slug in (p.targets or []) for slug in concern_slugs)
    ]
    kbeauty_by_skin = [
        p for p in all_korean
        if scan.skin_type in (p.suitable_for_skin_types or [])
        or 'all' in (p.suitable_for_skin_types or [])
    ]

    # Combine deduplicated: concern-matched first, then skin-type matched, then all
    seen_ids = set()
    ordered_kbeauty = []
    for p in kbeauty_by_concern + kbeauty_by_skin + all_korean:
        if p.id not in seen_ids:
            seen_ids.add(p.id)
            ordered_kbeauty.append(p)

    # IMPORTANT: {% regroup %} requires items sorted by the grouping key (category)
    ordered_kbeauty.sort(key=lambda p: p.category or '')
    kbeauty_products_final = ordered_kbeauty[:20]

    def _best_korean(category, name_hint=None):
        """Return best-matched Korean product for given category.
        Priority: concern-match + skin-type → skin-type only → any in category.
        """
        concern_slugs_local = list(scan.detected_concerns.values_list('slug', flat=True))
        qs = list(Product.objects.filter(product_range='korean', category=category))

        if not qs:
            return None

        if name_hint:
            hint_qs = [p for p in qs if name_hint.lower() in (p.name or '').lower()]
            if hint_qs:
                qs = hint_qs

        # Score each product: concern match = 2 pts, skin-type match = 1 pt
        def _score(p):
            score = 0
            targets = p.targets or []
            suitable = p.suitable_for_skin_types or []
            if concern_slugs_local and any(slug in targets for slug in concern_slugs_local):
                score += 2
            if scan.skin_type in suitable or 'all' in suitable:
                score += 1
            return score

        qs.sort(key=_score, reverse=True)
        return qs[0] if qs else None

    # Build Korean skincare routine (used on Screen 1 — Recommended Regimen)
    morning_routine = [
        {'step': 1, 'name': 'Cleanser',    'product_type': 'cleanser',    'product': _best_korean('cleanser')},
        {'step': 2, 'name': 'Toner',       'product_type': 'toner',       'product': _best_korean('toner')},
        {'step': 3, 'name': 'Serum',       'product_type': 'serum',       'product': _best_korean('serum')},
        {'step': 4, 'name': 'Moisturizer', 'product_type': 'moisturizer', 'product': _best_korean('moisturizer')},
        {'step': 5, 'name': 'Sunscreen',   'product_type': 'sunscreen',   'product': _best_korean('sunscreen')},
    ]

    evening_routine = [
        {'step': 1, 'name': 'Oil Cleanser',  'product_type': 'cleanser',    'product': _best_korean('cleanser', 'oil')},
        {'step': 2, 'name': 'Foam Cleanser', 'product_type': 'cleanser',    'product': _best_korean('cleanser')},
        {'step': 3, 'name': 'Toner',         'product_type': 'toner',       'product': _best_korean('toner')},
        {'step': 4, 'name': 'Treatment',     'product_type': 'serum',       'product': _best_korean('serum')},
        {'step': 5, 'name': 'Night Cream',   'product_type': 'moisturizer', 'product': _best_korean('moisturizer', 'night') or _best_korean('moisturizer')},
    ]
    
    # Facial zones data
    facial_zones = scan.facial_zones if scan.facial_zones else {
        'forehead': 'none',
        'nose': 'none',
        'left_cheek': 'none',
        'right_cheek': 'none',
        'chin': 'none'
    }
    
    # Treatment preview
    treatment_preview = {
        'duration': '8 weeks',
        'steps': len(morning_routine) + len(evening_routine),
        'products': Product.objects.filter(product_range='korean').count()
    }
    
    # ── DERIVED METRIC SCORES (accurate — no hardcoded defaults) ──────────────
    # Oiliness: skin_type is the primary signal; hydration inversely contributes.
    # oily=high, combination=moderate, normal/dry=low, adjusted by hydration.
    _skin_type_oil_base = {
        'oily': 80,
        'combination': 55,
        'normal': 25,
        'dry': 10,
    }
    oiliness_base = _skin_type_oil_base.get(scan.skin_type, 25)
    # Hydration correction: low hydration slightly raises oiliness (rebound oil)
    hydration_correction = max(0, (50 - scan.hydration_score) // 5)  # 0–10 pts
    oiliness_pct = min(100, oiliness_base + hydration_correction)

    # Large Pores: driven by acne_score (sebum stretches pores) + elasticity loss
    # low elasticity = pores look larger; oily/combination skin amplifies it.
    elasticity_pore_factor = max(0, (70 - scan.elasticity_score) // 3)  # 0–23 pts
    _skin_type_pore_base = {
        'oily': max(35, scan.acne_score),
        'combination': max(25, scan.acne_score // 2 + 15),
        'normal': max(15, scan.acne_score // 3),
        'dry': max(10, scan.acne_score // 4),
    }
    pore_pct = min(100, _skin_type_pore_base.get(scan.skin_type, 20) + elasticity_pore_factor)
    # ──────────────────────────────────────────────────────────────────────────

    context = {
        'scan': scan,
        'condition_cards': condition_cards,
        'foundations': foundations,
        'concealers': concealers,
        'blushes': blushes,
        'lipsticks': lipsticks,
        'morning_routine': morning_routine,
        'evening_routine': evening_routine,
        'facial_zones': facial_zones,
        'treatment_preview': treatment_preview,
        # Derived metric scores (computed from actual scan data — no defaults)
        'oiliness_pct': oiliness_pct,
        'pore_pct': pore_pct,
        # K-Beauty products from database (korean range only)
        'kbeauty_products': kbeauty_products_final,
        # Parsed from hf_acne_raw (vision result)
        'vision_data': _parse_vision_data(scan),
        # Face shape makeup guide — based on actual detected face shape + undertone
        'face_shape_tips': get_face_shape_makeup_tips(scan.face_shape, scan.undertone),
        'all_face_shapes': list(FACE_SHAPE_MAKEUP_GUIDE.keys()),
    }
    
    return render(request, 'results/results.html', context)


def face_shape_api(request, scan_id):
    """
    JSON API endpoint — returns face shape detection data for a scan.
    Requires ownership: must be the scan's owner or the same session.

    GET /results/<scan_id>/face-shape-api/
    """
    scan = get_object_or_404(ScanResult, id=scan_id)

    # Ownership check — prevent enumeration of other users' scan data
    if scan.user:
        if not request.user.is_authenticated or scan.user != request.user:
            from django.http import JsonResponse as JR
            return JR({'error': 'Forbidden'}, status=403)
    elif scan.session_key and scan.session_key != request.session.session_key:
        from django.http import JsonResponse as JR
        return JR({'error': 'Forbidden'}, status=403)

    # Try to extract cached MediaPipe measurements from hf_acne_raw
    try:
        raw = json.loads(scan.hf_acne_raw or '{}')
    except Exception:
        raw = {}

    tips = get_face_shape_makeup_tips(scan.face_shape, scan.undertone)

    return JsonResponse({
        'scan_id':    scan_id,
        'face_shape': scan.face_shape,
        'confidence': raw.get('face_shape_confidence', 0),
        'reason':     raw.get('face_shape_reason', ''),
        'makeup_tips': tips,
        'measurements': raw.get('face_shape_measurements', {}),
        'ratios':     raw.get('face_shape_ratios', {}),
        'undertone':  scan.undertone,
        'skin_type':  scan.skin_type,
    })
