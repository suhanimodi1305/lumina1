from django.contrib import admin
from .models import SkinSession


@admin.register(SkinSession)
class SkinSessionAdmin(admin.ModelAdmin):
    list_display  = ('id', 'user', 'skin_type_result', 'acne_severity', 'completed', 'created_at')
    list_filter   = ('completed', 'skin_type_result', 'acne_severity')
    search_fields = ('user__username', 'country')
    readonly_fields = ('id', 'created_at', 'updated_at')
