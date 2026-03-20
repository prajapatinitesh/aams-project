# Vision & Problem Statement
## AAMS — Advanced Attendance Management System

---

## Purpose of This Document

This is a context file for an AI building the AAMS web application. It defines what the system is, what problem it solves, and the core verification mechanism. All implementation decisions must align with the logic described here.

---

## What AAMS Is

AAMS is a **Django-only, server-rendered web application** for a single college institution. It manages lecture attendance using a two-factor verification model to prevent proxy attendance. There are three user roles: Admin, Teacher, and Student.

---

## The Problem: Proxy Attendance

Proxy attendance = Student B marks attendance on behalf of absent Student A. Every common method is exploitable:

| Method | How it is bypassed |
|--------|-------------------|
| Paper sign-in | Physically sign for someone else |
| Roll call | Respond verbally for someone else |
| Static QR code | Screenshot and forward over chat; absent friend scans from anywhere |
| Rotating QR alone | Still shareable within the rotation window; does not prove physical device presence |

Root vulnerability: **a QR code is just an image — it can be forwarded in under a second**.

---

## The Solution: Two-Factor Attendance Verification

Two conditions must both pass before attendance is recorded.

### Factor 1 — Rotating QR Code (time-bound)
- Teacher starts a session. System generates a **signed token** embedded in a QR code.
- Token auto-rotates server-side every N seconds. N is a value stored in `SystemConfig`, set by Admin.
- Expired tokens are rejected at submission time regardless of whether the QR image is still displayed.
- This limits — but does not fully eliminate — the window for sharing a screenshot.

### Factor 2 — WebGL Device Fingerprint (device-bound)
- On attendance submission, the student's browser executes a JS function:
  - Creates a hidden `<canvas>` with a WebGL context.
  - Renders a fixed triangle using a fixed vertex + fragment shader.
  - Reads back the raw pixel buffer via `gl.readPixels`.
  - Hashes the buffer using `crypto.subtle.digest("SHA-256", pixels)`.
  - Returns a 64-character hex string.
- This hash varies by GPU and driver — it acts as a device identifier.
- On first submission for a session: hash is stored against the student + session.
- On subsequent submissions in the same session: if the submitted hash already exists for a **different student** in that session → reject and log as proxy attempt.

### Proxy Rejection Logic (exact rules)

```
Given: student S submits token T with webgl_hash H for session X

1. If token T is expired or invalid          → reject: "QR code expired"
2. If session X status = "ended"             → reject: "Session has ended"
3. If attendance_record(S, X).status = present → reject: "Already marked present"
4. If webgl_fingerprint(session=X, hash=H) exists for student != S
                                             → log proxy_attempt, reject: "Proxy attempt detected"
5. Else:
   - Insert webgl_fingerprint(session=X, student=S, hash=H)
   - Update attendance_record(S, X).status = "present", marked_by = "qr"
   - Return success
```

### Why This Stops Proxy

- Student A (in class) shares QR with absent Student B.
- **Case 1:** B uses own account + own device → new hash for B in this session → marked present normally. Not a proxy issue; the rotating window limits how long the QR is valid.
- **Case 2:** B uses A's account + B's own device → A's hash already recorded from A's device → hash mismatch → **rejected + logged**.
- **Case 3:** B uses A's device → physically impossible without taking the device.

---

## Scope

### In Scope
- Department and subject management (Admin)
- Teacher and student account creation and assignment (Admin)
- Attendance session lifecycle: create → QR mode / manual mode → end (Teacher)
- Auto-rotating signed QR code generation and validation
- WebGL fingerprint capture (client-side JS), storage, and proxy detection (server-side)
- Attendance records viewable on portal for all roles (no export)
- Proxy attempt logging with reason codes

### Out of Scope — Do Not Implement
- Timetable or schedule management
- Marks, grades, or exam results
- Fee management
- Notices or announcements
- Parent portal or notifications
- Minimum attendance threshold enforcement
- Mobile native app (Android / iOS)
- Multi-institution or multi-campus support
- Any form of data export (CSV, PDF, Excel, etc.)
