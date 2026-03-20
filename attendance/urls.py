from django.urls import path
from .views import (
    student_dashboard, AttendanceSubmitView, AttendanceHistoryView,

    AjaxMarkAttendanceView, StudentSubjectDetailView
)

urlpatterns = [
    path("dashboard/", student_dashboard, name="student_dashboard"),

    path("history/",   AttendanceHistoryView.as_view(), name="student_history"),
    path("subject/<int:subject_id>/", StudentSubjectDetailView.as_view(), name="student_subject_detail"),
    path("scan/ajax/", AjaxMarkAttendanceView.as_view(), name="mark_attendance_ajax"),
    path("scan/<str:token>/", AttendanceSubmitView.as_view(), name="mark_attendance"),
]
