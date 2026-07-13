"""
Reviews views — list, create, helpful vote, admin moderation.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from apps.products.models import Product
from .models import ProductReview, ReviewHelpful


@login_required
def submit_review(request, product_pk):
    """GET shows review form, POST submits review."""
    product = get_object_or_404(Product, pk=product_pk)

    # Check if user already reviewed
    existing = ProductReview.objects.filter(product=product, user=request.user).first()
    if existing:
        messages.info(request, 'You have already reviewed this product.')
        return redirect('products:detail', pk=product_pk)

    if request.method == 'POST':
        rating = max(1, min(5, int(request.POST.get('rating', 5) or 5)))
        title  = request.POST.get('title', '').strip()[:200]
        body   = request.POST.get('body', '').strip()[:2000]

        if not title or not body:
            messages.error(request, 'Please fill in a title and review body.')
            return redirect('reviews:submit', product_pk=product_pk)

        # Check scan verification
        scan_verified = False
        try:
            from apps.scanner.models import ScanResult
            scan_verified = ScanResult.objects.filter(
                user=request.user, is_demo=False
            ).exists()
        except Exception:
            pass

        # Check purchase verification
        purchase_verified = False
        try:
            from apps.orders.models import Order
            purchase_verified = Order.objects.filter(
                user=request.user,
                items__name__icontains=product.name[:20],
                status='delivered',
            ).exists()
        except Exception:
            pass

        review = ProductReview.objects.create(
            product=product,
            user=request.user,
            rating=rating,
            title=title,
            body=body,
            skin_type=request.POST.get('skin_type', ''),
            concern=request.POST.get('concern', ''),
            used_for_weeks=max(0, min(52, int(request.POST.get('used_for_weeks', 0) or 0))),
            would_recommend=request.POST.get('would_recommend') == 'yes',
            scan_verified=scan_verified,
            purchase_verified=purchase_verified,
            status='approved',  # auto-approve; can add moderation later
        )

        messages.success(request, 'Review submitted! Thank you.')
        return redirect('products:detail', pk=product_pk)

    return render(request, 'reviews/submit.html', {
        'product':      product,
        'skin_choices': ProductReview.SKIN_TYPE_CHOICES,
        'concern_choices': ProductReview.CONCERN_CHOICES,
    })


@login_required
@require_POST
def helpful_vote(request, review_pk):
    """AJAX POST — mark a review as helpful."""
    review = get_object_or_404(ProductReview, pk=review_pk, status='approved')
    _, created = ReviewHelpful.objects.get_or_create(review=review, user=request.user)
    if created:
        review.helpful_count += 1
        review.save(update_fields=['helpful_count'])
    return JsonResponse({'ok': True, 'count': review.helpful_count})


@login_required
@require_POST
def delete_review(request, review_pk):
    """DELETE own review."""
    review = get_object_or_404(ProductReview, pk=review_pk, user=request.user)
    product_pk = review.product_id
    review.delete()
    messages.success(request, 'Review deleted.')
    return redirect('products:detail', pk=product_pk)
