"""
Core views - updated with context for home page
"""
from django.shortcuts import render
from apps.products.models import Product


def home(request):
    """Homepage view with feature showcase"""
    
    # Product counts
    korean_count = Product.objects.filter(product_range='korean').count()
    makeup_count = Product.objects.filter(product_range='makeup').count()
    
    # Features list
    features = [
        {
            'icon': 'bi-camera-fill',
            'title': 'AI Face Scanner',
            'description': 'Upload your photo and get instant skin analysis powered by 3 HuggingFace AI models'
        },
        {
            'icon': 'bi-stars',
            'title': 'K-Beauty Matching',
            'description': 'Get personalized Korean skincare products from SAS Global matched to your exact skin concerns'
        },
        {
            'icon': 'bi-palette',
            'title': 'Makeup Shade Finder',
            'description': 'Find your perfect foundation, concealer, blush and lipstick shades based on AI undertone analysis'
        },
        {
            'icon': 'bi-heart-pulse',
            'title': 'AI Dermatologist',
            'description': 'Chat 24/7 with Dr. Lumina for expert skincare advice and product recommendations'
        },
        {
            'icon': 'bi-capsule',
            'title': 'Treatment Planner',
            'description': 'Get personalized clinical treatment recommendations based on your skin severity'
        },
        {
            'icon': 'bi-graph-up',
            'title': 'Progress Tracking',
            'description': 'Track your skin health journey with detailed analytics and 4-week progress charts'
        }
    ]
    
    context = {
        'korean_count': korean_count,
        'makeup_count': makeup_count,
        'features': features,
        'active_tab': 'analysis'
    }
    
    return render(request, 'core/home.html', context)


def kbeauty(request):
    """K-Beauty Innovation Hub"""
    k_beauty_steps = [
        {'step_number': 1, 'icon': 'bi-droplet', 'name': 'Oil Cleanser'},
        {'step_number': 2, 'icon': 'bi-water', 'name': 'Water Cleanser'},
        {'step_number': 3, 'icon': 'bi-moisture', 'name': 'Exfoliator'},
        {'step_number': 4, 'icon': 'bi-wind', 'name': 'Toner'},
        {'step_number': 5, 'icon': 'bi-stars', 'name': 'Essence'},
        {'step_number': 6, 'icon': 'bi-eyedropper', 'name': 'Serum'},
        {'step_number': 7, 'icon': 'bi-layers', 'name': 'Sheet Mask'},
        {'step_number': 8, 'icon': 'bi-eye', 'name': 'Eye Cream'},
        {'step_number': 9, 'icon': 'bi-layers-fill', 'name': 'Moisturizer'},
        {'step_number': 10, 'icon': 'bi-sun', 'name': 'Sunscreen'},
    ]
    featured_products = Product.objects.filter(product_range='korean', is_featured=True)[:6]
    if not featured_products:
        featured_products = Product.objects.filter(product_range='korean')[:6]

    return render(request, 'core/kbeauty.html', {
        'k_beauty_steps': k_beauty_steps,
        'featured_products': featured_products,
    })


def dermatology(request):
    """Dermatology hub"""
    doctors = [
        {
            'name': 'Dr. Priya Sharma',
            'credentials': 'MD, DNB Dermatology',
            'specialty': 'Acne & Pigmentation',
            'verified': True,
        },
        {
            'name': 'Dr. Ananya Reddy',
            'credentials': 'MD Dermatology, Fellowship in Cosmetic Dermatology',
            'specialty': 'Anti-Aging & Laser Treatments',
            'verified': True,
        },
        {
            'name': 'Dr. Meera Iyer',
            'credentials': 'MD, DVL',
            'specialty': 'Sensitive Skin & Rosacea',
            'verified': True,
        },
    ]

    return render(request, 'core/dermatology.html', {'doctors': doctors})


def makeup(request):
    """Makeup shop page"""
    featured_products = Product.objects.filter(product_range='makeup', is_featured=True)[:6]
    if not featured_products:
        featured_products = Product.objects.filter(product_range='makeup')[:6]

    return render(request, 'core/shop.html', {'featured_products': featured_products})