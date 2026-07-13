from django.urls import path
from . import views

app_name = 'scanner'

urlpatterns = [
    path('', views.upload, name='upload'),
    path('<int:scan_id>/questions/', views.questionnaire, name='questionnaire'),
]