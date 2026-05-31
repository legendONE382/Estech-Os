from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("tasks/", views.tasks, name="tasks"),
    path("leads/", views.leads, name="leads"),
    path("automated-rules/", views.automated_rules, name="automated_rules"),
    path("reports/", views.reports, name="reports"),
    path("settings/", views.settings, name="settings"),
    path("register/", views.register, name="register"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="core/registration/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
