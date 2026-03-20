# Product Requirements Document (PRD)
## AAMS — Advanced Attendance Management System

---

## Purpose of This Document

Exact feature requirements for building AAMS. Each section defines what must be implemented, what the system must do automatically, and what constraints apply. Treat every requirement as a build instruction.

---

## 1. Roles and Access

Three roles exist. Each role has its own dashboard. Role is stored on the User model.

| Role | Access Level |
|------|-------------|
| `admin` | Full system — departments, subjects, users, reports, proxy logs |
| `teacher` | Own sessions only — create sessions, control QR/manual mode, view attendance |
| `student` | Own attendance only — submit via QR, view own records |

Rules:
- All three roles authenticate with email + password.
- After login, each role redirects to its own dashboard URL.
- No role can access another role's views. Enforce with a decorator or mixin on every view.
- Admin creates all accounts (teacher and student). There is no self-registration.

---

## 2. Admin Features

### 2.1 Department Management
- CRUD operations on departments.
- Each department has: `name` (unique).
- Deleting a department must be blocked if subjects are linked to it (show error, do not cascade delete blindly).

### 2.2 Subject Management
- CRUD operations on subjects.
- Each subject has: `name`, `department` (FK), `semester` (integer).
- Admin assigns one or more teachers to a subject. This is a many-to-many relationship.

### 2.3 Teacher Account Management
- Admin creates teacher accounts: `full_name`, `email`, `password`, `department`.
- Admin can edit or deactivate (soft delete via `is_active=False`) teacher accounts.

### 2.4 Student Account Management
- Admin creates student accounts: `full_name`, `email`, `password`, `department`, `semester`, `roll_number`.
- Roll number must be unique within the same department + semester combination.
- Admin can edit or deactivate student accounts.
- Admin does **not** manually enroll students in subjects. Enrollment is by department + semester match: a student is considered enrolled in all subjects whose `department` and `semester` match the student's own. This is resolved at session creation time.

### 2.5 System Config
- Admin can set `qr_rotation_interval` (integer, seconds). Default: 30.
- This value is read at QR generation time. Changing it affects all future sessions.

### 2.6 Reports
- Admin can view attendance for any session: list of students with present/absent status.
- Admin can view all proxy logs: filterable by session and date.

---

## 3. Teacher Features

### 3.1 Session Creation
- Teacher selects a subject (from their assigned subjects) and clicks "Start Session".
- On creation:
  1. A new `AttendanceSession` row is created with `status = "active"`, `mode = "none"`.
  2. All students whose `department` and `semester` match the subject's `department` and `semester` are fetched.
  3. One `AttendanceRecord` row is created per student with `status = "absent"` (default). This happens automatically — the teacher does not do this manually.
- A teacher can have multiple sessions (across different subjects).

### 3.2 QR Mode
- Teacher activates QR mode: session `mode` is set to `"qr"`.
- System generates a signed QR token and stores it in `AttendanceSession.current_qr_token` with `qr_generated_at = now()`.
- The token must encode: `session_id` + `issued_at` timestamp. It must be signed (use `django.core.signing`).
- Token validity window = `qr_rotation_interval` seconds from `qr_generated_at`.
- **Auto-rotation:** A background mechanism (or request-time lazy rotation — see note below) checks if `now() - qr_generated_at >= qr_rotation_interval`. If yes, a new token is generated and saved before being returned.
- Teacher's session screen polls `GET /teacher/sessions/<id>/qr/` every N seconds. This endpoint returns the current QR as a base64 PNG and the expiry timestamp.
- The teacher does not manually trigger rotation.

> **Implementation note on rotation:** Since Django has no built-in scheduler, implement lazy rotation: every time the `/qr/` endpoint is called, check if the current token has expired and regenerate if needed before responding. This is simpler than a background task and correct for this use case.

### 3.3 Manual Mode
- Teacher activates manual mode: session `mode` is set to `"manual"`.
- Teacher sees the full student list for the session, each showing current status.
- Teacher can toggle any student to `"present"`. This sets `marked_by = "manual"`.
- Toggling back to absent is also allowed (in case of a mistake).
- Absent is the default — teacher does not need to explicitly mark absent students.

### 3.4 Mode Switching
- Teacher can switch between QR mode and Manual mode at any point during an active session.
- Switching mode does **not** reset or overwrite existing attendance records.
- Both modes can be used within the same session, but not simultaneously (only one mode is active at a time; `mode` field holds the current one).

### 3.5 Ending a Session
- Teacher clicks "End Session". Session `status` is set to `"ended"`, `ended_at = now()`, `current_qr_token = null`.
- After this: no QR scans accepted, no manual toggles allowed, session is read-only.
- Teacher can view the final attendance record for any ended session.

---

## 4. Student Features

### 4.1 Marking Attendance via QR
- Student opens the attendance URL (decoded from the QR code) on their device browser.
- The page shows a confirmation screen ("Mark yourself present for [Subject] — [Date]?") with a "Confirm" button.
- On confirm:
  1. Browser runs the WebGL fingerprint function (see Section 6) and gets the hash.
  2. Browser POSTs `{ token, webgl_hash }` to the server.
  3. Server runs proxy rejection logic (see Vision doc, Section: Proxy Rejection Logic).
  4. Page shows success or error message.
- Student must be logged in. If not logged in, redirect to login first, then return to this URL after login.

### 4.2 Viewing Attendance
- Student sees a list of their enrolled subjects with a summary (e.g., "8 / 12 sessions present").
- Student can drill into a subject to see session-by-session status (date, present/absent).
- No export. No editing. Read-only.

---

## 5. Session Lifecycle State Machine

```
[Created] → mode: "none",   status: "active"
     ↓
[QR Mode] → mode: "qr",     status: "active"   (students can scan)
     ↓ ↑  (teacher can switch back and forth)
[Manual]  → mode: "manual", status: "active"   (teacher toggles students)
     ↓
[Ended]   → mode: any,      status: "ended"    (read-only, no more changes)
```

Transitions:
- `none → qr`: teacher activates QR mode
- `none → manual`: teacher activates manual mode
- `qr → manual`: teacher switches mode
- `manual → qr`: teacher switches mode
- `any → ended`: teacher ends session (irreversible)

---

## 6. WebGL Fingerprint Function (Client-side JS)

Implement exactly as follows. Do not modify the shader or geometry — consistency of output is critical for the hash to be reproducible on the same device.

```javascript
async function generateFingerprint() {
  const canvas = document.createElement("canvas");
  canvas.width = 256;
  canvas.height = 256;
  const gl = canvas.getContext("webgl");
  if (!gl) return null;

  const vsSource = `
    attribute vec2 position;
    void main(){ gl_Position = vec4(position, 0.0, 1.0); }
  `;
  const fsSource = `
    void main(){ gl_FragColor = vec4(0.3, 0.7, 0.2, 1.0); }
  `;

  function compile(type, source) {
    const shader = gl.createShader(type);
    gl.shaderSource(shader, source);
    gl.compileShader(shader);
    return shader;
  }

  const program = gl.createProgram();
  gl.attachShader(program, compile(gl.VERTEX_SHADER, vsSource));
  gl.attachShader(program, compile(gl.FRAGMENT_SHADER, fsSource));
  gl.linkProgram(program);
  gl.useProgram(program);

  const vertices = new Float32Array([0, 0.9, -0.9, -0.9, 0.9, -0.9]);
  const buffer = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
  gl.bufferData(gl.ARRAY_BUFFER, vertices, gl.STATIC_DRAW);

  const position = gl.getAttribLocation(program, "position");
  gl.enableVertexAttribArray(position);
  gl.vertexAttribPointer(position, 2, gl.FLOAT, false, 0, 0);

  gl.viewport(0, 0, canvas.width, canvas.height);
  gl.clearColor(0.1, 0.1, 0.1, 1);
  gl.clear(gl.COLOR_BUFFER_BIT);
  gl.drawArrays(gl.TRIANGLES, 0, 3);

  const pixels = new Uint8Array(canvas.width * canvas.height * 4);
  gl.readPixels(0, 0, canvas.width, canvas.height, gl.RGBA, gl.UNSIGNED_BYTE, pixels);

  const hashBuffer = await crypto.subtle.digest("SHA-256", pixels);
  return Array.from(new Uint8Array(hashBuffer))
    .map(b => b.toString(16).padStart(2, "0"))
    .join("");
}
```

- Call this function after the user clicks "Confirm Attendance".
- If `gl` is null (WebGL not supported), block attendance submission and show error: "Your browser does not support WebGL. Attendance cannot be marked from this device."
- The returned hash is a 64-character hex string. Submit it as `webgl_hash` in the POST body.

---

## 7. Constraints and Validation Rules

| Rule | Detail |
|------|--------|
| Roll number uniqueness | Unique per `(department, semester)` combination |
| QR token scope | Token encodes `session_id` — a token from session A cannot mark attendance in session B |
| Proxy detection scope | WebGL hash uniqueness is checked per session, not globally |
| Ended session | All write operations (QR scan, manual mark) must check `session.status != "ended"` before proceeding |
| Mode enforcement | QR scans are only accepted when `session.mode == "qr"`. Manual marks only when `session.mode == "manual"`. |
| Student enrollment | Determined by matching `student.department == subject.department` AND `student.semester == subject.semester` |
