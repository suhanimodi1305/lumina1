from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    path('product/<int:product_pk>/submit/', views.submit_review,  name='submit'),
    path('<int:review_pk>/helpful/',          views.helpful_vote,   name='helpful'),
    path('<int:review_pk>/delete/',           views.delete_review,  name='delete'),
]
