from __future__ import annotations

import os
from datetime import timedelta
from typing import Any

import requests
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import render
from django.utils import timezone

from core.models import Lead, Organization, Task, UserProfile

MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
MISTRAL_TIMEOUT_SECONDS = 3.5
MISTRAL_MODEL = "mistral-7b-chat"


def _is_htmx(request) -> bool:
    return request.headers.get("HX-Request") == "true" or request.META.get("HTTP_HX_REQUEST") == "true"


def _workspace_profile(request) -> UserProfile | None:
    try:
        return UserProfile.objects.select_related("organization", "user").get(user=request.user)
    except UserProfile.DoesNotExist:
        return None


def _build_mistral_summary(organization_name: str, stats: dict[str, int]) -> str | None:
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        return None

    content = (
        "Create a concise report summary for a B2B operations dashboard. "
        "Use a premium neon-glass tone and keep the message short. "
        f"Organization: {organization_name}. "
        f"New leads: {stats['new_leads']}. "
        f"Tasks completed this week: {stats['completed_tasks']}. "
        f"Overdue tasks: {stats['overdue_tasks']}."
    )

    payload = {
        "model": MISTRAL_MODEL,
        "messages": [
            {"role": "user", "content": content},
        ],
        "temperature": 0.3,
    }

    try:
        response = requests.post(
            MISTRAL_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=MISTRAL_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
        return (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content")
        )
    except requests.RequestException:
        return None


@login_required
def report_list(request):
    profile = _workspace_profile(request)
    if profile is None:
        return render(request, "workspace/session_error.html", status=409)

    organization = profile.organization
    today = timezone.localdate()
    week_start = timezone.now() - timedelta(days=7)

    new_leads = Lead.objects.filter(organization=organization, status=Lead.Status.NEW).count()
    completed_tasks = Task.objects.filter(
        organization=organization,
        status=Task.Status.COMPLETED,
        completed_at__gte=week_start,
    ).count()
    overdue_tasks = Task.objects.filter(
        organization=organization,
        due_date__lt=today,
    ).exclude(status=Task.Status.COMPLETED).count()

    report_summary = _build_mistral_summary(
        organization.name,
        {
            "new_leads": new_leads,
            "completed_tasks": completed_tasks,
            "overdue_tasks": overdue_tasks,
        },
    )

    context: dict[str, Any] = {
        "shell_organization": organization,
        "eyebrow": "Business intelligence",
        "title": "Reports",
        "description": "A tenant-scoped briefing of leads and task execution delivered with a premium operational tone.",
        "cards": [
            {
                "label": "New leads",
                "value": new_leads,
                "description": "Fresh opportunities newly added to this organization.",
            },
            {
                "label": "Completed tasks",
                "value": completed_tasks,
                "description": "Work items closed in the last seven days.",
            },
            {
                "label": "Overdue items",
                "value": overdue_tasks,
                "description": "Active tasks that are past due and still open.",
            },
        ],
        "report_summary": report_summary,
    }

    if _is_htmx(request):
        return render(request, "reports/report_panel.html", context)

    return render(request, "reports/report_list.html", context)
