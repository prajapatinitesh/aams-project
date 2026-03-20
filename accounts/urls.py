from django.urls import path
from .views import AAMSLoginView, AAMSLogoutView, DashboardRedirectView, LandingPageView

urlpatterns = [
    path("",           LandingPageView.as_view(),           name="landing"),
    path("login/",     AAMSLoginView.as_view(),          name="login"),
    path("logout/",    AAMSLogoutView.as_view(),          name="logout"),
    path("dashboard/", DashboardRedirectView.as_view(), name="dashboard"),
]
