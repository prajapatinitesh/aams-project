from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import RedirectView, TemplateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin

class DashboardRedirectView(LoginRequiredMixin, RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        role = self.request.user.role
        if role == 'admin':
            return reverse_lazy('admin_dashboard')
        elif role == 'teacher':
            return reverse_lazy('teacher_dashboard')
        elif role == 'student':
            return reverse_lazy('student_dashboard')
        return reverse_lazy('login')

class AAMSLoginView(LoginView):
    template_name = 'accounts/login.html'
    
    def get_success_url(self):
        return reverse_lazy('dashboard')

class AAMSLogoutView(LogoutView):
    next_page = reverse_lazy('login')

class LandingPageView(TemplateView):
    template_name = 'landing.html'
