from django.contrib import admin
from .models import DailyRoutineLog, WeeklyCheckin, ScanMilestone


@admin.register(DailyRoutineLog)
class DailyRoutineLogAdmin(admin.ModelAdmin):
    list_display  = ('user', 'log_date', 'am_done', 'pm_done', 'skin_rating', 'water_glasses')
    list_filter   = ('am_done', 'pm_done', 'log_date')
    search_fields = ('user__username',)
    date_hierarchy = 'log_date'


@admin.register(WeeklyCheckin)
class WeeklyCheckinAdmin(admin.ModelAdmin):
    list_display  = ('user', 'week_number', 'week_start', 'overall_rating', 'completed_at')
    list_filter   = ('overall_rating',)
    search_fields = ('user__username',)


@admin.register(ScanMilestone)
class ScanMilestoneAdmin(admin.ModelAdmin):
    list_display  = ('user', 'started_at', 'score_day0', 'score_day14', 'score_day30', 'score_day90')
    search_fields = ('user__username',)
    readonly_fields = ('started_at', 'updated_at')
