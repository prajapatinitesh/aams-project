from django.urls import path
from .views import (
    ReportIndexView,
    SessionAttendanceReportView,
    AdminMarkAttendanceView,
    ProxyLogListView
)

urlpatterns = [
    path("reports/",                              ReportIndexView.as_view(),             name="report_index"),
    path("reports/sessions/<int:session_id>/",    SessionAttendanceReportView.as_view(), name="report_session"),
    path("reports/mark/<int:record_id>/",         AdminMarkAttendanceView.as_view(),     name="admin_mark_attendance"),
    path("proxy-logs/",                           ProxyLogListView.as_view(),            name="proxy_logs"),
]
