"""
Blog views — public listing, detail, category filter, search.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.db.models import Q

from .models import BlogPost, BlogCategory


def blog_list(request):
    """Public blog listing — published posts, filterable by category."""
    category_slug = request.GET.get('category', '').strip()
    q             = request.GET.get('q', '').strip()
    tag           = request.GET.get('tag', '').strip()

    posts = BlogPost.objects.filter(
        status='published',
        published_at__lte=timezone.now(),
    ).select_related('category', 'author')

    if category_slug:
        posts = posts.filter(category__slug=category_slug)
    if q:
        posts = posts.filter(
            Q(title__icontains=q) |
            Q(excerpt__icontains=q) |
            Q(tags__icontains=q)
        )
    if tag:
        posts = posts.filter(tags__icontains=tag)

    featured    = posts.filter(is_featured=True)[:3]
    recent      = posts[:12]
    categories  = BlogCategory.objects.all()
    all_tags    = _popular_tags()

    return render(request, 'blog/list.html', {
        'posts':         recent,
        'featured':      featured,
        'categories':    categories,
        'all_tags':      all_tags,
        'cur_category':  category_slug,
        'cur_q':         q,
        'cur_tag':       tag,
        'total':         posts.count(),
    })


def blog_detail(request, slug):
    """Public blog post detail — auto-increment view count."""
    post = get_object_or_404(
        BlogPost, slug=slug, status='published', published_at__lte=timezone.now()
    )
    # Increment view count (simple, non-atomic — acceptable for blog)
    BlogPost.objects.filter(pk=post.pk).update(view_count=post.view_count + 1)

    # Related posts — same category, excluding self
    related = BlogPost.objects.filter(
        status='published',
        published_at__lte=timezone.now(),
        category=post.category,
    ).exclude(pk=post.pk)[:3]

    return render(request, 'blog/detail.html', {
        'post':    post,
        'related': related,
    })


def blog_category(request, slug):
    """Posts filtered by category — redirects to list with category param."""
    return redirect(f'/blog/?category={slug}')


# ── Helpers ───────────────────────────────────────────────────────────────────

def _popular_tags(limit=20):
    """Return a list of the most common tags across published posts."""
    from collections import Counter
    all_tags = []
    for post in BlogPost.objects.filter(status='published').values_list('tags', flat=True):
        if post:
            all_tags.extend([t.strip() for t in post.split(',') if t.strip()])
    counter = Counter(all_tags)
    return [tag for tag, _ in counter.most_common(limit)]
