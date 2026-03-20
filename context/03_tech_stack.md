# Tech Stack
## AAMS — Advanced Attendance Management System

---

## Purpose of This Document

Exact technology choices and configuration decisions for building AAMS. Use these as the implementation baseline — do not substitute alternatives unless a constraint makes them unavoidable.

---

## Core Stack

| Layer | Choice | Version / Notes |
|-------|--------|----------------|
| Language | Python | 3.11+ |
| Web Framework | Django | 4.2 LTS |
| Database (dev) | SQLite | Django default, zero config |
| Database (prod) | MySQL | stable recommended |
| Frontend | Django Templates | No React, no Vue — server-rendered HTML only |
| CSS | Plain CSS + Bootstrap 5 (CDN) | Keep it simple; no build step |

---

## Python Packages

```txt
# requirements.txt
Django==4.2.*
Pillow>=10.0          # Required for QR code image rendering
qrcode[pil]>=7.4      # QR code generation
psycopg2-binary>=2.9  # PostgreSQL driver (prod only)
```

No Celery, no Redis, no Django REST Framework, no JWT libraries. Keep dependencies minimal.

---

## Django App Structure

```
aams/                        ← Django project root
├── aams/                    ← Project settings package
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── accounts/                ← Custom User model, login/logout, role-based access
├── departments/             ← Department and Subject models + Admin CRUD views
├── sessions/                ← AttendanceSession lifecycle, QR token logic
├── attendance/              ← AttendanceRecord, WebGL hash validation, proxy logging
├── reports/                 ← Attendance and proxy log query views
└── templates/               ← All HTML templates (global template dir)
    ├── base.html
    ├── accounts/
    ├── admin_panel/
    ├── teacher/
    └── student/
```

---

## Authentication

- Use Django's built-in `AbstractBaseUser` + `PermissionsMixin` for the custom User model.
- Session-based auth (Django's default `SessionMiddleware` + `AuthenticationMiddleware`). No JWT.
- Custom User model fields: `email` (username field), `full_name`, `role` (`admin` / `teacher` / `student`), `is_active`, `is_staff`.
- Set `AUTH_USER_MODEL = "accounts.User"` in settings.
- Role-based access: implement three decorators — `@admin_required`, `@teacher_required`, `@student_required` — that check `request.user.role` and return 403 or redirect to login if not matching.

---

## QR Code Generation

```python
import qrcode
import io, base64
from django.core import signing

def generate_signed_token(session_id: int) -> str:
    """Returns a signed token string encoding session_id + timestamp."""
    return signing.dumps({"session_id": session_id}, salt="qr-attendance")

def verify_token(token: str, max_age: int) -> dict:
    """Raises signing.BadSignature or signing.SignatureExpired if invalid."""
    return signing.loads(token, salt="qr-attendance", max_age=max_age)

def token_to_qr_base64(token: str, attend_base_url: str) -> str:
    """Generates a QR code PNG as base64 string from the attendance URL."""
    url = f"{attend_base_url}/attend/{token}/"
    img = qrcode.make(url)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()
```

- `signing.dumps` + `signing.loads` with `max_age` handles token expiry automatically.
- `max_age` = value of `SystemConfig.get("qr_rotation_interval")` at the time of verification.
- Token is stored in `AttendanceSession.current_qr_token`. On each call to the `/qr/` polling endpoint, check if the stored token is still valid via `verify_token`. If expired, call `generate_signed_token` and save the new one first, then return it.

---

## WebGL Fingerprint (Client-side)

- The JS function lives in `static/js/fingerprint.js`.
- It is included only on the student attendance confirmation page.
- Called when the student clicks "Confirm Attendance".
- The resulting hash is added to a hidden `<input name="webgl_hash">` field before the form is submitted.
- Fallback: if `canvas.getContext("webgl")` returns null, disable the submit button and show an error message. Do not silently submit without a hash.

---

## QR Rotation Strategy

**Use lazy rotation — no background task needed.**

Every time the teacher's frontend polls `GET /teacher/sessions/<id>/qr/`:
1. Load `session.current_qr_token` and `session.qr_generated_at`.
2. Check if `(now - qr_generated_at).seconds >= qr_rotation_interval`.
3. If yes: generate a new token, update `current_qr_token` and `qr_generated_at`, save.
4. Return the (possibly new) token as a base64 QR image + expiry time.

**Frontend polling:** Use `setInterval(() => fetchNewQR(), N * 1000)` in the teacher session template. N comes from a template variable injected by the view.

---

## Settings (Key Values)

```python
# settings.py

AUTH_USER_MODEL = "accounts.User"

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/dashboard/"

# Default QR rotation interval — overridden by SystemConfig at runtime
QR_ROTATION_INTERVAL_DEFAULT = 30  # seconds

INSTALLED_APPS = [
    # Django built-ins
    "django.contrib.admin",       # Keep for DB shell access; not used as main admin UI
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # AAMS apps
    "accounts",
    "departments",
    "sessions",      # Note: avoid naming conflict with Django's own sessions app — rename to "att_sessions" if needed
    "attendance",
    "reports",
]
```

> **Naming conflict warning:** Django has a built-in app called `django.contrib.sessions`. Name the AAMS sessions app `att_sessions` (or `lecture_sessions`) to avoid import conflicts.

---

## Database

- Use Django ORM exclusively. No raw SQL.
- Migrations generated via `python manage.py makemigrations`.
- All FKs use `on_delete=models.PROTECT` by default unless cascade is explicitly correct.
- Add `db_index=True` on `WebGLFingerprint.hash` (queried on every attendance submission).

---

## Static Files and Templates

- All templates in a single top-level `templates/` directory (configure `DIRS` in settings).
- All static files in a single top-level `static/` directory.
- Use `{% extends "base.html" %}` for all pages.
- `base.html` includes nav links conditional on `request.user.role`.
