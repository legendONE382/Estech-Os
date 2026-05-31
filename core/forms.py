from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db import transaction
from django.utils.text import slugify

from .models import Organization, SystemActivityLog, UserProfile


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    organization_name = forms.CharField(max_length=255)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "organization_name", "password1", "password2")

    def clean_email(self) -> str:
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def _unique_organization_slug(self, organization_name: str) -> str:
        base_slug = slugify(organization_name) or "organization"
        slug = base_slug
        suffix = 2
        while Organization.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{suffix}"
            suffix += 1
        return slug

    @transaction.atomic
    def save(self, commit: bool = True) -> User:
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]

        if commit:
            user.save()
            organization_name = self.cleaned_data["organization_name"]
            organization = Organization.objects.create(
                name=organization_name,
                slug=self._unique_organization_slug(organization_name),
                owner=user,
            )
            UserProfile.objects.create(
                user=user,
                organization=organization,
                role=UserProfile.Role.ADMIN,
            )
            SystemActivityLog.objects.create(
                organization=organization,
                actor=user,
                description="Organization created during onboarding.",
            )

        return user


class OrganizationSettingsForm(forms.ModelForm):
    name = forms.CharField(
        max_length=255,
        label="Organization name",
        widget=forms.TextInput(
            attrs={
                "class": "w-full rounded-3xl border border-slate-700/80 bg-slate-950/80 px-4 py-3 text-sm text-slate-100 outline-none transition focus:border-emerald-400/60 focus:ring-4 focus:ring-emerald-400/10",
                "placeholder": "Enter your organization name",
            }
        ),
    )

    class Meta:
        model = Organization
        fields = ("name",)

    def clean_name(self) -> str:
        name = self.cleaned_data["name"].strip()
        if not name:
            raise forms.ValidationError("Organization name cannot be blank.")
        return name
