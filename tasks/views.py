from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Case, IntegerField, Value, When
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.utils import timezone
from django.views import View

from core.models import SystemActivityLog, Task, UserProfile

from .forms import TaskForm


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


class TaskQuerySetMixin:
    def get_task_queryset(self, organization):
        return (
            Task.objects.filter(organization=organization)
            .select_related("assigned_to__profile", "assigned_to__profile__organization")
            .annotate(
                priority_rank=Case(
                    When(priority=Task.Priority.HIGH, then=Value(3)),
                    When(priority=Task.Priority.MEDIUM, then=Value(2)),
                    When(priority=Task.Priority.LOW, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            )
            .order_by("-priority_rank", "due_date", "-created_at")
        )


class TaskListView(WorkspaceContextMixin, TaskQuerySetMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        organization = self.get_organization()
        if organization is None:
            return self.render_session_error()

        tasks = list(self.get_task_queryset(organization))
        form = TaskForm(organization=organization)
        context = {
            "tasks": tasks,
            "form": form,
            "organization": organization,
            "shell_organization": organization,
        }
        if self.is_htmx():
            return render(request, "tasks/task_list.html", context)
        return render(request, "tasks/task_page.html", context)


class TaskCreateView(WorkspaceContextMixin, View):
    def post(self, request: HttpRequest) -> HttpResponse:
        organization = self.get_organization()
        if organization is None:
            return self.render_session_error()

        form = TaskForm(request.POST, organization=organization)
        if not form.is_valid():
            response = render(
                request,
                "tasks/partials/task_form.html",
                {"form": form},
                status=422,
            )
            response["HX-Retarget"] = "#task-create-form"
            response["HX-Reswap"] = "outerHTML"
            return response

        task = form.save(commit=False)
        task.organization = organization
        task.save()
        task = (
            Task.objects.filter(pk=task.pk, organization=organization)
            .select_related("assigned_to__profile", "assigned_to__profile__organization")
            .get()
        )
        SystemActivityLog.objects.create(
            organization=organization,
            actor=request.user,
            description=f"{request.user.username} created task '{task.title}'.",
        )
        return render(
            request,
            "tasks/partials/task_create_success.html",
            {"task": task, "message": f"Task '{task.title}' created."},
            status=201,
        )


class TaskToggleCompleteView(WorkspaceContextMixin, View):
    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        organization = self.get_organization()
        if organization is None:
            return self.render_session_error()

        task = self._get_task(pk, organization)
        if task.status == Task.Status.COMPLETED:
            task.status = Task.Status.TODO
            task.completed_at = None
            activity_description = f"{request.user.username} reopened task '{task.title}'."
        else:
            task.status = Task.Status.COMPLETED
            task.completed_at = timezone.now()
            activity_description = f"{request.user.username} marked task '{task.title}' as completed."
        task.save(update_fields=["status", "completed_at"])
        SystemActivityLog.objects.create(
            organization=organization,
            actor=request.user,
            description=activity_description,
        )
        task = self._get_task(pk, organization)
        return render(request, "tasks/partials/task_card.html", {"task": task})

    def _get_task(self, pk: int, organization) -> Task:
        try:
            return Task.objects.filter(organization=organization).select_related(
                "assigned_to__profile", "assigned_to__profile__organization"
            ).get(pk=pk)
        except Task.DoesNotExist as exc:
            raise Http404("Task not found in this workspace.") from exc


class TaskStatusUpdateView(WorkspaceContextMixin, View):
    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        organization = self.get_organization()
        if organization is None:
            return self.render_session_error()

        status = request.POST.get("status")
        valid_statuses = {choice[0] for choice in Task.Status.choices}
        if status not in valid_statuses:
            return HttpResponseBadRequest("Invalid task status.")

        task = self._get_task(pk, organization)
        previous_status = task.get_status_display()
        task.status = status
        task.completed_at = timezone.now() if status == Task.Status.COMPLETED else None
        task.save(update_fields=["status", "completed_at"])
        task = self._get_task(pk, organization)
        SystemActivityLog.objects.create(
            organization=organization,
            actor=request.user,
            description=(
                f"{request.user.username} changed task '{task.title}' "
                f"from {previous_status} to {task.get_status_display()}."
            ),
        )
        return render(request, "tasks/partials/task_card.html", {"task": task})

    def _get_task(self, pk: int, organization) -> Task:
        try:
            return Task.objects.filter(organization=organization).select_related(
                "assigned_to__profile", "assigned_to__profile__organization"
            ).get(pk=pk)
        except Task.DoesNotExist as exc:
            raise Http404("Task not found in this workspace.") from exc
