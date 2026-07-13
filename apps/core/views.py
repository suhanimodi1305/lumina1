"""
Core views - updated with context for home page
"""
from django.shortcuts import render, redirect
from apps.products.models import Product


def home(request):
    """
    Public landing page for unauthenticated visitors.
    Logged-in users are redirected to their personal home dashboard.
    """
    # Authenticated users go straight to their personal home
    if request.user.is_authenticated:
        return redirect('user_home')

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


def faq(request):
    """Frequently Asked Questions page — accessible to all users."""
    faqs = [
        {
            'category': 'Getting Started',
            'icon': '🚀',
            'items': [
                {
                    'q': 'How does the AI skin analysis work?',
                    'a': 'Lumina uses Groq Llama-4-Scout Vision and Grok-4 to analyse 468 facial landmarks from your selfie. It detects skin type, acne severity, undertone, face shape, and pigmentation in under 30 seconds.'
                },
                {
                    'q': 'Is the analysis free?',
                    'a': 'Yes — the core AI face scan, skin type detection, and basic product recommendations are completely free. Premium features like AI Makeup Chat, K-Beauty Chat, and the VIP Doctor require a Plus or VIP membership.'
                },
                {
                    'q': 'What photo should I use?',
                    'a': 'Use a clear, well-lit selfie with no makeup. Face the camera straight on in natural light. Avoid filters or heavy shadows for the most accurate analysis.'
                },
            ]
        },
        {
            'category': 'Privacy & Data',
            'icon': '🔒',
            'items': [
                {
                    'q': 'Is my photo stored?',
                    'a': 'Your scan images are stored securely and linked only to your account. We never share your photos or skin data with third parties. You can delete your account and all associated data at any time.'
                },
                {
                    'q': 'Who can see my scan results?',
                    'a': 'Only you. Your results are private to your account. Staff can see anonymised analytics but never your individual scans or personal details without your consent.'
                },
            ]
        },
        {
            'category': 'Results & Accuracy',
            'icon': '📊',
            'items': [
                {
                    'q': 'How accurate is the skin analysis?',
                    'a': 'Our AI models achieve 98% accuracy on skin type detection in controlled conditions. Results may vary with poor lighting or low-resolution images. The 15-step Smart Quiz further improves accuracy by adding lifestyle context.'
                },
                {
                    'q': 'What is the Harmony Score?',
                    'a': 'The Harmony Score (0–100%) is Lumina\'s composite measure of your overall skin health — combining acne severity, hydration, tone evenness, and texture. Re-scan every 14 days to track your improvement.'
                },
                {
                    'q': 'How often should I rescan?',
                    'a': 'We recommend rescanning every 14 days to track progress. Skin changes slowly, so weekly scans won\'t show meaningful differences. The 14-day cycle aligns with most skincare product cycles.'
                },
            ]
        },
        {
            'category': 'Membership & Billing',
            'icon': '⭐',
            'items': [
                {
                    'q': 'What is included in the Free plan?',
                    'a': 'Free members get unlimited AI Face Scans, basic skin analysis, AI Doctor chat, product browsing, daily routine logging, and progress tracking. No credit card required.'
                },
                {
                    'q': 'What does Plus membership add?',
                    'a': 'Plus members unlock AI Makeup Chat, AI K-Beauty Chat, priority AI Doctor responses, advanced analytics, and early access to new features.'
                },
                {
                    'q': 'How do I cancel my membership?',
                    'a': 'You can cancel anytime from your membership page. Your access continues until the end of the billing period. Contact support if you need immediate assistance.'
                },
            ]
        },
        {
            'category': 'Products & Recommendations',
            'icon': '🛍',
            'items': [
                {
                    'q': 'How are products recommended to me?',
                    'a': 'Products are matched to your scan profile — skin type, concerns, undertone, and goals. The AI cross-references your profile with our curated catalogue to surface the most compatible products.'
                },
                {
                    'q': 'Can I shop without completing a scan?',
                    'a': 'Yes — the full product catalogue is browsable without a scan. However, personalised recommendations only activate after your first analysis.'
                },
            ]
        },
    ]
    return render(request, 'core/faq.html', {'faqs': faqs})