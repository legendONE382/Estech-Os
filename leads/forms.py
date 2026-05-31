from django import forms

from core.models import Lead


class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ("name", "company_name", "email", "phone", "status", "notes")
        labels = {
            "company_name": "Company",
        }
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Avery Johnson",
                    "class": "mt-2 block w-full rounded-2xl border border-slate-700/80 bg-slate-950/80 px-4 py-3 text-sm text-slate-100 outline-none transition-all duration-300 placeholder:text-slate-600 focus:border-emerald-400/60 focus:ring-4 focus:ring-emerald-400/10",
                }
            ),
            "company_name": forms.TextInput(
                attrs={
                    "placeholder": "Northstar Studio",
                    "class": "mt-2 block w-full rounded-2xl border border-slate-700/80 bg-slate-950/80 px-4 py-3 text-sm text-slate-100 outline-none transition-all duration-300 placeholder:text-slate-600 focus:border-emerald-400/60 focus:ring-4 focus:ring-emerald-400/10",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "placeholder": "avery@example.com",
                    "class": "mt-2 block w-full rounded-2xl border border-slate-700/80 bg-slate-950/80 px-4 py-3 text-sm text-slate-100 outline-none transition-all duration-300 placeholder:text-slate-600 focus:border-emerald-400/60 focus:ring-4 focus:ring-emerald-400/10",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "placeholder": "+1 555 0142",
                    "class": "mt-2 block w-full rounded-2xl border border-slate-700/80 bg-slate-950/80 px-4 py-3 text-sm text-slate-100 outline-none transition-all duration-300 placeholder:text-slate-600 focus:border-emerald-400/60 focus:ring-4 focus:ring-emerald-400/10",
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "mt-2 block w-full rounded-2xl border border-slate-700/80 bg-slate-950/80 px-4 py-3 text-sm text-slate-100 outline-none transition-all duration-300 focus:border-emerald-400/60 focus:ring-4 focus:ring-emerald-400/10",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Capture qualification notes, source, and next best action.",
                    "class": "mt-2 block w-full rounded-2xl border border-slate-700/80 bg-slate-950/80 px-4 py-3 text-sm text-slate-100 outline-none transition-all duration-300 placeholder:text-slate-600 focus:border-emerald-400/60 focus:ring-4 focus:ring-emerald-400/10",
                }
            ),
        }
