from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.accounts.views import user_home
from apps.memberships import views as memberships_views

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
    path('doctor/',     memberships_views.doctor_consultation, name='doctor'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
