from django import forms
from django.contrib.auth.models import User

from core.models import Organization, Task


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ("title", "description", "priority", "status", "assigned_to", "due_date")
        labels = {
            "assigned_to": "Assigned to",
            "due_date": "Due date",
        }
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "placeholder": "Review client proposal",
                    "class": "mt-2 block w-full rounded-2xl border border-slate-700/80 bg-slate-950/80 px-4 py-3 text-sm text-slate-100 outline-none transition-all duration-300 placeholder:text-slate-600 focus:border-emerald-400/60 focus:ring-4 focus:ring-emerald-400/10",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Add the operational context your teammate needs.",
                    "class": "mt-2 block w-full rounded-2xl border border-slate-700/80 bg-slate-950/80 px-4 py-3 text-sm text-slate-100 outline-none transition-all duration-300 placeholder:text-slate-600 focus:border-emerald-400/60 focus:ring-4 focus:ring-emerald-400/10",
                }
            ),
            "priority": forms.Select(
                attrs={
                    "class": "mt-2 block w-full rounded-2xl border border-slate-700/80 bg-slate-950/80 px-4 py-3 text-sm text-slate-100 outline-none transition-all duration-300 focus:border-emerald-400/60 focus:ring-4 focus:ring-emerald-400/10",
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "mt-2 block w-full rounded-2xl border border-slate-700/80 bg-slate-950/80 px-4 py-3 text-sm text-slate-100 outline-none transition-all duration-300 focus:border-emerald-400/60 focus:ring-4 focus:ring-emerald-400/10",
                }
            ),
            "assigned_to": forms.Select(
                attrs={
                    "class": "mt-2 block w-full rounded-2xl border border-slate-700/80 bg-slate-950/80 px-4 py-3 text-sm text-slate-100 outline-none transition-all duration-300 focus:border-emerald-400/60 focus:ring-4 focus:ring-emerald-400/10",
                }
            ),
            "due_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "mt-2 block w-full rounded-2xl border border-slate-700/80 bg-slate-950/80 px-4 py-3 text-sm text-slate-100 outline-none transition-all duration-300 focus:border-emerald-400/60 focus:ring-4 focus:ring-emerald-400/10",
                }
            ),
        }

    def __init__(self, *args, organization: Organization, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization = organization
        self.fields["assigned_to"].queryset = User.objects.filter(
            profile__organization=organization
        ).select_related("profile", "profile__organization").order_by("username")

    def clean_assigned_to(self):
        assigned_to = self.cleaned_data["assigned_to"]
        if not User.objects.filter(pk=assigned_to.pk, profile__organization=self.organization).exists():
            raise forms.ValidationError("Select a team member from this organization.")
        return assigned_to
