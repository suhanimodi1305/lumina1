from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('',                        views.product_list,   name='list'),
    path('brand/<str:brand_slug>/', views.brand_page,     name='brand'),
    path('<int:pk>/',               views.product_detail, name='detail'),
]