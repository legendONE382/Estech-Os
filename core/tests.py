from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Organization, SystemActivityLog, UserProfile


class RegistrationFlowTests(TestCase):
    def test_register_creates_admin_workspace_and_logs_user_in(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "founder",
                "email": "founder@example.com",
                "organization_name": "Acme Services",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
            follow=True,
        )

        user = User.objects.get(username="founder")
        organization = Organization.objects.get(owner=user)
        profile = UserProfile.objects.get(user=user)

        self.assertRedirects(response, reverse("dashboard"))
        self.assertEqual(organization.name, "Acme Services")
        self.assertEqual(organization.slug, "acme-services")
        self.assertEqual(profile.organization, organization)
        self.assertEqual(profile.role, UserProfile.Role.ADMIN)
        self.assertTrue(SystemActivityLog.objects.filter(organization=organization, actor=user).exists())
        self.assertEqual(str(response.context["user"]), "founder")
