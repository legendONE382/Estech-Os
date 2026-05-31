from django.urls import reverse

from .models import Lead, Task, UserProfile, WorkflowRule


def workspace_navigation(request):
    nav_counts = {"new_leads": 0, "active_rules": 0, "open_tasks": 0}
    if request.user.is_authenticated:
        try:
            profile = UserProfile.objects.select_related("organization").get(user=request.user)
            organization = profile.organization
            nav_counts = {
                "new_leads": Lead.objects.filter(organization=organization, status=Lead.Status.NEW).count(),
                "active_rules": WorkflowRule.objects.filter(organization=organization, is_active=True).count(),
                "open_tasks": Task.objects.filter(organization=organization).exclude(status=Task.Status.COMPLETED).count(),
            }
        except UserProfile.DoesNotExist:
            nav_counts = {"new_leads": 0, "active_rules": 0, "open_tasks": 0}

    return {
        "dashboard_url": reverse("dashboard"),
        "tasks_url": reverse("tasks:list"),
        "leads_url": reverse("leads:list"),
        "rules_url": reverse("automation:list"),
        "reports_url": reverse("reports"),
        "settings_url": reverse("settings"),
        "nav_counts": nav_counts,
    }
