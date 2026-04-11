from django.contrib import admin
from .models import AttendanceSession

@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ("subject", "teacher", "date", "status", "mode")
    list_filter = ("status", "mode", "date")
    search_fields = ("subject__name", "teacher__user__full_name")
