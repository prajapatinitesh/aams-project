from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, DetailView, TemplateView, View
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django import forms
from accounts.decorators import teacher_required
from accounts.models import User, SystemConfig
from departments.models import Subject, TeacherProfile, StudentProfile
from attendance.models import AttendanceRecord
from .models import AttendanceSession
from .utils import generate_signed_token, token_to_qr_base64

@method_decorator(teacher_required, name='dispatch')
class TeacherDashboardView(TemplateView):
    template_name = 'teacher/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.request.user.teacher_profile
        active_sessions = AttendanceSession.objects.filter(teacher=profile, status='active')
        context['assigned_subjects'] = profile.subjects.all()
        context['active_sessions'] = active_sessions
        # Always allow starting a new session since multiple are permitted
        context['subjects_without_active_session'] = profile.subjects.all()
        return context

@method_decorator(teacher_required, name='dispatch')
class SessionListView(ListView):
    model = AttendanceSession
    template_name = 'teacher/session_list.html'
    context_object_name = 'sessions'

    def get_queryset(self):
        return AttendanceSession.objects.filter(teacher=self.request.user.teacher_profile).order_by('-date', '-created_at')

@method_decorator(teacher_required, name='dispatch')
class SessionCreateView(View):
    def get(self, request):
        subjects = request.user.teacher_profile.subjects.all()
        return render(request, 'teacher/session_form.html', {'subjects': subjects, 'today': timezone.now().date()})

    def post(self, request):
        subject_id = request.POST.get('subject')
        date = request.POST.get('date')
        teacher = request.user.teacher_profile
        subject = get_object_or_404(Subject, pk=subject_id)

        # Relaxation: Multiple sessions allowed per request.
        # No check for existing sessions.

        session = AttendanceSession.objects.create(
            subject=subject,
            teacher=teacher,
            date=date,
            status='active',
            mode='none'
        )

        # Bulk create records for matching students
        students = StudentProfile.objects.filter(department=subject.department, semester=subject.semester)
        records = [
            AttendanceRecord(session=session, student=student, status='absent')
            for student in students
        ]
        AttendanceRecord.objects.bulk_create(records)

        messages.success(request, f"Session created for {subject.name}. {len(records)} students enrolled.")
        return redirect('session_detail', pk=session.pk)

@method_decorator(teacher_required, name='dispatch')
class SessionDetailView(DetailView):
    model = AttendanceSession
    template_name = 'teacher/session_detail.html'
    context_object_name = 'session'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['records'] = self.object.records.select_related('student__user').order_by('student__roll_number')
        context['qr_interval'] = SystemConfig.get("qr_rotation_interval", 30)
        return context

@method_decorator(teacher_required, name='dispatch')
class SessionEndView(View):
    def post(self, request, pk):
        session = get_object_or_404(AttendanceSession, pk=pk, teacher=request.user.teacher_profile)
        session.status = 'ended'
        session.mode = 'none'
        session.current_qr_token = None
        session.ended_at = timezone.now()
        session.save()
        messages.success(request, "Session ended.")
        return redirect('session_detail', pk=pk)

@method_decorator(teacher_required, name='dispatch')
class ActivateQRModeView(View):
    def post(self, request, pk):
        session = get_object_or_404(AttendanceSession, pk=pk, teacher=request.user.teacher_profile)
        if session.status == 'active':
            session.mode = 'qr'
            session.save()
        return redirect('session_detail', pk=pk)

@method_decorator(teacher_required, name='dispatch')
class ActivateManualModeView(View):
    def post(self, request, pk):
        session = get_object_or_404(AttendanceSession, pk=pk, teacher=request.user.teacher_profile)
        if session.status == 'active':
            session.mode = 'manual'
            session.save()
        return redirect('session_detail', pk=pk)

@method_decorator(teacher_required, name='dispatch')
class GetCurrentQRView(View):
    def get(self, request, pk):
        session = get_object_or_404(AttendanceSession, pk=pk, teacher=request.user.teacher_profile)
        if session.status != 'active' or session.mode != 'qr':
            return JsonResponse({'error': 'QR mode not active'}, status=400)

        interval = int(SystemConfig.get("qr_rotation_interval", 30))
        now = timezone.now()
        
        # Lazy rotation
        if session.qr_generated_at is None or (now - session.qr_generated_at).total_seconds() >= interval:
            session.current_qr_token = generate_signed_token(session.id)
            session.qr_generated_at = now
            session.save(update_fields=['current_qr_token', 'qr_generated_at'])

        # Generate base64 QR
        base_url = request.build_absolute_uri('/')[:-1]
        qr_image = token_to_qr_base64(session.current_qr_token, base_url)
        
        return JsonResponse({
            'qr_image': qr_image,
            'interval': interval,
            'expires_at': (session.qr_generated_at + timezone.timedelta(seconds=interval)).isoformat()
        })

@method_decorator(teacher_required, name='dispatch')
class ManualMarkView(View):
    def post(self, request, pk, student_pk):
        session = get_object_or_404(AttendanceSession, pk=pk, teacher=request.user.teacher_profile)
        student = get_object_or_404(StudentProfile, pk=student_pk)
        record = get_object_or_404(AttendanceRecord, session=session, student=student)
        
        if record.status == 'absent':
            record.status = 'present'
            record.marked_by = 'manual'
            record.marked_at = timezone.now()
        else:
            record.status = 'absent'
            record.marked_by = 'default'
            record.marked_at = None
        
        record.save()
        return JsonResponse({'status': record.status})

@method_decorator(teacher_required, name='dispatch')
class SessionDeleteView(View):
    def post(self, request, pk):
        session = get_object_or_404(AttendanceSession, pk=pk, teacher=request.user.teacher_profile)
        subject_name = session.subject.name
        session.delete()
        messages.success(request, f"Session for {subject_name} has been deleted.")
        return redirect('session_list')
