from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import redirect, render
from django.utils import timezone

from .forms import RegistrationForm
from .models import Lead, Organization, SystemActivityLog, Task, UserProfile, WorkflowRule


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome to Estech OS. Your workspace is ready.")
            return redirect("dashboard")
    else:
        form = RegistrationForm()

    return render(request, "core/registration/register.html", {"form": form})


def _is_htmx(request) -> bool:
    return request.headers.get("HX-Request") == "true" or request.META.get("HTTP_HX_REQUEST") == "true"


def _workspace_profile(request) -> UserProfile | None:
    try:
        return UserProfile.objects.select_related("organization", "user").get(user=request.user)
    except UserProfile.DoesNotExist:
        return None


def _render_workspace(request, template_name: str, fragment_name: str, context: dict[str, Any]):
    if _is_htmx(request):
        return render(request, fragment_name, context)
    return render(request, template_name, context)


def _render_session_error(request):
    if _is_htmx(request):
        return render(request, "workspace/session_error_fragment.html", status=409)
    return render(request, "workspace/session_error.html", status=409)


def _metric(label: str, value: int, badge: str, description: str, tone: str) -> dict[str, str | int]:
    tones = {
        "emerald": {
            "badge_bg": "bg-emerald-400/10",
            "badge_border": "border-emerald-400/20",
            "badge_text": "text-emerald-300",
        },
        "cyan": {
            "badge_bg": "bg-cyan-400/10",
            "badge_border": "border-cyan-400/20",
            "badge_text": "text-cyan-300",
        },
        "red": {
            "badge_bg": "bg-red-400/10",
            "badge_border": "border-red-400/20",
            "badge_text": "text-red-300",
        },
        "indigo": {
            "badge_bg": "bg-indigo-400/10",
            "badge_border": "border-indigo-400/20",
            "badge_text": "text-indigo-300",
        },
    }
    return {
        "label": label,
        "value": value,
        "badge": badge,
        "description": description,
        **tones[tone],
    }


@login_required
def dashboard(request):
    profile = _workspace_profile(request)
    if profile is None:
        return _render_session_error(request)

    organization = profile.organization
    today = timezone.localdate()
    week_start = timezone.now() - timedelta(days=7)

    task_stats = Task.objects.filter(organization=organization).aggregate(
        pending_assigned=Count(
            "id",
            filter=Q(assigned_to=request.user) & ~Q(status=Task.Status.COMPLETED),
        ),
        overdue=Count(
            "id",
            filter=Q(due_date__lt=today) & ~Q(status=Task.Status.COMPLETED),
        ),
        completed_week=Count(
            "id",
            filter=Q(status=Task.Status.COMPLETED, completed_at__gte=week_start),
        ),
    )
    new_leads = Lead.objects.filter(organization=organization, status=Lead.Status.NEW).count()
    activity_logs = list(
        SystemActivityLog.objects.filter(organization=organization)
        .select_related("actor")
        .order_by("-created_at")[:10]
    )

    context = {
        "profile": profile,
        "organization": organization,
        "shell_organization": organization,
        "metrics": [
            _metric(
                "New Leads",
                new_leads,
                "Intake",
                "Fresh inbound opportunities waiting for first contact.",
                "emerald",
            ),
            _metric(
                "Pending Tasks",
                task_stats["pending_assigned"] or 0,
                "Assigned",
                "Open work assigned to you and not yet completed.",
                "cyan",
            ),
            _metric(
                "Overdue Critical Items",
                task_stats["overdue"] or 0,
                "Risk",
                "Organization tasks past due and still active.",
                "red",
            ),
            _metric(
                "Weekly Performance",
                task_stats["completed_week"] or 0,
                "Closed",
                "Tasks completed in the last seven days.",
                "indigo",
            ),
        ],
        "activity_logs": activity_logs,
    }
    return _render_workspace(request, "core/dashboard.html", "dashboard/index.html", context)


def _module_card(label: str, value: int | str, description: str) -> dict[str, int | str]:
    return {"label": label, "value": value, "description": description}


@login_required
def tasks(request):
    profile = _workspace_profile(request)
    if profile is None:
        return _render_session_error(request)

    organization = profile.organization
    today = timezone.localdate()
    stats = Task.objects.filter(organization=organization).aggregate(
        total=Count("id"),
        assigned_open=Count("id", filter=Q(assigned_to=request.user) & ~Q(status=Task.Status.COMPLETED)),
        overdue=Count("id", filter=Q(due_date__lt=today) & ~Q(status=Task.Status.COMPLETED)),
    )
    context = {
        "shell_organization": organization,
        "eyebrow": "Task command",
        "title": "Task workload",
        "description": "A tenant-scoped workload summary focused on open execution, ownership, and operational risk.",
        "cards": [
            _module_card("Total tasks", stats["total"] or 0, "All task records attached to this organization."),
            _module_card("Your open tasks", stats["assigned_open"] or 0, "Incomplete tasks currently assigned to you."),
            _module_card("Overdue tasks", stats["overdue"] or 0, "Active tasks past their due date."),
        ],
    }
    return _render_workspace(request, "workspace/module_page.html", "workspace/module.html", context)


@login_required
def leads(request):
    profile = _workspace_profile(request)
    if profile is None:
        return _render_session_error(request)

    organization = profile.organization
    stats = Lead.objects.filter(organization=organization).aggregate(
        total=Count("id"),
        new=Count("id", filter=Q(status=Lead.Status.NEW)),
        qualified=Count("id", filter=Q(status=Lead.Status.QUALIFIED)),
    )
    context = {
        "shell_organization": organization,
        "eyebrow": "Revenue intake",
        "title": "Lead pipeline",
        "description": "A secure organization-level view of incoming opportunities and qualification momentum.",
        "cards": [
            _module_card("Total leads", stats["total"] or 0, "Every lead record isolated to this tenant."),
            _module_card("New leads", stats["new"] or 0, "Fresh contacts waiting for first action."),
            _module_card("Qualified leads", stats["qualified"] or 0, "Opportunities validated for follow-up."),
        ],
    }
    return _render_workspace(request, "workspace/module_page.html", "workspace/module.html", context)


@login_required
def automated_rules(request):
    profile = _workspace_profile(request)
    if profile is None:
        return _render_session_error(request)

    organization = profile.organization
    stats = WorkflowRule.objects.filter(organization=organization).aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(is_active=True)),
        paused=Count("id", filter=Q(is_active=False)),
    )
    context = {
        "shell_organization": organization,
        "eyebrow": "Automation control",
        "title": "Automated rules",
        "description": "A tenant-safe automation summary for the rules that will drive repeatable operating procedures.",
        "cards": [
            _module_card("Total rules", stats["total"] or 0, "All workflow rules configured for this organization."),
            _module_card("Active rules", stats["active"] or 0, "Rules currently allowed to execute."),
            _module_card("Paused rules", stats["paused"] or 0, "Rules preserved but not currently active."),
        ],
    }
    return _render_workspace(request, "workspace/module_page.html", "workspace/module.html", context)


@login_required
def reports(request):
    profile = _workspace_profile(request)
    if profile is None:
        return _render_session_error(request)

    organization = profile.organization
    week_start = timezone.now() - timedelta(days=7)
    lead_stats = Lead.objects.filter(organization=organization).aggregate(
        converted=Count("id", filter=Q(status=Lead.Status.CONVERTED)),
        lost=Count("id", filter=Q(status=Lead.Status.LOST)),
    )
    completed_week = Task.objects.filter(
        organization=organization,
        status=Task.Status.COMPLETED,
        completed_at__gte=week_start,
    ).count()
    context = {
        "shell_organization": organization,
        "eyebrow": "Business intelligence",
        "title": "Reports snapshot",
        "description": "A focused operational reporting surface built from tenant-filtered lead and task telemetry.",
        "cards": [
            _module_card("Converted leads", lead_stats["converted"] or 0, "Leads marked as converted in this workspace."),
            _module_card("Lost leads", lead_stats["lost"] or 0, "Leads marked as lost in this workspace."),
            _module_card("Tasks closed this week", completed_week, "Completed task throughput from the last seven days."),
        ],
    }
    return _render_workspace(request, "workspace/module_page.html", "workspace/module.html", context)


@login_required
def settings(request):
    profile = _workspace_profile(request)
    if profile is None:
        return _render_session_error(request)

    organization = Organization.objects.select_related("owner").get(pk=profile.organization_id)
    context = {
        "shell_organization": organization,
        "eyebrow": "Workspace settings",
        "title": "Organization profile",
        "description": "Core tenant identity and access context for this Estech OS workspace.",
        "cards": [
            _module_card("Organization", organization.name, "The legal or operating name for this tenant."),
            _module_card("Owner", organization.owner.username, "The user account that owns this workspace."),
            _module_card("Your role", profile.role, "Your current access level inside this organization."),
        ],
    }
    return _render_workspace(request, "workspace/module_page.html", "workspace/module.html", context)
