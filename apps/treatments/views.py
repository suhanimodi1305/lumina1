"""
Treatment planning views
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from apps.scanner.models import ScanResult
from apps.products.models import Product
import logging

logger = logging.getLogger(__name__)

# Complete treatment mapping for all 12 skin concerns
TREATMENT_MAP = {
    'acne': [
        {
            'name': 'Potenza RF Microneedling',
            'priority': 1,
            'priority_label': 'Urgent',
            'best_for': ['Active inflammatory acne', 'Acne scarring', 'Oily skin with breakouts'],
            'cost_inr': '₹12,000 – ₹25,000 per session',
            'sessions': '4-6 sessions, 4 weeks apart',
            'expect': 'Significant reduction in active breakouts within 2-3 sessions. RF energy targets sebaceous glands while microneedling promotes healing and reduces scarring.',
            'clinic_type': 'Advanced dermatology clinic with RF devices'
        },
        {
            'name': 'Chemical Peel (Salicylic Acid)',
            'priority': 2,
            'priority_label': 'Recommended',
            'best_for': ['Comedonal acne', 'Mild inflammatory acne', 'Blackheads'],
            'cost_inr': '₹3,000 – ₹6,000 per session',
            'sessions': '4-6 sessions, 3 weeks apart',
            'expect': 'Unclogged pores and reduced inflammation. Exfoliates dead skin cells and regulates sebum production.',
            'clinic_type': 'Dermatology clinic or medical spa'
        }
    ],
    'pigmentation': [
        {
            'name': 'Pico Laser Treatment',
            'priority': 1,
            'priority_label': 'Urgent',
            'best_for': ['Stubborn melasma', 'Post-inflammatory hyperpigmentation', 'Sun damage'],
            'cost_inr': '₹15,000 – ₹35,000 per session',
            'sessions': '3-5 sessions, 4-6 weeks apart',
            'expect': 'Visible lightening of dark spots within 2-3 sessions. Pico laser shatters melanin without damaging surrounding tissue.',
            'clinic_type': 'Advanced laser clinic'
        },
        {
            'name': 'Q-Switch Nd:YAG Laser',
            'priority': 2,
            'priority_label': 'Recommended',
            'best_for': ['Age spots', 'Freckles', 'Post-acne marks'],
            'cost_inr': '₹8,000 – ₹18,000 per session',
            'sessions': '4-6 sessions, 6 weeks apart',
            'expect': 'Gradual fading of pigmented lesions. Safe for all skin types including Indian skin tones.',
            'clinic_type': 'Dermatology laser clinic'
        }
    ],
    'blackheads': [
        {
            'name': 'HydraFacial / Aqua Peel',
            'priority': 1,
            'priority_label': 'Urgent',
            'best_for': ['Clogged pores', 'Blackheads', 'Dull congested skin'],
            'cost_inr': '₹5,000 – ₹12,000 per session',
            'sessions': 'Monthly maintenance',
            'expect': 'Immediate extraction of blackheads and deep cleansing. Skin appears brighter and pores look refined instantly.',
            'clinic_type': 'Medical spa or dermatology clinic'
        },
        {
            'name': 'Carbon Laser Peel',
            'priority': 2,
            'priority_label': 'Recommended',
            'best_for': ['Enlarged pores', 'Oily skin', 'Persistent blackheads'],
            'cost_inr': '₹6,000 – ₹15,000 per session',
            'sessions': '4-6 sessions, monthly',
            'expect': 'Deep pore cleansing with laser technology. Reduces oil production and tightens pores.',
            'clinic_type': 'Laser dermatology clinic'
        }
    ],
    'large_pores': [
        {
            'name': 'PDRN Skin Booster Therapy',
            'priority': 2,
            'priority_label': 'Recommended',
            'best_for': ['Enlarged pores', 'Loss of skin elasticity', 'Aging skin'],
            'cost_inr': '₹18,000 – ₹35,000 per session',
            'sessions': '3-4 sessions, 3 weeks apart',
            'expect': 'Improved skin texture and elasticity. PDRN stimulates collagen production, naturally tightening pores over time.',
            'clinic_type': 'Advanced aesthetic clinic'
        },
        {
            'name': 'Aqua Peel + Niacinamide Infusion',
            'priority': 2,
            'priority_label': 'Recommended',
            'best_for': ['Oily skin with large pores', 'Texture issues'],
            'cost_inr': '₹6,000 – ₹14,000 per session',
            'sessions': 'Monthly',
            'expect': 'Immediate pore refinement and oil control. Niacinamide regulates sebum and minimizes pore appearance.',
            'clinic_type': 'Medical spa or dermatology clinic'
        }
    ],
    'aging': [
        {
            'name': 'Potenza RF Microneedling',
            'priority': 1,
            'priority_label': 'Urgent',
            'best_for': ['Wrinkles', 'Sagging skin', 'Loss of firmness'],
            'cost_inr': '₹15,000 – ₹30,000 per session',
            'sessions': '4-6 sessions, monthly',
            'expect': 'Significant collagen remodeling and skin tightening. Results improve progressively over 6 months.',
            'clinic_type': 'Advanced dermatology clinic'
        },
        {
            'name': 'Rejuran Healer (PDRN)',
            'priority': 2,
            'priority_label': 'Recommended',
            'best_for': ['Fine lines', 'Skin repair', 'Anti-aging maintenance'],
            'cost_inr': '₹20,000 – ₹40,000 per session',
            'sessions': '3-4 sessions, monthly',
            'expect': 'Enhanced skin regeneration and tissue repair. Korean favorite for natural anti-aging.',
            'clinic_type': 'Aesthetic dermatology clinic'
        }
    ],
    'fine_lines': [
        {
            'name': 'Exosome Therapy',
            'priority': 2,
            'priority_label': 'Recommended',
            'best_for': ['Early aging signs', 'Fine lines', 'Skin rejuvenation'],
            'cost_inr': '₹25,000 – ₹50,000 per session',
            'sessions': '3-4 sessions, 6 weeks apart',
            'expect': 'Cutting-edge regenerative treatment. Stimulates cellular renewal and reduces fine lines from within.',
            'clinic_type': 'Premium aesthetic clinic'
        },
        {
            'name': 'Hyaluronic Acid Skin Booster',
            'priority': 3,
            'priority_label': 'Maintenance',
            'best_for': ['Dehydration lines', 'Crepey skin', 'Plumpness'],
            'cost_inr': '₹12,000 – ₹25,000 per session',
            'sessions': '3 sessions, monthly, then maintenance',
            'expect': 'Deep dermal hydration that plumps fine lines. Skin looks dewy and youthful.',
            'clinic_type': 'Aesthetic clinic or medical spa'
        }
    ],
    'dryness': [
        {
            'name': 'Mesotherapy Skin Booster',
            'priority': 3,
            'priority_label': 'Maintenance',
            'best_for': ['Chronic dryness', 'Dehydrated skin', 'Barrier repair'],
            'cost_inr': '₹8,000 – ₹18,000 per session',
            'sessions': '3-4 sessions, monthly',
            'expect': 'Microinjections of hyaluronic acid and vitamins. Restores skin hydration from the inside.',
            'clinic_type': 'Dermatology clinic or medical spa'
        }
    ],
    'dark_circles': [
        {
            'name': 'Under Eye PRP (Platelet-Rich Plasma)',
            'priority': 2,
            'priority_label': 'Recommended',
            'best_for': ['Dark circles', 'Under eye hollowing', 'Fine lines'],
            'cost_inr': '₹10,000 – ₹22,000 per session',
            'sessions': '3-4 sessions, 4 weeks apart',
            'expect': 'Natural growth factors stimulate collagen. Reduces darkness and improves skin thickness under eyes.',
            'clinic_type': 'Aesthetic dermatology clinic'
        },
        {
            'name': 'Carboxytherapy',
            'priority': 3,
            'priority_label': 'Maintenance',
            'best_for': ['Vascular dark circles', 'Poor circulation'],
            'cost_inr': '₹5,000 – ₹12,000 per session',
            'sessions': '6-8 sessions, weekly',
            'expect': 'CO2 injections improve blood flow. Reduces bluish tint and puffiness.',
            'clinic_type': 'Aesthetic clinic'
        }
    ],
    'redness': [
        {
            'name': 'LED Light Therapy (Yellow/Green)',
            'priority': 2,
            'priority_label': 'Recommended',
            'best_for': ['Rosacea', 'Inflammation', 'Sensitive skin'],
            'cost_inr': '₹3,000 – ₹8,000 per session',
            'sessions': '8-12 sessions, weekly',
            'expect': 'Non-invasive anti-inflammatory treatment. Calms redness and strengthens capillaries.',
            'clinic_type': 'Dermatology clinic or medical spa'
        },
        {
            'name': 'Azelaic Acid Medical Peel',
            'priority': 2,
            'priority_label': 'Recommended',
            'best_for': ['Rosacea', 'Post-inflammatory erythema'],
            'cost_inr': '₹4,000 – ₹10,000 per session',
            'sessions': '4-6 sessions, monthly',
            'expect': 'Gentle peel that reduces redness and inflammation. Safe for sensitive skin.',
            'clinic_type': 'Dermatology clinic'
        }
    ],
    'dullness': [
        {
            'name': 'Glass Skin Program (Multi-modal)',
            'priority': 2,
            'priority_label': 'Recommended',
            'best_for': ['Dull skin', 'Uneven texture', 'Desire for glass skin effect'],
            'cost_inr': '₹15,000 – ₹35,000 per session',
            'sessions': '4-6 sessions, 3 weeks apart',
            'expect': 'Combination of hydrating boosters, gentle peels, and laser toning. Achieves Korean glass skin glow.',
            'clinic_type': 'K-Beauty focused aesthetic clinic'
        }
    ],
    'oiliness': [
        {
            'name': 'Botox for Oil Control',
            'priority': 3,
            'priority_label': 'Maintenance',
            'best_for': ['Excessive oiliness', 'Shiny T-zone'],
            'cost_inr': '₹12,000 – ₹25,000 per session',
            'sessions': 'Every 6-8 months',
            'expect': 'Micro-botox injections reduce sebum production. Controls oil without freezing expression.',
            'clinic_type': 'Aesthetic dermatology clinic'
        }
    ],
    'sensitivity': [
        {
            'name': 'Barrier Repair Therapy',
            'priority': 2,
            'priority_label': 'Recommended',
            'best_for': ['Compromised barrier', 'Reactive skin'],
            'cost_inr': '₹8,000 – ₹15,000 per session',
            'sessions': '4 sessions, monthly',
            'expect': 'Customized treatment with ceramides and growth factors. Rebuilds skin barrier and reduces reactivity.',
            'clinic_type': 'Dermatology clinic'
        }
    ]
}


@login_required
def plan(request, scan_id):
    """
    Display personalized treatment plan based on scan results
    """
    # Get scan result
    scan = get_object_or_404(ScanResult, id=scan_id)
    
    # Verify ownership
    if scan.user != request.user and scan.session_key != request.session.session_key:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("You don't have permission to view this treatment plan.")
    
    logger.info(f"Generating treatment plan for scan {scan_id}")
    
    # Collect all treatments for detected concerns
    all_treatments = []
    seen_treatments = set()  # To deduplicate by name
    
    for concern in scan.detected_concerns.all():
        treatments = TREATMENT_MAP.get(concern.slug, [])
        
        for treatment in treatments:
            # Deduplicate by treatment name
            if treatment['name'] not in seen_treatments:
                # Add concern reference
                treatment_with_concern = treatment.copy()
                treatment_with_concern['concern'] = concern
                all_treatments.append(treatment_with_concern)
                seen_treatments.add(treatment['name'])
    
    # Sort by priority (1 = Urgent first)
    all_treatments.sort(key=lambda t: t['priority'])
    
    # Get post-treatment SAS products
    post_treatment_products = Product.objects.filter(
        product_range='korean',
        category__in=['serum', 'cream', 'mask']
    )[:3]
    
    context = {
        'scan': scan,
        'treatments': all_treatments,
        'post_treatment_products': post_treatment_products,
        'total_treatments': len(all_treatments)
    }
    
    return render(request, 'treatments/plan.html', context)