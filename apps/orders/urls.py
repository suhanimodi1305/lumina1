from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Cart actions
    path('cart/add/<int:pk>/',    views.cart_add,    name='cart_add'),
    path('cart/remove/<int:pk>/', views.cart_remove, name='cart_remove'),
    path('cart/update/<int:pk>/', views.cart_update, name='cart_update'),

    # Order flow
    path('checkout/',                       views.checkout,       name='checkout'),
    path('payment/',                        views.payment,        name='payment'),
    path('success/<str:order_id>/',         views.order_success,  name='success'),
    path('tracking/<str:order_id>/',        views.order_tracking, name='tracking'),

    # My orders + public tracker
    path('my-orders/',                      views.my_orders,      name='my_orders'),
    path('track/',                          views.track_order,    name='track'),

    # User requirements
    path('requirements/',                           views.my_requirements,    name='my_requirements'),
    path('requirements/new/',                       views.requirement_create, name='requirement_create'),
    path('requirements/<str:req_id>/',              views.requirement_detail, name='requirement_detail'),
    path('requirements/<str:req_id>/cancel/',       views.requirement_cancel, name='requirement_cancel'),
]
