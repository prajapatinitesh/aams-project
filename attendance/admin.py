from django.contrib import admin
from .models import AttendanceRecord, WebGLFingerprint, ProxyLog

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ("session", "student", "status", "marked_by", "marked_at")
    list_filter = ("status", "marked_by")
    search_fields = ("student__user__full_name", "student__roll_number")

@admin.register(WebGLFingerprint)
class WebGLFingerprintAdmin(admin.ModelAdmin):
    list_display = ("session", "student", "webgl_hash", "submitted_at")
    search_fields = ("student__user__full_name", "webgl_hash")

@admin.register(ProxyLog)
class ProxyLogAdmin(admin.ModelAdmin):
    list_display = ("session", "attempted_by_student", "reason", "attempted_at")
    list_filter = ("reason",)
    search_fields = ("attempted_by_student__user__full_name", "reason")
