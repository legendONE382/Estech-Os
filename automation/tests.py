from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from automation.engine import execute_workflows
from core.models import Lead, Organization, Task, UserProfile, WorkflowRule


class AutomationEngineTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="StrongPass123!")
        self.organization = Organization.objects.create(name="Acme", slug="acme", owner=self.owner)
        UserProfile.objects.create(user=self.owner, organization=self.organization, role=UserProfile.Role.ADMIN)
        self.lead = Lead.objects.create(
            organization=self.organization,
            name="Avery Johnson",
            company_name="Northstar Studio",
            email="avery@example.com",
            phone="+15550142",
            status=Lead.Status.NEW,
            notes="Interested in managed operations.",
        )

    def test_rule_create_scopes_to_current_organization(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("automation:create"),
            {
                "name": "New lead follow-up",
                "trigger": "lead_created",
                "action": "assign_member",
                "is_active": "on",
            },
            HTTP_HX_REQUEST="true",
        )

        rule = WorkflowRule.objects.get(name="New lead follow-up")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(rule.organization, self.organization)
        self.assertEqual(rule.trigger, "lead_created")
        self.assertEqual(rule.action, "assign_member")

    def test_engine_creates_follow_up_task_for_matching_rule(self):
        WorkflowRule.objects.create(
            organization=self.organization,
            name="New lead follow-up",
            trigger="lead_created",
            action="assign_member",
            is_active=True,
        )

        results = execute_workflows(self.organization, "lead_created", self.lead, actor=self.owner)

        self.assertEqual(len(results), 1)
        task = Task.objects.get(title="Follow up with new lead: Avery Johnson")
        self.assertEqual(task.organization, self.organization)
        self.assertEqual(task.assigned_to, self.owner)
