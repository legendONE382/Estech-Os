from django.contrib.auth import views as auth_views
from django.urls import include, path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("tasks/", include("tasks.urls")),
    path("leads/", include("leads.urls")),
    path("automated-rules/", include("automation.urls")),
    path("reports/", include("reports.urls")),
    path("settings/", views.settings, name="settings"),
    path("register/", views.register, name="register"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="core/registration/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
