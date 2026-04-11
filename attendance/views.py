from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.generic import ListView, TemplateView, View, DetailView
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.utils import timezone
from django.core import signing
from django.db import transaction
from accounts.decorators import student_required
from att_sessions.models import AttendanceSession
from att_sessions.utils import verify_token
from departments.models import StudentProfile
from accounts.models import SystemConfig
from att_sessions.geoutils import haversine_distance
from .models import AttendanceRecord, WebGLFingerprint, ProxyLog

@student_required
def student_dashboard(request):
    student = request.user.student_profile
    
    # 1. Total Attendance
    all_records = AttendanceRecord.objects.filter(student=student)
    total_sessions = all_records.count()
    total_present = all_records.filter(status='present').count()
    
    overall_attendance = {
        'count': f"{total_present}/{total_sessions}",
        'percent': round((total_present / total_sessions * 100), 1) if total_sessions > 0 else 0
    }

    # 2. Subject-wise Attendance
    subject_stats = []
    subjects = student.department.subjects.filter(semester=student.semester)
    for sub in subjects:
        sub_records = all_records.filter(session__subject=sub)
        sub_total = sub_records.count()
        sub_present = sub_records.filter(status='present').count()
        subject_stats.append({
            'name': sub.name,
            'id': sub.id,
            'percent': round((sub_present / sub_total * 100), 1) if sub_total > 0 else 0,
            'count': f"{sub_present}/{sub_total}"
        })

    # 3. My Courses & Teachers
    courses = []
    subjects = student.department.subjects.filter(semester=student.semester).prefetch_related('teachers__user')
    for sub in subjects:
        courses.append({
            'name': sub.name,
            'teachers': ", ".join([t.user.full_name for t in sub.teachers.all()]) or "Not Assigned"
        })

    context = {
        'overall_attendance': overall_attendance,
        'subject_stats': subject_stats,
        'recent_attendance': all_records.order_by('-marked_at')[:5],
        'courses': courses,
    }
    return render(request, 'student/dashboard.html', context)

@method_decorator(student_required, name='dispatch')
class AttendanceSubmitView(View):
    def get(self, request, token):
        try:
            max_age = int(SystemConfig.get("qr_rotation_interval", 30)) + 5
            data = verify_token(token, max_age)
            session = get_object_or_404(AttendanceSession, pk=data['session_id'], status='active', mode='qr')
            return render(request, 'student/attend_confirm.html', {'session': session, 'token': token})
        except (signing.SignatureExpired, signing.BadSignature):
            messages.error(request, "QR Code expired or invalid. Please scan again.")
            return redirect('student_dashboard')

    def post(self, request, token):
        webgl_hash = request.POST.get('webgl_hash')
        lat = request.POST.get('latitude')
        lng = request.POST.get('longitude')
        student = request.user.student_profile
        
        if not webgl_hash:
            messages.error(request, "Device verification failed. Hardware fingerprint missing.")
            return redirect('student_dashboard')

        try:
            max_age = int(SystemConfig.get("qr_rotation_interval", 30)) + 10
            data = verify_token(token, max_age)
            session = get_object_or_404(AttendanceSession, pk=data['session_id'], status='active', mode='qr')
            
            with transaction.atomic():
                existing_fp = WebGLFingerprint.objects.filter(session=session, webgl_hash=webgl_hash).exclude(student=student).first()
                if existing_fp:
                    ProxyLog.objects.create(
                        session=session, attempted_by_student=student,
                        conflicting_student=existing_fp.student, webgl_hash=webgl_hash, reason='device_conflict'
                    )
                    messages.error(request, "Multiple attendance attempts detected from this device. Flagged as proxy.")
                    return redirect('student_dashboard')

                # Geofencing Check
                distance = None
                if session.is_geofenced:
                    g_lat = SystemConfig.get('geofence_lat')
                    g_lng = SystemConfig.get('geofence_lng')
                    
                    if not g_lat or not g_lng:
                        # Fallback: if is_geofenced is True but no global coords, skip check or log error
                        pass
                    else:
                        if not lat or not lng:
                            ProxyLog.objects.create(
                                session=session, attempted_by_student=student,
                                webgl_hash=webgl_hash, reason='location_denied'
                            )
                            messages.error(request, "Location verification required. Please enable GPS.")
                            return redirect('student_dashboard')
                        
                        distance = haversine_distance(g_lat, g_lng, lat, lng)
                        radius = int(SystemConfig.get("geofence_radius", 100))
                        
                        if distance > radius:
                            ProxyLog.objects.create(
                                session=session, attempted_by_student=student,
                                webgl_hash=webgl_hash, reason='location_mismatch',
                                attempted_lat=lat, attempted_lng=lng
                            )
                            messages.error(request, f"Location mismatch! You are {int(distance)}m away from the allowed area.")
                            return redirect('student_dashboard')

                WebGLFingerprint.objects.update_or_create(session=session, student=student, defaults={'webgl_hash': webgl_hash})
                record = get_object_or_404(AttendanceRecord, session=session, student=student)
                if record.status != 'present':
                    record.status = 'present'
                    record.marked_by = 'qr'
                    record.marked_at = timezone.now()
                    record.lat = lat
                    record.lng = lng
                    record.distance = distance
                    record.save()
                    messages.success(request, f"Attendance marked for {session.subject.name}!")
                else:
                    messages.info(request, "Your attendance is already marked.")

        except (signing.SignatureExpired, signing.BadSignature):
            messages.error(request, "Session timed out. Please scan the current QR code.")
            
        return redirect('student_dashboard')

@method_decorator(student_required, name='dispatch')
class AttendanceHistoryView(ListView):
    model = AttendanceRecord
    template_name = 'student/history.html'
    context_object_name = 'records'

    def get_queryset(self):
        return AttendanceRecord.objects.filter(student=self.request.user.student_profile).order_by('-session__date')

@method_decorator(student_required, name='dispatch')
class AjaxMarkAttendanceView(View):
    def post(self, request):
        token = request.POST.get('token')
        webgl_hash = request.POST.get('webgl_hash')
        lat = request.POST.get('latitude')
        lng = request.POST.get('longitude')
        student = request.user.student_profile
        
        if not token or not webgl_hash:
            return JsonResponse({'success': False, 'message': 'Missing token or fingerprint'}, status=400)

        try:
            max_age = int(SystemConfig.get("qr_rotation_interval", 30)) + 60
            data = verify_token(token, max_age)
            session = get_object_or_404(AttendanceSession, pk=data['session_id'], status='active', mode='qr')
            
            with transaction.atomic():
                existing_fp = WebGLFingerprint.objects.filter(session=session, webgl_hash=webgl_hash).exclude(student=student).first()
                if existing_fp:
                    ProxyLog.objects.create(
                        session=session, attempted_by_student=student,
                        conflicting_student=existing_fp.student, webgl_hash=webgl_hash, reason='device_conflict'
                    )
                    return JsonResponse({'success': False, 'message': 'Proxy attempt detected! device conflict.'}, status=403)

                # Geofencing Check
                distance = None
                if session.is_geofenced:
                    g_lat = SystemConfig.get('geofence_lat')
                    g_lng = SystemConfig.get('geofence_lng')

                    if g_lat and g_lng:
                        if not lat or not lng:
                            ProxyLog.objects.create(
                                session=session, attempted_by_student=student,
                                webgl_hash=webgl_hash, reason='location_denied'
                            )
                            return JsonResponse({'success': False, 'message': 'Location verification required! Access denied.'}, status=403)
                        
                        distance = haversine_distance(g_lat, g_lng, lat, lng)
                        radius = int(SystemConfig.get("geofence_radius", 100))
                        
                        if distance > radius:
                            ProxyLog.objects.create(
                                session=session, attempted_by_student=student,
                                webgl_hash=webgl_hash, reason='location_mismatch',
                                attempted_lat=lat, attempted_lng=lng
                            )
                            return JsonResponse({'success': False, 'message': f'Location mismatch! You are too far ({int(distance)}m).'}, status=403)

                WebGLFingerprint.objects.update_or_create(session=session, student=student, defaults={'webgl_hash': webgl_hash})
                record = get_object_or_404(AttendanceRecord, session=session, student=student)
                if record.status == 'present':
                    return JsonResponse({'success': True, 'message': 'Attendance already marked.'})
                
                record.status = 'present'
                record.marked_by = 'qr'
                record.marked_at = timezone.now()
                record.lat = lat
                record.lng = lng
                record.distance = distance
                record.save()
                return JsonResponse({'success': True, 'message': f'Attendance marked for {session.subject.name}!'})

        except (signing.SignatureExpired, signing.BadSignature):
            return JsonResponse({'success': False, 'message': 'QR Code expired or invalid.'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

@method_decorator(student_required, name='dispatch')
class StudentSubjectDetailView(TemplateView):
    template_name = 'student/subject_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.request.user.student_profile
        subject = get_object_or_404(student.department.subjects, pk=self.kwargs['subject_id'])
        records = AttendanceRecord.objects.filter(student=student, session__subject=subject).select_related('session__teacher__user').order_by('-session__date', '-session__created_at')
        total = records.count()
        present = records.filter(status='present').count()
        context.update({
            'subject': subject,
            'records': records,
            'stats': {
                'total': total,
                'present': present,
                'absent': total - present,
                'percent': round((present / total * 100), 1) if total > 0 else 0
            }
        })
        return context
