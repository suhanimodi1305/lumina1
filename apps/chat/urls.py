from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('',                            views.index,               name='index'),
    path('create/',                     views.create_conversation, name='create'),
    path('new/',                        views.create_conversation, name='new_room'),
    path('<uuid:pk>/',                  views.room,                name='room'),
    path('<uuid:pk>/send/',             views.send_message,        name='send_message'),
    path('<uuid:pk>/photo/',            views.send_photo,          name='send_photo'),
    path('<uuid:pk>/switch-mode/',      views.switch_mode,         name='switch_mode'),
    path('<uuid:pk>/delete/',           views.delete_conversation, name='delete'),
]
