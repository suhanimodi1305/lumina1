"""
Product catalog views
"""
from django.shortcuts import render, get_object_or_404
from .models import Product
from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)


# Metadata for each SAS Global Korean range
KOREAN_RANGE_META = {
    "Resurrection Aesthetic Range": {
        "icon": "✨",
        "tagline": "Exosome-Powered Premium Care for Timeless Beauty",
        "desc": "Harnesses advanced exosome technology for barrier strengthening, tissue remodeling, and anti-aging effects. Ideal for mature, sensitive, or demanding skin.",
        "color": "#c9a96e",
    },
    "Differensea Blue Biome Repair Range": {
        "icon": "🌊",
        "tagline": "Advanced Barrier Repair & Soothing Solutions",
        "desc": "Replenishes the skin's natural barrier with the proprietary Blue Biome Complex. Soothes irritation, calms redness, and intensely hydrates sensitive and reactive skin.",
        "color": "#3b82f6",
    },
    "Revital Energy Line": {
        "icon": "🌿",
        "tagline": "Centella-Powered Daily Barrier & Glow Solutions",
        "desc": "Powered by Houttuynia Cordata and Centella Asiatica for balanced hydration, barrier support, and a naturally radiant glow. Suitable for all skin types.",
        "color": "#22c55e",
    },
    "Advance Formula Serum Range": {
        "icon": "🔬",
        "tagline": "Next-Generation Skin Repair & Hydration Technology",
        "desc": "Combines exosome technology with botanical actives and stabilized Vitamin C for advanced rejuvenation, soothing, hydration, and brightening.",
        "color": "#8b5cf6",
    },
    "Ultimate Repair Range": {
        "icon": "💊",
        "tagline": "Clinically Inspired Anti-Aging and Skin Barrier Restoration",
        "desc": "Formulated with retinol, 8-peptide complex, ceramides, and niacinamide for enhanced elasticity, reduced wrinkles, and long-lasting hydration.",
        "color": "#0891b2",
    },
    "Phyto PDRN Skin Boosting Range": {
        "icon": "⚗️",
        "tagline": "Boost Skin Elasticity & Renew Radiance with Advanced PDRN Therapy",
        "desc": "Combines high-purity PDRN (salmon DNA) with nourishing botanicals to rejuvenate skin at the cellular level. Improves elasticity and visibly reduces wrinkles.",
        "color": "#0d9488",
    },
    "Post-Laser & Post-Surgery Care": {
        "icon": "🩹",
        "tagline": "Advanced Soothing and Regeneration Solutions for Skin Recovery",
        "desc": "Supports and accelerates healing after laser treatments and dermatological procedures. Reduces redness, irritation, and discomfort while enhancing regeneration.",
        "color": "#f59e0b",
    },
    "Exolusion Time Rewinder": {
        "icon": "⏱️",
        "tagline": "Innovative Vibration Massager with Exosome-Infused Serum Technology",
        "desc": "Uses micro-vibrations to stimulate skin cell activity, enhance serum absorption, and promote firmer, smoother, radiant skin. For anti-wrinkle and brightening treatments.",
        "color": "#e91e63",
    },
}


def product_list(request):
    """
    Display complete product catalog with search + filter support.
    GET params: q (search), category, price, product_range, brand, skin_type, sort
    """
    from django.db.models import Q

    q             = request.GET.get('q', '').strip()
    category      = request.GET.get('category', '').strip()
    price         = request.GET.get('price', '').strip()
    product_range = request.GET.get('product_range', '').strip()   # 'korean' | 'makeup' | ''
    brand         = request.GET.get('brand', '').strip()
    skin_type     = request.GET.get('skin_type', '').strip()
    sort          = request.GET.get('sort', '').strip()            # 'price_asc' | 'price_desc' | 'name_asc' | 'newest'
    featured      = request.GET.get('featured', '').strip()        # '1' to show only featured

    # ── Base querysets ──
    korean_qs    = Product.objects.filter(product_range='korean')
    makeup_qs    = Product.objects.filter(product_range='makeup')
    ayurvedic_qs = Product.objects.filter(product_range='ayurvedic')
    pharmacy_qs  = Product.objects.filter(product_range='pharmacy')

    # ── Filter by product_range (show only one section) ──
    if product_range == 'korean':
        makeup_qs    = Product.objects.none()
        ayurvedic_qs = Product.objects.none()
        pharmacy_qs  = Product.objects.none()
    elif product_range == 'makeup':
        korean_qs    = Product.objects.none()
        ayurvedic_qs = Product.objects.none()
        pharmacy_qs  = Product.objects.none()
    elif product_range == 'ayurvedic':
        korean_qs   = Product.objects.none()
        makeup_qs   = Product.objects.none()
        pharmacy_qs = Product.objects.none()
    elif product_range == 'pharmacy':
        korean_qs    = Product.objects.none()
        makeup_qs    = Product.objects.none()
        ayurvedic_qs = Product.objects.none()

    # ── Apply search ──
    if q:
        q_filter = (
            Q(name__icontains=q) |
            Q(brand__icontains=q) |
            Q(description__icontains=q) |
            Q(key_ingredients__icontains=q) |
            Q(sku__icontains=q)
        )
        korean_qs    = korean_qs.filter(q_filter)
        makeup_qs    = makeup_qs.filter(q_filter)
        ayurvedic_qs = ayurvedic_qs.filter(q_filter)
        pharmacy_qs  = pharmacy_qs.filter(q_filter)

    # ── Apply category filter ──
    if category:
        korean_qs    = korean_qs.filter(category=category)
        makeup_qs    = makeup_qs.filter(category=category)
        ayurvedic_qs = ayurvedic_qs.filter(category=category)
        pharmacy_qs  = pharmacy_qs.filter(category=category)

    # ── Apply brand filter ──
    if brand:
        korean_qs    = korean_qs.filter(brand=brand)
        makeup_qs    = makeup_qs.filter(brand=brand)
        ayurvedic_qs = ayurvedic_qs.filter(brand=brand)
        pharmacy_qs  = pharmacy_qs.filter(brand=brand)

    # ── Apply skin type filter ──
    if skin_type:
        korean_qs    = korean_qs.filter(suitable_for_skin_types__contains=skin_type)
        makeup_qs    = makeup_qs.filter(suitable_for_skin_types__contains=skin_type)
        ayurvedic_qs = ayurvedic_qs.filter(suitable_for_skin_types__contains=skin_type)
        pharmacy_qs  = pharmacy_qs.filter(suitable_for_skin_types__contains=skin_type)

    # ── Apply featured filter ──
    if featured == '1':
        korean_qs    = korean_qs.filter(is_featured=True)
        makeup_qs    = makeup_qs.filter(is_featured=True)
        ayurvedic_qs = ayurvedic_qs.filter(is_featured=True)
        pharmacy_qs  = pharmacy_qs.filter(is_featured=True)

    # ── Apply price filter ──
    if price:
        if price == '0-500':
            korean_qs    = korean_qs.filter(price__lte=500)
            makeup_qs    = makeup_qs.filter(price__lte=500)
            ayurvedic_qs = ayurvedic_qs.filter(price__lte=500)
            pharmacy_qs  = pharmacy_qs.filter(price__lte=500)
        elif price == '500-1000':
            korean_qs    = korean_qs.filter(price__gte=500, price__lte=1000)
            makeup_qs    = makeup_qs.filter(price__gte=500, price__lte=1000)
            ayurvedic_qs = ayurvedic_qs.filter(price__gte=500, price__lte=1000)
            pharmacy_qs  = pharmacy_qs.filter(price__gte=500, price__lte=1000)
        elif price == '1000-2500':
            korean_qs    = korean_qs.filter(price__gte=1000, price__lte=2500)
            makeup_qs    = makeup_qs.filter(price__gte=1000, price__lte=2500)
            ayurvedic_qs = ayurvedic_qs.filter(price__gte=1000, price__lte=2500)
            pharmacy_qs  = pharmacy_qs.filter(price__gte=1000, price__lte=2500)
        elif price == '2500-5000':
            korean_qs    = korean_qs.filter(price__gte=2500, price__lte=5000)
            makeup_qs    = makeup_qs.filter(price__gte=2500, price__lte=5000)
            ayurvedic_qs = ayurvedic_qs.filter(price__gte=2500, price__lte=5000)
            pharmacy_qs  = pharmacy_qs.filter(price__gte=2500, price__lte=5000)
        elif price == '5000-':
            korean_qs    = korean_qs.filter(price__gte=5000)
            makeup_qs    = makeup_qs.filter(price__gte=5000)
            ayurvedic_qs = ayurvedic_qs.filter(price__gte=5000)
            pharmacy_qs  = pharmacy_qs.filter(price__gte=5000)

    # ── Apply sort ──
    if sort == 'price_asc':
        korean_qs    = korean_qs.order_by('price', 'name')
        makeup_qs    = makeup_qs.order_by('price', 'name')
        ayurvedic_qs = ayurvedic_qs.order_by('price', 'name')
        pharmacy_qs  = pharmacy_qs.order_by('price', 'name')
    elif sort == 'price_desc':
        korean_qs    = korean_qs.order_by('-price', 'name')
        makeup_qs    = makeup_qs.order_by('-price', 'name')
        ayurvedic_qs = ayurvedic_qs.order_by('-price', 'name')
        pharmacy_qs  = pharmacy_qs.order_by('-price', 'name')
    elif sort == 'name_asc':
        korean_qs    = korean_qs.order_by('name')
        makeup_qs    = makeup_qs.order_by('name')
        ayurvedic_qs = ayurvedic_qs.order_by('name')
        pharmacy_qs  = pharmacy_qs.order_by('name')
    elif sort == 'newest':
        korean_qs    = korean_qs.order_by('-created_at')
        makeup_qs    = makeup_qs.order_by('-created_at')
        ayurvedic_qs = ayurvedic_qs.order_by('-created_at')
        pharmacy_qs  = pharmacy_qs.order_by('-created_at')
    else:
        korean_qs    = korean_qs.order_by('brand', 'name')
        makeup_qs    = makeup_qs.order_by('brand', 'name')
        ayurvedic_qs = ayurvedic_qs.order_by('brand', 'name')
        pharmacy_qs  = pharmacy_qs.order_by('brand', 'name')

    # ── Group Korean products by range (brand field holds range name) ──
    korean_ranges = OrderedDict()
    for product in korean_qs:
        range_name = product.brand or 'Other'
        if range_name not in korean_ranges:
            korean_ranges[range_name] = []
        korean_ranges[range_name].append(product)

    # ── Group makeup products by brand ──
    makeup_brands = OrderedDict()
    for product in makeup_qs:
        brand_name = product.brand or 'Other'
        if brand_name not in makeup_brands:
            makeup_brands[brand_name] = []
        makeup_brands[brand_name].append(product)

    # ── Group ayurvedic products by brand ──
    ayurvedic_brands = OrderedDict()
    for product in ayurvedic_qs:
        brand_name = product.brand or 'Other'
        if brand_name not in ayurvedic_brands:
            ayurvedic_brands[brand_name] = []
        ayurvedic_brands[brand_name].append(product)

    # ── Group pharmacy products by brand ──
    pharmacy_brands = OrderedDict()
    for product in pharmacy_qs:
        brand_name = product.brand or 'Other'
        if brand_name not in pharmacy_brands:
            pharmacy_brands[brand_name] = []
        pharmacy_brands[brand_name].append(product)

    total_korean    = korean_qs.count()
    total_makeup    = makeup_qs.count()
    total_ayurvedic = ayurvedic_qs.count()
    total_pharmacy  = pharmacy_qs.count()

    # ── Sidebar filter data (all-products scope for counts) ──
    all_makeup_brands = (
        Product.objects.filter(product_range='makeup')
        .values_list('brand', flat=True)
        .distinct()
        .order_by('brand')
    )
    all_korean_ranges = (
        Product.objects.filter(product_range='korean')
        .values_list('brand', flat=True)
        .distinct()
        .order_by('brand')
    )
    # Category counts for sidebar
    makeup_categories = (
        Product.objects.filter(product_range='makeup')
        .values_list('category', flat=True)
        .distinct()
        .order_by('category')
    )
    korean_categories = (
        Product.objects.filter(product_range='korean')
        .values_list('category', flat=True)
        .distinct()
        .order_by('category')
    )

    # Count active filters for badge
    active_filter_count = sum([
        bool(q), bool(category), bool(price),
        bool(product_range), bool(brand), bool(skin_type), bool(featured),
    ])

    skin_type_options = [
        ('oily', 'Oily'),
        ('dry', 'Dry'),
        ('combination', 'Combination'),
        ('normal', 'Normal'),
        ('all', 'All Skin Types'),
    ]

    context = {
        'korean_ranges':      korean_ranges,
        'korean_range_meta':  KOREAN_RANGE_META,
        'makeup_brands':      makeup_brands,
        'ayurvedic_brands':   ayurvedic_brands,
        'pharmacy_brands':    pharmacy_brands,
        'total_korean':       total_korean,
        'total_makeup':       total_makeup,
        'total_ayurvedic':    total_ayurvedic,
        'total_pharmacy':     total_pharmacy,
        'total_results':      total_korean + total_makeup + total_ayurvedic + total_pharmacy,
        # sidebar data
        'all_makeup_brands':  list(all_makeup_brands),
        'all_korean_ranges':  list(all_korean_ranges),
        'makeup_categories':  list(makeup_categories),
        'korean_categories':  list(korean_categories),
        'active_filter_count': active_filter_count,
        'skin_type_options':  skin_type_options,
        # current filter values echoed back
        'cur_q':              q,
        'cur_category':       category,
        'cur_price':          price,
        'cur_product_range':  product_range,
        'cur_brand':          brand,
        'cur_skin_type':      skin_type,
        'cur_sort':           sort,
        'cur_featured':       featured,
    }

    return render(request, 'products/list.html', context)


def product_detail(request, pk):
    """
    Flipkart-style product detail page — images, shades, COD, shop policy, related products.
    """
    product = get_object_or_404(Product, pk=pk)

    # Related products — same category & range, excluding self
    related = Product.objects.filter(
        product_range=product.product_range,
        category=product.category,
    ).exclude(pk=pk)[:6]

    # Same brand products
    same_brand = Product.objects.filter(
        brand=product.brand,
    ).exclude(pk=pk)[:4]

    # Build ingredients list
    ingredients_list = product.get_key_ingredients_list()

    # Range meta for K-Beauty
    range_meta = KOREAN_RANGE_META.get(product.brand, {})

    context = {
        'product':          product,
        'related':          related,
        'same_brand':       same_brand,
        'ingredients_list': ingredients_list,
        'range_meta':       range_meta,
    }
    return render(request, 'products/detail.html', context)
