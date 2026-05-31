from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views import View

from automation.engine import execute_workflows
from core.models import Lead, SystemActivityLog, Task, UserProfile, WorkflowRule

from .forms import LeadForm


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


class LeadListView(WorkspaceContextMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        organization = self.get_organization()
        if organization is None:
            return self.render_session_error()

        leads = list(Lead.objects.filter(organization=organization).order_by("-created_at", "name"))
        context = {
            "leads": leads,
            "form": LeadForm(),
            "organization": organization,
            "shell_organization": organization,
        }
        if self.is_htmx():
            return render(request, "leads/lead_list.html", context)
        return render(request, "leads/lead_page.html", context)


class LeadCreateView(WorkspaceContextMixin, View):
    def post(self, request: HttpRequest) -> HttpResponse:
        organization = self.get_organization()
        if organization is None:
            return self.render_session_error()

        form = LeadForm(request.POST)
        if not form.is_valid():
            response = render(request, "leads/partials/lead_form.html", {"form": form}, status=422)
            response["HX-Retarget"] = "#lead-create-form"
            response["HX-Reswap"] = "outerHTML"
            return response

        lead = form.save(commit=False)
        lead.organization = organization
        lead.save()
        SystemActivityLog.objects.create(
            organization=organization,
            actor=request.user,
            description=f"{request.user.username} created lead '{lead.name}' for {lead.company_name}.",
        )
        workflow_results = execute_workflows(organization, "lead_created", lead, actor=request.user)
        message = f"Lead '{lead.name}' created."
        if workflow_results:
            message = f"Lead '{lead.name}' created and {len(workflow_results)} automation rule executed."
        context = {
            "lead": lead,
            "message": message,
            "nav_counts": self.nav_counts(organization),
        }
        return render(request, "leads/partials/lead_create_success.html", context, status=201)


class LeadStatusUpdateView(WorkspaceContextMixin, View):
    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        organization = self.get_organization()
        if organization is None:
            return self.render_session_error()

        status = request.POST.get("status")
        valid_statuses = {choice[0] for choice in Lead.Status.choices}
        if status not in valid_statuses:
            return HttpResponseBadRequest("Invalid lead status.")

        lead = self._get_lead(pk, organization)
        previous_status = lead.get_status_display()
        lead.status = status
        lead.save(update_fields=["status", "updated_at"])
        lead = self._get_lead(pk, organization)
        SystemActivityLog.objects.create(
            organization=organization,
            actor=request.user,
            description=(
                f"{request.user.username} moved lead '{lead.name}' "
                f"from {previous_status} to {lead.get_status_display()}."
            ),
        )
        execute_workflows(organization, "lead_status_updated", lead, actor=request.user)
        return render(
            request,
            "leads/partials/lead_status_update.html",
            {
                "lead": lead,
                "message": f"Lead '{lead.name}' moved to {lead.get_status_display()}.",
                "nav_counts": self.nav_counts(organization),
            },
        )

    def _get_lead(self, pk: int, organization) -> Lead:
        try:
            return Lead.objects.filter(organization=organization).get(pk=pk)
        except Lead.DoesNotExist as exc:
            raise Http404("Lead not found in this workspace.") from exc
