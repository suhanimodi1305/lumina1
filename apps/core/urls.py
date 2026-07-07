from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('kbeauty/', views.kbeauty, name='kbeauty'),
    path('dermatology/', views.dermatology, name='dermatology'),
    path('shop/', views.makeup, name='shop'),
]