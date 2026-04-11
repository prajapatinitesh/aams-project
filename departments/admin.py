from django.contrib import admin
from .models import Department, Subject, TeacherProfile, StudentProfile

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "department", "semester")
    list_filter = ("department", "semester")
    search_fields = ("name",)

@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "department")
    list_filter = ("department",)
    search_fields = ("user__email", "user__full_name")

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "department", "semester", "roll_number")
    list_filter = ("department", "semester")
    search_fields = ("user__email", "user__full_name", "roll_number")
