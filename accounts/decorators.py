from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

def admin_required(view_func):
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.role == 'admin':
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return _wrapped_view

def teacher_required(view_func):
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.role == 'teacher':
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return _wrapped_view

def student_required(view_func):
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.role == 'student':
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return _wrapped_view
