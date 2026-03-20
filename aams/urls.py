from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("",              include("accounts.urls")),
    path("admin/",        include("departments.urls_admin")),
    path("admin/",        include("reports.urls")),
    path("teacher/",      include("att_sessions.urls")),
    path("student/",      include("attendance.urls")),
]
