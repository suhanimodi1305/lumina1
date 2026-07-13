from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views
from apps.accounts.views import user_home
from apps.accounts import views as account_views
from apps.accounts.forms import LuminaLoginForm

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('me/', user_home, name='user_home'),
    path('scan/', include('apps.scanner.urls')),
    path('results/', include('apps.results.urls')),
    path('products/', include('apps.products.urls')),
    path('treatments/', include('apps.treatments.urls')),
    path('chat/', include('apps.chat.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
    path('employee/', include('apps.employee.urls')),
    path('orders/',     include('apps.orders.urls')),
    path('membership/', include('apps.memberships.urls', namespace='memberships')),
    path('diagnostic/', include('apps.diagnostic.urls', namespace='diagnostic')),
    path('skin/', include('apps.skin.urls', namespace='skin')),
    path('hair/', include('apps.hair.urls', namespace='hair')),
    path('progress/', include('apps.progress.urls', namespace='progress')),
    path('notifications/', include('apps.notifications.urls', namespace='notifications')),
    path('reviews/', include('apps.reviews.urls', namespace='reviews')),
    path('coupons/', include('apps.coupons.urls', namespace='coupons')),
    path('blog/', include('apps.blog.urls', namespace='blog')),

    # ── Navigation convenience shortcuts ─────────────────────────────────────
    # These short URLs match the flow diagram so every page can use clean links.
    path('login/',    auth_views.LoginView.as_view(
        template_name='accounts/login.html',
        authentication_form=LuminaLoginForm,
        redirect_authenticated_user=True,
    ), name='login'),
    path('logout/',   auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('register/', account_views.signup, name='register'),
    path('verify/',   account_views.signup, name='verify'),          # placeholder — signup handles OTP if added later
    path('profile/create/', account_views.profile_create, name='profile_create'),

    # Routine / check-in shorthand (redirect to progress app views)
    path('routine/', RedirectView.as_view(pattern_name='progress:daily_log',  permanent=False), name='routine'),
    path('checkin/', RedirectView.as_view(pattern_name='progress:weekly_checkin', permanent=False), name='checkin'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
