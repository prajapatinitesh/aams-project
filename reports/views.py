from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, TemplateView, View
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.utils import timezone
from accounts.decorators import admin_required
from att_sessions.models import AttendanceSession
from attendance.models import AttendanceRecord, ProxyLog
from departments.models import Subject

@method_decorator(admin_required, name='dispatch')
class ReportIndexView(TemplateView):
    template_name = 'admin_panel/report_index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from departments.models import Department, TeacherProfile
        
        dept_id = self.request.GET.get('department')
        subject_id = self.request.GET.get('subject')
        teacher_id = self.request.GET.get('teacher')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        departments = Department.objects.all()
        teachers = TeacherProfile.objects.all().select_related('user')
        subjects = Subject.objects.all()
        
        if dept_id:
            subjects = subjects.filter(department_id=dept_id)
            
        sessions = AttendanceSession.objects.all().select_related('subject', 'teacher__user').order_by('-date', '-created_at')
        
        if dept_id:
            sessions = sessions.filter(subject__department_id=dept_id)
        if subject_id:
            sessions = sessions.filter(subject_id=subject_id)
        if teacher_id:
            sessions = sessions.filter(teacher_id=teacher_id)
        if date_from:
            sessions = sessions.filter(date__gte=date_from)
        if date_to:
            sessions = sessions.filter(date__lte=date_to)
            
        context.update({
            'subjects': subjects,
            'departments': departments,
            'teachers': teachers,
            'sessions': sessions,
            'selected_subject': int(subject_id) if subject_id else None,
            'selected_dept': int(dept_id) if dept_id else None,
            'selected_teacher': int(teacher_id) if teacher_id else None,
            'date_from': date_from,
            'date_to': date_to,
        })
        return context

@method_decorator(admin_required, name='dispatch')
class SessionAttendanceReportView(ListView):
    model = AttendanceRecord
    template_name = 'admin_panel/report_session.html'
    context_object_name = 'records'

    def get_queryset(self):
        return AttendanceRecord.objects.filter(session_id=self.kwargs['session_id']).select_related('student__user')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['session'] = get_object_or_404(AttendanceSession, pk=self.kwargs['session_id'])
        return context

@method_decorator(admin_required, name='dispatch')
class ProxyLogListView(ListView):
    model = ProxyLog
    template_name = 'admin_panel/proxy_logs.html'
    context_object_name = 'logs'

    def get_queryset(self):
        queryset = ProxyLog.objects.all().order_by('-attempted_at')
        session_id = self.request.GET.get('session_id')
        if session_id:
            queryset = queryset.filter(session_id=session_id)
        return queryset
@method_decorator(admin_required, name='dispatch')
class AdminMarkAttendanceView(View):
    def post(self, request, record_id):
        record = get_object_or_404(AttendanceRecord, pk=record_id)
        if record.status == 'absent':
            record.status = 'present'
            record.marked_by = 'admin'
            record.marked_at = timezone.now()
        else:
            record.status = 'absent'
            record.marked_by = 'default'
            record.marked_at = None
        record.save()
        return JsonResponse({'status': record.status, 'message': 'Updated by Admin'})
