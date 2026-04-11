from django.db import models
from att_sessions.models import AttendanceSession
from departments.models import StudentProfile

class AttendanceRecord(models.Model):
    MARKED_BY_CHOICES = [("default", "Default"), ("qr", "QR Scan"), ("manual", "Manual")]

    session    = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name="records")
    student    = models.ForeignKey(StudentProfile, on_delete=models.PROTECT, related_name="attendance_records")
    status     = models.CharField(max_length=20, default="absent")  # "present" or "absent"
    marked_by  = models.CharField(max_length=20, choices=MARKED_BY_CHOICES, default="default")
    marked_at  = models.DateTimeField(null=True, blank=True)
    
    # Location data
    lat        = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lng        = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    distance   = models.FloatField(null=True, blank=True, help_text="Distance from teacher in meters")

    class Meta:
        unique_together = [("session", "student")]

    def __str__(self): return f"{self.student.user.full_name} - {self.status}"

class WebGLFingerprint(models.Model):
    session      = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name="fingerprints")
    student      = models.ForeignKey(StudentProfile, on_delete=models.PROTECT, related_name="fingerprints")
    webgl_hash   = models.CharField(max_length=64, db_index=True)  # SHA-256 hex, 64 chars
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("session", "student")]  # one fingerprint per student per session

    def __str__(self): return f"Fingerprint: {self.hash[:8]}..."

class ProxyLog(models.Model):
    REASON_CHOICES = [
        ("already_marked",    "Already Marked"),
        ("device_conflict",   "Device Conflict"),
        ("location_mismatch", "Location Mismatch"),
        ("location_denied",   "Location Denied"),
    ]

    session               = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name="proxy_logs")
    attempted_by_student  = models.ForeignKey(StudentProfile, on_delete=models.PROTECT, related_name="proxy_attempts")
    conflicting_student   = models.ForeignKey(StudentProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="proxy_conflicts")
    webgl_hash            = models.CharField(max_length=64)
    reason                = models.CharField(max_length=30, choices=REASON_CHOICES)
    attempted_at          = models.DateTimeField(auto_now_add=True)

    # Attempted location
    attempted_lat         = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    attempted_lng         = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    def __str__(self): return f"Proxy Alert: {self.reason}"
