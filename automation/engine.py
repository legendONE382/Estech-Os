from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.utils import timezone

from core.models import Lead, SystemActivityLog, Task, WorkflowRule


def execute_workflows(organization, trigger_type: str, target_object: Any, actor=None) -> list[dict[str, str | int]]:
    rules = WorkflowRule.objects.filter(
        organization=organization,
        is_active=True,
        trigger=trigger_type,
    ).select_related("organization", "organization__owner")
    results: list[dict[str, str | int]] = []

    for rule in rules:
        if rule.action == "assign_member":
            task = _create_follow_up_task(organization, target_object, rule)
            SystemActivityLog.objects.create(
                organization=organization,
                actor=actor or organization.owner,
                description=(
                    f"Automation '{rule.name}' created task '{task.title}' "
                    f"from trigger '{rule.trigger}'."
                ),
            )
            results.append({"rule_id": rule.id, "action": rule.action, "task_id": task.id})
        else:
            SystemActivityLog.objects.create(
                organization=organization,
                actor=actor or organization.owner,
                description=f"Automation '{rule.name}' skipped unsupported action '{rule.action}'.",
            )
            results.append({"rule_id": rule.id, "action": rule.action, "status": "unsupported"})

    return results


def _create_follow_up_task(organization, target_object: Any, rule: WorkflowRule) -> Task:
    if isinstance(target_object, Lead):
        title = f"Follow up with new lead: {target_object.name}"
        description = (
            f"Automation rule '{rule.name}' generated this task for {target_object.name} "
            f"at {target_object.company_name}. Review the lead profile, contact them, and move the pipeline forward."
        )
    else:
        title = f"Follow up from automation: {rule.name}"
        description = f"Automation rule '{rule.name}' generated this task from a {rule.trigger} event."

    return Task.objects.create(
        organization=organization,
        title=title,
        description=description,
        priority=Task.Priority.MEDIUM,
        status=Task.Status.TODO,
        assigned_to=organization.owner,
        due_date=timezone.localdate() + timedelta(days=1),
    )
