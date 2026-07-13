"""
Blog app — articles, categories, tags for SEO and content marketing.
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class BlogCategory(models.Model):
    name        = models.CharField(max_length=100)
    slug        = models.SlugField(max_length=100, unique=True)
    description = models.CharField(max_length=300, blank=True)
    icon        = models.CharField(max_length=10, blank=True)  # emoji
    order       = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Blog Category'
        verbose_name_plural = 'Blog Categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class BlogPost(models.Model):
    """A published blog article."""

    STATUS_CHOICES = [
        ('draft',     'Draft'),
        ('published', 'Published'),
        ('archived',  'Archived'),
    ]

    # Identity
    title       = models.CharField(max_length=300)
    slug        = models.SlugField(max_length=300, unique=True)
    category    = models.ForeignKey(BlogCategory, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='posts')
    tags        = models.CharField(max_length=300, blank=True,
                                   help_text='Comma-separated tags')

    # Content
    excerpt     = models.TextField(max_length=500, blank=True,
                                   help_text='Short preview shown on listing page')
    content     = models.TextField(help_text='Full article body (HTML allowed)')
    cover_image = models.ImageField(upload_to='blog/%Y/%m/', null=True, blank=True)
    cover_image_alt = models.CharField(max_length=200, blank=True)

    # Authorship
    author      = models.ForeignKey(User, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='blog_posts')
    author_name = models.CharField(max_length=100, default='Lumina Team',
                                   help_text='Display name (overrides User.get_full_name)')

    # Status & dates
    status      = models.CharField(max_length=12, choices=STATUS_CHOICES, default='draft')
    published_at = models.DateTimeField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    # SEO
    meta_title       = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=400, blank=True)

    # Engagement
    view_count    = models.PositiveIntegerField(default=0)
    reading_time  = models.PositiveSmallIntegerField(
        default=5, help_text='Estimated reading time in minutes'
    )
    is_featured   = models.BooleanField(default=False)

    class Meta:
        ordering = ['-published_at', '-created_at']
        verbose_name = 'Blog Post'

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:300]
        if not self.reading_time and self.content:
            # ~200 words per minute
            word_count = len(self.content.split())
            self.reading_time = max(1, word_count // 200)
        super().save(*args, **kwargs)

    @property
    def tag_list(self):
        return [t.strip() for t in self.tags.split(',') if t.strip()]

    @property
    def display_author(self):
        if self.author and self.author.get_full_name():
            return self.author.get_full_name()
        return self.author_name
