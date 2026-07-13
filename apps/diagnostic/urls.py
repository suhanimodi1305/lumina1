from django.urls import path
from . import views

app_name = 'diagnostic'

urlpatterns = [
    path('',                        views.wizard,            name='wizard'),
    path('quiz/',                   views.quiz,              name='quiz'),
    path('result/<uuid:session_id>/',views.result,           name='result'),
    path('step/',                   views.wizard_step,       name='step'),
    path('marketing/',              views.marketing_portal,  name='marketing'),
    path('admin-panel/',            views.admin_panel,       name='admin_panel'),
    path('log-earn/',               views.log_earn,          name='log_earn'),
    path('log-habit/',              views.log_habit_ajax,    name='log_habit'),
    path('admin-panel/logs-fragment/', views.logs_fragment,  name='logs_fragment'),

    # ── Smart Diagnostic Quiz ────────────────────────────────────────────────
    path('smart/',                           views.smart_start,    name='smart_start'),
    path('smart/q/<int:step>/',              views.smart_question, name='smart_question'),
    path('smart/q/<int:step>/save/',         views.smart_save,     name='smart_save'),
    path('smart/finish/<uuid:session_id>/',  views.smart_finish,   name='smart_finish'),
    path('smart/result/<uuid:session_id>/',  views.smart_result,   name='smart_result'),
]
