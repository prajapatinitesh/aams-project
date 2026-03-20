import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aams.settings')
django.setup()

from accounts.models import User, SystemConfig
from departments.models import Department, Subject, TeacherProfile, StudentProfile

def seed_data():
    print("Starting data seeding...")

    # 1. System Config
    SystemConfig.objects.get_or_create(key="qr_rotation_interval", defaults={"value": "30"})
    print("- SystemConfig seeded.")

    # 2. Admin User
    admin_email = "admin@college.com"
    if not User.objects.filter(email=admin_email).exists():
        User.objects.create_superuser(
            email=admin_email,
            password="admin",
            full_name="College Admin",
            role="admin"
        )
        print(f"- Admin {admin_email} created.")

    # 3. Departments
    dept_names = ["Computer Engineering", "Mechanical", "AI&DS", "Civil"]
    depts = []
    for name in dept_names:
        dept, created = Department.objects.get_or_create(name=name)
        depts.append(dept)
    print(f"- {len(depts)} Departments created.")

    # 4. Subjects & Teachers
    teacher_count = 1
    semesters = [1, 3, 5]
    
    for dept in depts:
        for sem in semesters:
            # Create 1 subject for this dept/sem
            sub_name = f"{dept.name} Core {sem}"
            subject, created = Subject.objects.get_or_create(
                name=sub_name,
                department=dept,
                semester=sem
            )
            
            # Create a teacher for this subject
            t_email = f"teacher{teacher_count}@college.com"
            if not User.objects.filter(email=t_email).exists():
                t_user = User.objects.create_user(
                    email=t_email,
                    password="teacher",
                    full_name=f"Professor {teacher_count}",
                    role="teacher",
                    is_staff=True
                )
                t_profile = TeacherProfile.objects.create(user=t_user, department=dept)
                subject.teachers.add(t_profile)
                teacher_count += 1
    
    print(f"- {teacher_count - 1} Teachers and matching subjects created.")

    # 5. Students (50 students)
    student_total = 50
    for i in range(1, student_total + 1):
        s_email = f"student{i}@college.com"
        if not User.objects.filter(email=s_email).exists():
            s_user = User.objects.create_user(
                email=s_email,
                password="student",
                full_name=f"Student {i}",
                role="student"
            )
            # Distribute among depts and semesters
            dept = random.choice(depts)
            sem = random.choice(semesters)
            StudentProfile.objects.create(
                user=s_user,
                department=dept,
                semester=sem,
                roll_number=f"R2026-{i:03d}"
            )
    
    print(f"- {student_total} Students created across various departments.")
    print("Seeding complete! Use 'python manage.py run_server' to start.")

if __name__ == "__main__":
    seed_data()
