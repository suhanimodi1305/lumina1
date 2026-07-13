from django.urls import path
from . import views

app_name = 'progress'

urlpatterns = [
    path('',                     views.progress_home,         name='progress_home'),
    path('daily/',               views.daily_log,              name='daily_log'),
    path('daily/save/',          views.save_daily_log,         name='save_daily_log'),
    path('weekly/',              views.weekly_checkin,         name='weekly_checkin'),
    path('milestones/',          views.milestone_tracker,      name='milestone_tracker'),
    path('milestones/link/',     views.link_scan_to_milestone, name='link_scan'),
    path('analytics/',           views.analytics,              name='analytics'),
]
