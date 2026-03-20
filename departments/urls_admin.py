from django.urls import path
from .views_admin import (
    AdminDashboardView,
    DepartmentListView, DepartmentCreateView, DepartmentEditView, DepartmentDeleteView,
    SubjectListView, SubjectCreateView, SubjectEditView, SubjectDeleteView, AssignTeachersView,
    TeacherListView, TeacherCreateView, TeacherEditView, TeacherDeactivateView,
    StudentListView, StudentCreateView, StudentEditView, StudentDeactivateView,
    SystemConfigView
)

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
