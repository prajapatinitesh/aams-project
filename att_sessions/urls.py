from django.urls import path
from .views import (
    TeacherDashboardView,
    SessionListView, SessionCreateView, SessionDetailView, SessionEndView,
    ActivateQRModeView, ActivateManualModeView, GetCurrentQRView, ManualMarkView,
    SessionDeleteView
)

urlpatterns = [
    path("dashboard/",                              TeacherDashboardView.as_view(),    name="teacher_dashboard"),
    path("sessions/",                               SessionListView.as_view(),         name="session_list"),
    path("sessions/create/",                        SessionCreateView.as_view(),       name="session_create"),
    path("sessions/<int:pk>/",                      SessionDetailView.as_view(),       name="session_detail"),
    path("sessions/<int:pk>/end/",                  SessionEndView.as_view(),          name="session_end"),
    path("sessions/<int:pk>/mode/qr/",              ActivateQRModeView.as_view(),      name="session_mode_qr"),
    path("sessions/<int:pk>/mode/manual/",          ActivateManualModeView.as_view(),  name="session_mode_manual"),
    path("sessions/<int:pk>/qr/",                   GetCurrentQRView.as_view(),        name="session_qr_json"),
    path("sessions/<int:pk>/mark/<int:student_pk>/", ManualMarkView.as_view(),         name="session_manual_mark"),
    path("sessions/<int:pk>/delete/",               SessionDeleteView.as_view(),       name="session_delete"),
]
