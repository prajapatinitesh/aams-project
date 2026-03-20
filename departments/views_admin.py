from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView, View
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.contrib import messages
from accounts.decorators import admin_required
from accounts.models import User, SystemConfig
from .models import Department, Subject, TeacherProfile, StudentProfile

@method_decorator(admin_required, name='dispatch')
class AdminDashboardView(TemplateView):
    template_name = 'admin_panel/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['counts'] = {
            'departments': Department.objects.count(),
            'subjects': Subject.objects.count(),
            'teachers': TeacherProfile.objects.count(),
            'students': StudentProfile.objects.count(),
        }
        return context

# --- Department Views ---

@method_decorator(admin_required, name='dispatch')
class DepartmentListView(ListView):
    model = Department
    template_name = 'admin_panel/dept_list.html'
    context_object_name = 'departments'

@method_decorator(admin_required, name='dispatch')
class DepartmentCreateView(CreateView):
    model = Department
    fields = ['name']
    template_name = 'admin_panel/dept_form.html'
    success_url = reverse_lazy('dept_list')

@method_decorator(admin_required, name='dispatch')
class DepartmentEditView(UpdateView):
    model = Department
    fields = ['name']
    template_name = 'admin_panel/dept_form.html'
    success_url = reverse_lazy('dept_list')

@method_decorator(admin_required, name='dispatch')
class DepartmentDeleteView(DeleteView):
    model = Department
    template_name = 'admin_panel/dept_confirm_delete.html'
    success_url = reverse_lazy('dept_list')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.subjects.exists():
            messages.error(request, "Cannot delete: subjects are linked to this department.")
            return redirect('dept_list')
        return super().post(request, *args, **kwargs)

# --- Subject Views ---

@method_decorator(admin_required, name='dispatch')
class SubjectListView(ListView):
    model = Subject
    template_name = 'admin_panel/subject_list.html'
    context_object_name = 'subjects'

@method_decorator(admin_required, name='dispatch')
class SubjectCreateView(CreateView):
    model = Subject
    fields = ['name', 'department', 'semester']
    template_name = 'admin_panel/subject_form.html'
    success_url = reverse_lazy('subject_list')

@method_decorator(admin_required, name='dispatch')
class SubjectEditView(UpdateView):
    model = Subject
    fields = ['name', 'department', 'semester']
    template_name = 'admin_panel/subject_form.html'
    success_url = reverse_lazy('subject_list')

@method_decorator(admin_required, name='dispatch')
class SubjectDeleteView(DeleteView):
    model = Subject
    template_name = 'admin_panel/subject_confirm_delete.html'
    success_url = reverse_lazy('subject_list')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.sessions.exists():
            messages.error(request, "Cannot delete: attendance sessions are linked to this subject.")
            return redirect('subject_list')
        return super().post(request, *args, **kwargs)

@method_decorator(admin_required, name='dispatch')
class AssignTeachersView(TemplateView):
    template_name = 'admin_panel/subject_assign_teachers.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        subject = get_object_or_404(Subject, pk=self.kwargs['pk'])
        context['subject'] = subject
        context['teachers'] = TeacherProfile.objects.all()
        context['assigned_teacher_ids'] = subject.teachers.values_list('id', flat=True)
        return context

    def post(self, request, pk):
        subject = get_object_or_404(Subject, pk=pk)
        teacher_ids = request.POST.getlist('teachers')
        subject.teachers.set(teacher_ids)
        messages.success(request, "Teachers assigned successfully.")
        return redirect('subject_list')

# --- Teacher Views ---

@method_decorator(admin_required, name='dispatch')
class TeacherListView(ListView):
    model = TeacherProfile
    template_name = 'admin_panel/teacher_list.html'
    context_object_name = 'teachers'

@method_decorator(admin_required, name='dispatch')
class TeacherCreateView(View):
    def get(self, request):
        departments = Department.objects.all()
        return render(request, 'admin_panel/teacher_form.html', {'departments': departments})

    def post(self, request):
        email = request.POST.get('email')
        full_name = request.POST.get('full_name')
        password = request.POST.get('password')
        dept_id = request.POST.get('department')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "User with this email already exists.")
            return self.get(request)

        user = User.objects.create_user(
            email=email,
            password=password,
            full_name=full_name,
            role='teacher',
            is_staff=True
        )
        dept = get_object_or_404(Department, pk=dept_id) if dept_id else None
        TeacherProfile.objects.create(user=user, department=dept)
        messages.success(request, "Teacher account created successfully.")
        return redirect('teacher_list')
@method_decorator(admin_required, name='dispatch')
class TeacherEditView(View):
    def get(self, request, pk):
        profile = get_object_or_404(TeacherProfile, pk=pk)
        departments = Department.objects.all()
        return render(request, 'admin_panel/teacher_form.html', {
            'profile': profile,
            'departments': departments
        })

    def post(self, request, pk):
        profile = get_object_or_404(TeacherProfile, pk=pk)
        profile.user.full_name = request.POST.get('full_name')
        profile.user.email = request.POST.get('email')
        dept_id = request.POST.get('department')
        profile.department = get_object_or_404(Department, pk=dept_id) if dept_id else None
        
        password = request.POST.get('password')
        if password:
            profile.user.set_password(password)
        
        profile.user.save()
        profile.save()
        messages.success(request, "Teacher account updated.")
        return redirect('teacher_list')

@method_decorator(admin_required, name='dispatch')
class TeacherDeactivateView(View):
    def post(self, request, pk):
        profile = get_object_or_404(TeacherProfile, pk=pk)
        profile.user.is_active = not profile.user.is_active
        profile.user.save()
        status = "activated" if profile.user.is_active else "deactivated"
        messages.success(request, f"Teacher account {status}.")
        return redirect('teacher_list')

# --- Student Views ---

@method_decorator(admin_required, name='dispatch')
class StudentListView(ListView):
    model = StudentProfile
    template_name = 'admin_panel/student_list.html'
    context_object_name = 'students'

@method_decorator(admin_required, name='dispatch')
class StudentCreateView(View):
    def get(self, request):
        departments = Department.objects.all()
        return render(request, 'admin_panel/student_form.html', {'departments': departments})

    def post(self, request):
        email = request.POST.get('email')
        full_name = request.POST.get('full_name')
        password = request.POST.get('password')
        dept_id = request.POST.get('department')
        semester = request.POST.get('semester')
        roll_number = request.POST.get('roll_number')

        if User.objects.filter(email=email).exists():
            messages.error(request, "User with this email already exists.")
            return self.get(request)

        user = User.objects.create_user(
            email=email,
            password=password,
            full_name=full_name,
            role='student'
        )
        dept = get_object_or_404(Department, pk=dept_id)
        StudentProfile.objects.create(
            user=user, 
            department=dept, 
            semester=semester, 
            roll_number=roll_number
        )
        messages.success(request, "Student account created.")
        return redirect('student_list')

@method_decorator(admin_required, name='dispatch')
class StudentEditView(View):
    def get(self, request, pk):
        profile = get_object_or_404(StudentProfile, pk=pk)
        departments = Department.objects.all()
        return render(request, 'admin_panel/student_form.html', {
            'profile': profile,
            'departments': departments
        })

    def post(self, request, pk):
        profile = get_object_or_404(StudentProfile, pk=pk)
        profile.user.full_name = request.POST.get('full_name')
        profile.user.email = request.POST.get('email')
        profile.department = get_object_or_404(Department, pk=request.POST.get('department'))
        profile.semester = request.POST.get('semester')
        profile.roll_number = request.POST.get('roll_number')
        
        password = request.POST.get('password')
        if password:
            profile.user.set_password(password)
            
        profile.user.save()
        profile.save()
        messages.success(request, "Student account updated.")
        return redirect('student_list')

@method_decorator(admin_required, name='dispatch')
class StudentDeactivateView(View):
    def post(self, request, pk):
        profile = get_object_or_404(StudentProfile, pk=pk)
        profile.user.is_active = not profile.user.is_active
        profile.user.save()
        status = "activated" if profile.user.is_active else "deactivated"
        messages.success(request, f"Student account {status}.")
        return redirect('student_list')

@method_decorator(admin_required, name='dispatch')
class SystemConfigView(View):
    def get(self, request):
        interval = SystemConfig.get("qr_rotation_interval", "30")
        return render(request, 'admin_panel/config.html', {'interval': interval})

    def post(self, request):
        interval = request.POST.get('interval')
        if interval and interval.isdigit():
            config, _ = SystemConfig.objects.get_or_create(key="qr_rotation_interval")
            config.value = interval
            config.save()
            messages.success(request, "System configuration updated.")
        else:
            messages.error(request, "Invalid interval value.")
        return redirect('system_config')
