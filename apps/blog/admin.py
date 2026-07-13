from django.contrib import admin
from django.utils import timezone
from .models import BlogCategory, BlogPost


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order',)


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display   = ('title', 'category', 'status', 'is_featured',
                      'view_count', 'published_at', 'reading_time')
    list_filter    = ('status', 'is_featured', 'category')
    search_fields  = ('title', 'content', 'tags')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('view_count', 'created_at', 'updated_at')
    ordering       = ('-created_at',)
    actions        = ['publish_posts', 'draft_posts']

    @admin.action(description='Publish selected posts')
    def publish_posts(self, request, queryset):
        count = queryset.update(status='published', published_at=timezone.now())
        self.message_user(request, f'{count} post(s) published.')

    @admin.action(description='Set selected posts to draft')
    def draft_posts(self, request, queryset):
        count = queryset.update(status='draft')
        self.message_user(request, f'{count} post(s) set to draft.')
