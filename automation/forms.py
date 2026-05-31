from django import forms

from core.models import WorkflowRule


TRIGGER_CHOICES = (
    ("lead_created", "When a lead is added"),
)

ACTION_CHOICES = (
    ("assign_member", "Assign to team member"),
)


class WorkflowRuleForm(forms.ModelForm):
    trigger = forms.ChoiceField(choices=TRIGGER_CHOICES)
    action = forms.ChoiceField(choices=ACTION_CHOICES)

    class Meta:
        model = WorkflowRule
        fields = ("name", "trigger", "action", "is_active")
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "New lead follow-up",
                    "class": "mt-2 block w-full rounded-2xl border border-slate-700/80 bg-slate-950/80 px-4 py-3 text-sm text-slate-100 outline-none transition-all duration-300 placeholder:text-slate-600 focus:border-emerald-400/60 focus:ring-4 focus:ring-emerald-400/10",
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "h-5 w-5 rounded border-slate-600 bg-slate-950 text-emerald-400 focus:ring-emerald-400/30",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        select_classes = "mt-2 block w-full rounded-2xl border border-slate-700/80 bg-slate-950/80 px-4 py-3 text-sm text-slate-100 outline-none transition-all duration-300 focus:border-emerald-400/60 focus:ring-4 focus:ring-emerald-400/10"
        self.fields["trigger"].widget.attrs.update({"class": select_classes})
        self.fields["action"].widget.attrs.update({"class": select_classes})
        self.fields["is_active"].initial = True
