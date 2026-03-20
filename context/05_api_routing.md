# API Specification & URL Routing
## AAMS — Advanced Attendance Management System

---

## Purpose of This Document

Exact URL patterns, view responsibilities, HTTP methods, request inputs, and response contracts. All views are Django class-based or function-based views returning HTML, except endpoints marked `[JSON]` which return `application/json`.

---

## URL Configuration

### `aams/urls.py` (root)

```python
from django.urls import path, include

urlpatterns = [
    path("",          include("accounts.urls")),
    path("admin/",    include("departments.urls.admin")),   # department, subject, teacher, student management
    path("admin/",    include("reports.urls")),             # reports and proxy logs
    path("teacher/",  include("att_sessions.urls")),        # session management + QR endpoint
    path("student/",  include("attendance.urls")),          # student attendance views
    path("attend/",   include("attendance.urls_submit")),   # QR submission (no role prefix)
]
```

---

## 1. Authentication — `accounts/urls.py`

```python
urlpatterns = [
    path("login/",     LoginView.as_view(),          name="login"),
    path("logout/",    LogoutView.as_view(),          name="logout"),
    path("dashboard/", DashboardRedirectView.as_view(), name="dashboard"),
]
```

### `GET /login/`
- Renders login form (email + password).

### `POST /login/`
- Authenticates user.
- On success: redirect based on `user.role`:
  - `admin` → `/admin/dashboard/`
  - `teacher` → `/teacher/dashboard/`
  - `student` → `/student/dashboard/`
- On failure: re-render form with error message.

### `POST /logout/`
- Calls `auth.logout(request)`. Redirects to `/login/`.

### `GET /dashboard/`
- Requires login. Redirects to the role-specific dashboard. Shortcut for use in templates.

---

## 2. Admin URLs — `departments/urls/admin.py`

All views decorated with `@admin_required`. URL prefix: `/admin/`.

```python
urlpatterns = [
    path("dashboard/",                         AdminDashboardView.as_view(),       name="admin_dashboard"),

    # Departments
    path("departments/",                       DepartmentListView.as_view(),       name="dept_list"),
    path("departments/create/",                DepartmentCreateView.as_view(),     name="dept_create"),
    path("departments/<int:pk>/edit/",         DepartmentEditView.as_view(),       name="dept_edit"),
    path("departments/<int:pk>/delete/",       DepartmentDeleteView.as_view(),     name="dept_delete"),

    # Subjects
    path("subjects/",                          SubjectListView.as_view(),          name="subject_list"),
    path("subjects/create/",                   SubjectCreateView.as_view(),        name="subject_create"),
    path("subjects/<int:pk>/edit/",            SubjectEditView.as_view(),          name="subject_edit"),
    path("subjects/<int:pk>/delete/",          SubjectDeleteView.as_view(),        name="subject_delete"),
    path("subjects/<int:pk>/assign-teachers/", AssignTeachersView.as_view(),       name="subject_assign_teachers"),

    # Teachers
    path("teachers/",                          TeacherListView.as_view(),          name="teacher_list"),
    path("teachers/create/",                   TeacherCreateView.as_view(),        name="teacher_create"),
    path("teachers/<int:pk>/edit/",            TeacherEditView.as_view(),          name="teacher_edit"),
    path("teachers/<int:pk>/deactivate/",      TeacherDeactivateView.as_view(),    name="teacher_deactivate"),

    # Students
    path("students/",                          StudentListView.as_view(),          name="student_list"),
    path("students/create/",                   StudentCreateView.as_view(),        name="student_create"),
    path("students/<int:pk>/edit/",            StudentEditView.as_view(),          name="student_edit"),
    path("students/<int:pk>/deactivate/",      StudentDeactivateView.as_view(),    name="student_deactivate"),

    # System Config
    path("config/",                            SystemConfigView.as_view(),         name="system_config"),
]
```

### Key View Behaviors

**`DepartmentDeleteView` (POST):**
- Check if any `Subject` has `department=this`. If yes, return error "Cannot delete: subjects are linked." Do not delete.

**`SubjectDeleteView` (POST):**
- Check if any `AttendanceSession` has `subject=this`. If yes, block deletion.

**`AssignTeachersView` (GET/POST):**
- GET: render form with all teachers, checkboxes for current assignments.
- POST: update `TeacherProfile.subjects` M2M for this subject.

**`TeacherCreateView` / `StudentCreateView` (POST):**
- Create `User` with appropriate role.
- Create linked `TeacherProfile` / `StudentProfile` in the same transaction.

**`SystemConfigView` (GET/POST):**
- GET: show form with current `qr_rotation_interval` value.
- POST: validate it is a positive integer, save to `SystemConfig`.

---

## 3. Admin Reports URLs — `reports/urls.py`

URL prefix: `/admin/`. All views decorated with `@admin_required`.

```python
urlpatterns = [
    path("reports/",                              ReportIndexView.as_view(),             name="report_index"),
    path("reports/sessions/<int:session_id>/",    SessionAttendanceReportView.as_view(), name="report_session"),
    path("proxy-logs/",                           ProxyLogListView.as_view(),            name="proxy_logs"),
]
```

**`ReportIndexView` (GET):**
- Filter form: select subject, optionally filter by date range.
- Lists matching sessions with link to detail view.

**`SessionAttendanceReportView` (GET):**
- Shows all `AttendanceRecord` rows for the session.
- Columns: student name, roll number, status, marked_by, marked_at.

**`ProxyLogListView` (GET):**
- Lists all `ProxyLog` rows.
- Query params: `?session_id=` and `?date=` for filtering.

---

## 4. Teacher URLs — `att_sessions/urls.py`

URL prefix: `/teacher/`. All views decorated with `@teacher_required`.

```python
urlpatterns = [
    path("dashboard/",                              TeacherDashboardView.as_view(),    name="teacher_dashboard"),
    path("sessions/",                               SessionListView.as_view(),         name="session_list"),
    path("sessions/create/",                        SessionCreateView.as_view(),       name="session_create"),
    path("sessions/<int:pk>/",                      SessionDetailView.as_view(),       name="session_detail"),
    path("sessions/<int:pk>/end/",                  SessionEndView.as_view(),          name="session_end"),
    path("sessions/<int:pk>/mode/qr/",              ActivateQRModeView.as_view(),      name="session_mode_qr"),
    path("sessions/<int:pk>/mode/manual/",          ActivateManualModeView.as_view(),  name="session_mode_manual"),
    path("sessions/<int:pk>/qr/",                   GetCurrentQRView.as_view(),        name="session_qr_json"),   # [JSON]
    path("sessions/<int:pk>/mark/<int:student_pk>/", ManualMarkView.as_view(),         name="session_manual_mark"),
]
```

### View Contracts

**`SessionCreateView` (GET/POST):**
- GET: form with dropdown of teacher's assigned subjects. Pre-fills date = today.
- POST:
  1. Check no active session exists for `(teacher, subject, date)`.
  2. Create `AttendanceSession`.
  3. Query `StudentProfile.objects.filter(department=subject.department, semester=subject.semester)`.
  4. Bulk-create `AttendanceRecord` for each student with `status="absent"`.
  5. Redirect to `session_detail`.

**`SessionDetailView` (GET):**
- Renders the session screen: current mode, student list with statuses, QR display area (if mode=qr).
- Passes `qr_rotation_interval` from `SystemConfig` as template variable (used by JS poller).

**`SessionEndView` (POST):**
- Set `session.status = "ended"`, `session.ended_at = now()`, `session.current_qr_token = None`.
- Save. Redirect to session detail (now read-only).

**`ActivateQRModeView` (POST):**
- Check `session.status != "ended"`.
- Set `session.mode = "qr"`. Save.
- Return redirect to `session_detail`.

**`ActivateManualModeView` (POST):**
- Check `session.status != "ended"`.
- Set `session.mode = "manual"`. Save.
- Return redirect to `session_detail`.

**`GetCurrentQRView` (GET) `[JSON]`:**
- Check `session.status == "active"` and `session.mode == "qr"`.
- Lazy rotation logic:
  ```python
  interval = int(SystemConfig.get("qr_rotation_interval", 30))
  if session.qr_generated_at is None or (now() - session.qr_generated_at).seconds >= interval:
      session.current_qr_token = generate_signed_token(session.id)
      session.qr_generated_at  = now()
      session.save(update_fields=["current_qr_token", "qr_generated_at"])
  ```
- Generate QR image from token URL.
- Response:
  ```json
  {
    "qr_image": "<base64 PNG string>",
    "expires_at": "<ISO8601 datetime>",
    "interval": 30
  }
  ```

**`ManualMarkView` (POST):**
- Check `session.status == "active"` and `session.mode == "manual"`.
- Toggle `AttendanceRecord` for `(session, student)`:
  - If currently `"absent"` → set `status="present"`, `marked_by="manual"`, `marked_at=now()`.
  - If currently `"present"` → set `status="absent"`, `marked_by="default"`, `marked_at=None`.
- Return JSON:
  ```json
  { "status": "present" }   // or "absent"
  ```
  (Used by JS to update the button state without full page reload.)

---

## 5. Student & Attendance Submission URLs

### `attendance/urls.py` — Student portal (prefix: `/student/`)

```python
urlpatterns = [
    path("dashboard/",                    StudentDashboardView.as_view(),        name="student_dashboard"),
    path("attendance/",                   StudentAttendanceListView.as_view(),   name="student_attendance"),
    path("attendance/<int:subject_pk>/",  StudentSubjectDetailView.as_view(),    name="student_subject_detail"),
]
```

**`StudentDashboardView` (GET):**
- For each subject whose `(department, semester)` matches the student, compute attendance summary:
  - Total sessions for that subject (status=ended or all active+ended), sessions where student is present.
- Render as a summary list.

**`StudentAttendanceListView` (GET):**
- Same as dashboard but more detailed — one row per subject with counts.

**`StudentSubjectDetailView` (GET):**
- Lists every `AttendanceSession` for the subject where student has a record.
- Columns: date, status (present/absent).

---

### `attendance/urls_submit.py` — QR Submission (prefix: `/attend/`)

```python
urlpatterns = [
    path("<str:token>/", AttendanceSubmitView.as_view(), name="attend_submit"),
]
```

**`AttendanceSubmitView` (GET):**
- Student must be logged in. If not: `redirect(f"/login/?next=/attend/{token}/")`
- Decode token (do not verify max_age yet — just read session_id from it to show session info).
- Render confirmation page: "You are about to mark attendance for [Subject] — [Date]. Confirm?"
- Page includes the WebGL fingerprint JS. On "Confirm" button click:
  1. JS runs `generateFingerprint()`.
  2. JS sets hidden input `webgl_hash` to result.
  3. JS submits the form via POST.

**`AttendanceSubmitView` (POST):**

Input:
```
token       : str (from URL)
webgl_hash  : str (64-char SHA-256 hex, from hidden form field)
```

Logic (exact order — do not change):
```python
interval = int(SystemConfig.get("qr_rotation_interval", 30))

# Step 1: Verify token
try:
    payload = verify_token(token, max_age=interval)
except (signing.BadSignature, signing.SignatureExpired):
    return error("QR code is invalid or has expired.")

session = AttendanceSession.objects.get(id=payload["session_id"])

# Step 2: Session must be active
if session.status == "ended":
    return error("This session has already ended.")

# Step 3: Session must be in QR mode
if session.mode != "qr":
    return error("QR attendance is not active for this session.")

student = request.user.student_profile

# Step 4: Must not already be marked present
record = AttendanceRecord.objects.get(session=session, student=student)
if record.status == "present":
    return error("You have already been marked present.")

# Step 5: Check for device conflict (proxy detection)
conflict = WebGLFingerprint.objects.filter(
    session=session, hash=webgl_hash
).exclude(student=student).first()

if conflict:
    ProxyLog.objects.create(
        session=session,
        attempted_by_student=student,
        conflicting_student=conflict.student,
        webgl_hash=webgl_hash,
        reason="device_conflict"
    )
    return error("Proxy attempt detected. Request rejected.")

# Step 6: Save fingerprint and mark present
WebGLFingerprint.objects.create(session=session, student=student, hash=webgl_hash)
record.status    = "present"
record.marked_by = "qr"
record.marked_at = now()
record.save()

return success("Attendance marked successfully.")
```

Response format (JSON for AJAX or redirect-with-message for plain form):
```json
{ "status": "success", "message": "Attendance marked successfully." }
{ "status": "error",   "message": "<reason string>" }
```

---

## 6. Access Control Summary

| URL Pattern | Role Required | Method |
|-------------|--------------|--------|
| `/login/` | None | GET, POST |
| `/admin/*` | `admin` | GET, POST |
| `/teacher/*` | `teacher` | GET, POST |
| `/student/*` | `student` | GET |
| `/attend/<token>/` | Any authenticated | GET, POST |

- Unauthenticated requests to protected URLs → redirect to `/login/?next=<url>`.
- Wrong role → return HTTP 403.
