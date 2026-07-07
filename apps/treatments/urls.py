from django.urls import path
from . import views

app_name = 'treatments'

urlpatterns = [
    path('<int:scan_id>/', views.plan, name='plan'),
]