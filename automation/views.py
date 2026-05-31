from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views import View

from core.models import Lead, SystemActivityLog, Task, UserProfile, WorkflowRule

from .forms import ACTION_CHOICES, TRIGGER_CHOICES, WorkflowRuleForm


class WorkspaceContextMixin(LoginRequiredMixin):
    def is_htmx(self) -> bool:
        return self.request.headers.get("HX-Request") == "true" or self.request.META.get("HTTP_HX_REQUEST") == "true"

    def get_profile(self) -> UserProfile | None:
        if not hasattr(self, "_workspace_profile"):
            try:
                self._workspace_profile = UserProfile.objects.select_related("organization", "user").get(
                    user=self.request.user
                )
            except UserProfile.DoesNotExist:
                self._workspace_profile = None
        return self._workspace_profile

    def get_organization(self):
        profile = self.get_profile()
        return profile.organization if profile else None

    def render_session_error(self) -> HttpResponse:
        if self.is_htmx():
            return render(self.request, "workspace/session_error_fragment.html", status=409)
        return render(self.request, "workspace/session_error.html", status=409)

    def nav_counts(self, organization) -> dict[str, int]:
        return {
            "new_leads": Lead.objects.filter(organization=organization, status=Lead.Status.NEW).count(),
            "active_rules": WorkflowRule.objects.filter(organization=organization, is_active=True).count(),
            "open_tasks": Task.objects.filter(organization=organization).exclude(status=Task.Status.COMPLETED).count(),
        }


class WorkflowRuleListView(WorkspaceContextMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        organization = self.get_organization()
        if organization is None:
            return self.render_session_error()

        rules = list(WorkflowRule.objects.filter(organization=organization).order_by("-is_active", "name"))
        context = {
            "rules": rules,
            "form": WorkflowRuleForm(),
            "organization": organization,
            "shell_organization": organization,
            "trigger_labels": dict(TRIGGER_CHOICES),
            "action_labels": dict(ACTION_CHOICES),
        }
        if self.is_htmx():
            return render(request, "automation/rule_list.html", context)
        return render(request, "automation/rule_page.html", context)


class WorkflowRuleCreateView(WorkspaceContextMixin, View):
    def post(self, request: HttpRequest) -> HttpResponse:
        organization = self.get_organization()
        if organization is None:
            return self.render_session_error()

        form = WorkflowRuleForm(request.POST)
        if not form.is_valid():
            response = render(request, "automation/partials/rule_form.html", {"form": form}, status=422)
            response["HX-Retarget"] = "#rule-create-form"
            response["HX-Reswap"] = "outerHTML"
            return response

        rule = form.save(commit=False)
        rule.organization = organization
        rule.save()
        SystemActivityLog.objects.create(
            organization=organization,
            actor=request.user,
            description=f"{request.user.username} created automation rule '{rule.name}'.",
        )
        context = {
            "rule": rule,
            "message": f"Automation rule '{rule.name}' created.",
            "trigger_labels": dict(TRIGGER_CHOICES),
            "action_labels": dict(ACTION_CHOICES),
            "nav_counts": self.nav_counts(organization),
        }
        return render(request, "automation/partials/rule_create_success.html", context, status=201)
