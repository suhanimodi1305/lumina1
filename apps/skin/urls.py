from django.urls import path
from . import views

app_name = 'skin'

urlpatterns = [
    path('',                             views.start,     name='start'),
    path('begin/',                       views.begin,     name='begin'),
    path('q/<int:step>/',                views.question,  name='question'),
    path('q/<int:step>/save/',           views.save_step, name='save_step'),
    path('result/<uuid:session_id>/',    views.result,    name='result'),
    path('restart/',                     views.restart,   name='restart'),
]
