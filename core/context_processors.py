from django.urls import reverse


def workspace_navigation(request):
    return {
        "dashboard_url": reverse("dashboard"),
        "tasks_url": reverse("tasks"),
        "leads_url": reverse("leads"),
        "rules_url": reverse("automated_rules"),
        "reports_url": reverse("reports"),
        "settings_url": reverse("settings"),
    }
