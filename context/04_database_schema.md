# Database Schema
## AAMS — Advanced Attendance Management System

---

## Purpose of This Document

Exact Django model definitions and schema constraints for AAMS. Implement these models as written. Field names, types, constraints, and relationships are all specified.

---

## App: `accounts`

### Model: `User` (custom, replaces Django's default)

```python
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UserManager(BaseUserManager):
    def create_user(self, email, password, role, full_name, **kwargs):
        email = self.normalize_email(email)
        user = self.model(email=email, role=role, full_name=full_name, **kwargs)
        user.set_password(password)
        user.save()
        return user

class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [("admin", "Admin"), ("teacher", "Teacher"), ("student", "Student")]

    email      = models.EmailField(unique=True)
    full_name  = models.CharField(max_length=255)
    role       = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=False)   # required for Django admin shell access
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = ["full_name", "role"]
    objects = UserManager()
```

---

## App: `departments`

### Model: `Department`

```python
class Department(models.Model):
    name       = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): return self.name
```

### Model: `Subject`

```python
class Subject(models.Model):
    name          = models.CharField(max_length=150)
    department    = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="subjects")
    semester      = models.PositiveSmallIntegerField()  # 1–8
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("name", "department", "semester")]

    def __str__(self): return f"{self.name} (Sem {self.semester})"
```

### Model: `TeacherProfile`

```python
class TeacherProfile(models.Model):
    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name="teacher_profile")
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    subjects   = models.ManyToManyField(Subject, blank=True, related_name="teachers")
```

### Model: `StudentProfile`

```python
class StudentProfile(models.Model):
    user        = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")
    department  = models.ForeignKey(Department, on_delete=models.PROTECT)
    semester    = models.PositiveSmallIntegerField()
    roll_number = models.CharField(max_length=30)

    class Meta:
        unique_together = [("department", "semester", "roll_number")]
```

> **Enrollment logic:** There is no explicit enrollment table. A student is considered enrolled in a subject if `student.department == subject.department AND student.semester == subject.semester`. This is resolved at session creation time by querying `StudentProfile` with those filters.

---

## App: `att_sessions`

### Model: `AttendanceSession`

```python
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
        # Prevent duplicate active sessions for same teacher+subject+date
        unique_together = [("teacher", "subject", "date")]
```

---

## App: `attendance`

### Model: `AttendanceRecord`

Pre-populated at session creation. One row per enrolled student per session, default absent.

```python
class AttendanceRecord(models.Model):
    MARKED_BY_CHOICES = [("default", "Default"), ("qr", "QR Scan"), ("manual", "Manual")]

    session    = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name="records")
    student    = models.ForeignKey(StudentProfile, on_delete=models.PROTECT, related_name="attendance_records")
    status     = models.CharField(max_length=20, default="absent")  # "present" or "absent"
    marked_by  = models.CharField(max_length=20, choices=MARKED_BY_CHOICES, default="default")
    marked_at  = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("session", "student")]
```

### Model: `WebGLFingerprint`

```python
class WebGLFingerprint(models.Model):
    session      = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name="fingerprints")
    student      = models.ForeignKey(StudentProfile, on_delete=models.PROTECT, related_name="fingerprints")
    hash         = models.CharField(max_length=64, db_index=True)  # SHA-256 hex, 64 chars
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("session", "student")]  # one fingerprint per student per session
```

> **Index note:** `db_index=True` on `hash` is required — on every QR submission, the server queries `WebGLFingerprint.objects.filter(session=session, hash=submitted_hash).exclude(student=current_student)`. Without the index this is a full table scan.

### Model: `ProxyLog`

```python
class ProxyLog(models.Model):
    REASON_CHOICES = [
        ("already_marked",  "Already Marked"),
        ("device_conflict", "Device Conflict"),
    ]

    session               = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name="proxy_logs")
    attempted_by_student  = models.ForeignKey(StudentProfile, on_delete=models.PROTECT, related_name="proxy_attempts")
    conflicting_student   = models.ForeignKey(StudentProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="proxy_conflicts")
    webgl_hash            = models.CharField(max_length=64)
    reason                = models.CharField(max_length=30, choices=REASON_CHOICES)
    attempted_at          = models.DateTimeField(auto_now_add=True)
```

---

## App: `reports`

No custom models. All report views query `AttendanceRecord`, `WebGLFingerprint`, and `ProxyLog` using ORM.

---

## App: `accounts` — System Config

### Model: `SystemConfig`

```python
class SystemConfig(models.Model):
    key   = models.CharField(max_length=100, unique=True)
    value = models.CharField(max_length=255)

    @classmethod
    def get(cls, key, default=None):
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return default
```

**Seed this on first run (via data migration or management command):**

```python
SystemConfig.objects.get_or_create(key="qr_rotation_interval", defaults={"value": "30"})
```

---

## Schema Relationships (Visual)

```
User ──(1:1)── TeacherProfile ──(M2M)── Subject ──(FK)── Department
User ──(1:1)── StudentProfile ──(FK)────────────────────── Department

AttendanceSession ──(FK)── Subject
AttendanceSession ──(FK)── TeacherProfile

AttendanceRecord ──(FK)── AttendanceSession
AttendanceRecord ──(FK)── StudentProfile

WebGLFingerprint ──(FK)── AttendanceSession
WebGLFingerprint ──(FK)── StudentProfile

ProxyLog ──(FK)── AttendanceSession
ProxyLog ──(FK)── StudentProfile (attempted_by)
ProxyLog ──(FK)── StudentProfile (conflicting, nullable)
```

---

## FK `on_delete` Policy Summary

| Relationship | Policy | Reason |
|-------------|--------|--------|
| TeacherProfile → User | CASCADE | Profile is meaningless without the user |
| StudentProfile → User | CASCADE | Profile is meaningless without the user |
| Subject → Department | PROTECT | Do not silently delete subjects when dept is deleted |
| TeacherProfile → Department | SET_NULL | Teacher can exist without a home dept |
| AttendanceSession → Subject | PROTECT | Sessions are historical records |
| AttendanceSession → TeacherProfile | PROTECT | Sessions are historical records |
| AttendanceRecord → Session | CASCADE | Records belong to session; delete together |
| AttendanceRecord → StudentProfile | PROTECT | Do not delete records when student is deactivated |
| WebGLFingerprint → Session | CASCADE | Fingerprints belong to session |
| WebGLFingerprint → StudentProfile | PROTECT | Preserve for audit |
| ProxyLog → Session | CASCADE | Logs belong to session |
| ProxyLog → StudentProfile | PROTECT | Preserve for audit |
