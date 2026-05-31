from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.models import Organization, SystemActivityLog, Task, UserProfile
from tasks.forms import TaskForm


class TaskEngineTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="StrongPass123!")
        self.member = User.objects.create_user(username="member", password="StrongPass123!")
        self.other_user = User.objects.create_user(username="outsider", password="StrongPass123!")
        self.organization = Organization.objects.create(name="Acme", slug="acme", owner=self.owner)
        self.other_organization = Organization.objects.create(name="Other", slug="other", owner=self.other_user)
        UserProfile.objects.create(user=self.owner, organization=self.organization, role=UserProfile.Role.ADMIN)
        UserProfile.objects.create(user=self.member, organization=self.organization, role=UserProfile.Role.MEMBER)
        UserProfile.objects.create(user=self.other_user, organization=self.other_organization, role=UserProfile.Role.ADMIN)

    def test_task_form_limits_assignees_to_active_organization(self):
        form = TaskForm(organization=self.organization)

        self.assertIn(self.owner, form.fields["assigned_to"].queryset)
        self.assertIn(self.member, form.fields["assigned_to"].queryset)
        self.assertNotIn(self.other_user, form.fields["assigned_to"].queryset)

    def test_create_task_scopes_to_current_users_organization(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("tasks:create"),
            {
                "title": "Review invoice",
                "description": "Validate the client invoice before approval.",
                "priority": Task.Priority.HIGH,
                "status": Task.Status.TODO,
                "assigned_to": self.member.pk,
                "due_date": date.today().isoformat(),
            },
            HTTP_HX_REQUEST="true",
        )

        task = Task.objects.get(title="Review invoice")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(task.organization, self.organization)
        self.assertEqual(task.assigned_to, self.member)
        self.assertIn(f'id="task-{task.id}"', response.content.decode())
        self.assertTrue(SystemActivityLog.objects.filter(organization=self.organization, actor=self.owner).exists())

    def test_toggle_complete_only_updates_task_inside_active_tenant(self):
        self.client.force_login(self.owner)
        task = Task.objects.create(
            organization=self.organization,
            title="Review invoice",
            description="Validate the client invoice before approval.",
            priority=Task.Priority.HIGH,
            status=Task.Status.TODO,
            assigned_to=self.member,
            due_date=date.today(),
        )
        other_task = Task.objects.create(
            organization=self.other_organization,
            title="Other tenant task",
            description="This should remain isolated.",
            priority=Task.Priority.HIGH,
            status=Task.Status.TODO,
            assigned_to=self.other_user,
            due_date=date.today(),
        )

        response = self.client.post(reverse("tasks:toggle_complete", args=[task.pk]), HTTP_HX_REQUEST="true")
        blocked_response = self.client.post(reverse("tasks:toggle_complete", args=[other_task.pk]), HTTP_HX_REQUEST="true")

        task.refresh_from_db()
        other_task.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(task.status, Task.Status.COMPLETED)
        self.assertIsNotNone(task.completed_at)
        self.assertEqual(blocked_response.status_code, 404)
        self.assertEqual(other_task.status, Task.Status.TODO)
        self.assertIsNone(other_task.completed_at)
