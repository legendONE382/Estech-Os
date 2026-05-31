from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.models import Lead, Organization, SystemActivityLog, Task, UserProfile, WorkflowRule


class LeadAutomationTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="StrongPass123!")
        self.other_user = User.objects.create_user(username="outsider", password="StrongPass123!")
        self.organization = Organization.objects.create(name="Acme", slug="acme", owner=self.owner)
        self.other_organization = Organization.objects.create(name="Other", slug="other", owner=self.other_user)
        UserProfile.objects.create(user=self.owner, organization=self.organization, role=UserProfile.Role.ADMIN)
        UserProfile.objects.create(user=self.other_user, organization=self.other_organization, role=UserProfile.Role.ADMIN)

    def test_create_lead_triggers_active_workflow_task_inside_tenant(self):
        self.client.force_login(self.owner)
        WorkflowRule.objects.create(
            organization=self.organization,
            name="New lead follow-up",
            trigger="lead_created",
            action="assign_member",
            is_active=True,
        )

        response = self.client.post(
            reverse("leads:create"),
            {
                "name": "Avery Johnson",
                "company_name": "Northstar Studio",
                "email": "avery@example.com",
                "phone": "+15550142",
                "status": Lead.Status.NEW,
                "notes": "Interested in managed operations.",
            },
            HTTP_HX_REQUEST="true",
        )

        lead = Lead.objects.get(name="Avery Johnson")
        task = Task.objects.get(title="Follow up with new lead: Avery Johnson")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(lead.organization, self.organization)
        self.assertEqual(task.organization, self.organization)
        self.assertEqual(task.assigned_to, self.owner)
        self.assertIn(f'id="lead-{lead.id}"', response.content.decode())
        self.assertTrue(
            SystemActivityLog.objects.filter(
                organization=self.organization,
                description__contains="Automation 'New lead follow-up' created task",
            ).exists()
        )

    def test_status_update_blocks_cross_tenant_lead(self):
        self.client.force_login(self.owner)
        other_lead = Lead.objects.create(
            organization=self.other_organization,
            name="Other Lead",
            company_name="Other Co",
            email="other@example.com",
            phone="+15550143",
            status=Lead.Status.NEW,
            notes="Isolated.",
        )

        response = self.client.post(
            reverse("leads:update_status", args=[other_lead.pk]),
            {"status": Lead.Status.CONVERTED},
            HTTP_HX_REQUEST="true",
        )

        other_lead.refresh_from_db()
        self.assertEqual(response.status_code, 404)
        self.assertEqual(other_lead.status, Lead.Status.NEW)
