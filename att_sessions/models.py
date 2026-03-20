from django.db import models
from departments.models import Subject, TeacherProfile

class AttendanceSession(models.Model):
    STATUS_CHOICES = [("active", "Active"), ("ended", "Ended")]
    MODE_CHOICES   = [("none", "None"), ("qr", "QR"), ("manual", "Manual")]

    subject          = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name="sessions")
    teacher          = models.ForeignKey(TeacherProfile, on_delete=models.PROTECT, related_name="sessions")
    date             = models.DateField()
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    mode             = models.CharField(max_length=20, choices=MODE_CHOICES, default="none")
    current_qr_token = models.TextField(null=True, blank=True)
    qr_generated_at  = models.DateTimeField(null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    ended_at         = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self): return f"{self.subject.name} - {self.date}"

    @property
    def total_count(self):
        return self.records.count()

    @property
    def present_count(self):
        return self.records.filter(status='present').count()
