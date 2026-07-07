from django.urls import path
from . import views

app_name = 'memberships'

urlpatterns = [
    path('upgrade/',         views.upgrade_page,    name='upgrade'),
    path('upgrade/confirm/', views.upgrade_confirm, name='upgrade_confirm'),
    path('redeem/',          views.redeem_points,   name='redeem'),
]
