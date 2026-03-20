# 🎓 AAMS: Advanced Attendance Management System

[![Django](https://img.shields.io/badge/Django-4.2-092E20?style=for-the-badge&logo=django)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Status-Beta-E9711C?style=for-the-badge)](https://github.com/)

Advanced Attendance Management System (AAMS) is a robust, security-focused web application designed to eliminate **proxy attendance** in academic environments. Unlike traditional systems, AAMS uses a combination of time-bound rotating QR codes and device-specific WebGL fingerprinting to ensure that students are physically present and using their own devices to mark attendance.

---

## 🚀 Key Features

### 🛡️ Anti-Proxy Security
- **WebGL Device Fingerprinting**: Generates a unique hardware-based hash for each student device. The system blocks attendance if multiple accounts attempt to sign in from the same physical hardware.
- **Dynamic QR Rotation**: Signed attendance tokens rotate every 30 seconds (configurable), preventing students from sharing screenshots of QR codes with absent peers.

### 👤 Role-Based Portals
- **Administrator Hub**: Centralized management for Departments, Subjects, Faculty, and Students. Access to system-wide logs and proxy detection alerts.
- **Faculty Workspace**: Start/End sessions, toggle between QR and Manual modes, and view real-time attendance stats for assigned subjects.
- **Student Dashboard**: Scan QR codes instantly, track attendance history, and monitor performance analysis across subjects.

### 📊 Intelligence & Reporting
- **Automated Logging**: Every attendance mark recorded with timestamp and device ID.
- **Proxy Alert System**: Detects and flags suspicious behavior for administrative review.

---

## 🛠️ Tech Stack

- **Core**: [Django 4.2](https://www.djangoproject.com/) (Python)
- **Database**: SQLite (Default) | PostgreSQL ready
- **Frontend**: Bootstrap 5, Vanilla JavaScript, HTML5/CSS3
- **QR Engine**: `qrcode[pil]` for secure server-side generation
- **Scanning**: `html5-qrcode` for high-performance browser-side scanning

---

## ⚙️ Installation & Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/prajapatinitesh/aams-project.git
   cd aams-project
   ```

2. **Setup Virtual Environment**:
   ```bash
   python -m venv venv
   
   # Linux/Mac:
   source venv/bin/activate  
   # Windows: 
   venv/Scripts/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Database Initialization**:
   ```bash
   python manage.py migrate
   ```

5. **Seed Initial Data**:
   Creates default academic structure and test accounts.
   ```bash
   python seed_data.py
   ```

6. **Run Server**:
   ```bash
   python manage.py runserver
   ```

---

## 🧪 Testing Credentials (Post-Seeding)

| Role | Username | Password |
| :--- | :--- | :--- |
| **Admin** | `admin@college.com` | `admin` |
| **Teacher** | `teacher1@college.com` | `teacher` |
| **Student** | `student1@college.com` | `student` |

---

## 📜 License & Acknowledgement

Distributed under the **MIT License**. See `LICENSE` for more information.

Developed by **APEX Group (No. 12)** @ Rizvi College of Engineering.
- Khan Istiyaq
- Hanmante Ashish
- Mishra Priyanshu
- Prajapati Nitesh

*Guided by Prof. Mohammed Juned.*
