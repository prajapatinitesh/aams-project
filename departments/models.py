from django.db import models
from accounts.models import User

class Department(models.Model):
    name       = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): return self.name

class Subject(models.Model):
    name          = models.CharField(max_length=150)
    department    = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="subjects")
    semester      = models.PositiveSmallIntegerField()  # 1–8
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("name", "department", "semester")]

    def __str__(self): return f"{self.name} (Sem {self.semester})"

class TeacherProfile(models.Model):
    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name="teacher_profile")
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    subjects   = models.ManyToManyField(Subject, blank=True, related_name="teachers")

    def __str__(self): return f"Teacher: {self.user.full_name}"

class StudentProfile(models.Model):
    user        = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")
    department  = models.ForeignKey(Department, on_delete=models.PROTECT)
    semester    = models.PositiveSmallIntegerField()
    roll_number = models.CharField(max_length=30)

    class Meta:
        unique_together = [("department", "semester", "roll_number")]

    def __str__(self): return f"Student: {self.user.full_name} ({self.roll_number})"
