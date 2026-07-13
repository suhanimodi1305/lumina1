from django.urls import path
from . import views

app_name = 'results'

urlpatterns = [
    path('<int:scan_id>/', views.skin_results, name='detail'),
    path('<int:scan_id>/face-shape-api/', views.face_shape_api, name='face_shape_api'),
    path('progress/', views.progress_overview, name='progress'),
    path('progress/<int:baseline_id>/<int:latest_id>/', views.compare_scans, name='compare'),
]