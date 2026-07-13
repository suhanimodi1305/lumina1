from django.urls import path
from . import views

app_name = 'coupons'

urlpatterns = [
    path('',            views.coupon_list,      name='list'),
    path('validate/',   views.validate_coupon,  name='validate'),
    path('my/',         views.my_coupons,        name='my_coupons'),
]
