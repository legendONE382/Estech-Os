from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import RegistrationForm


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome to Estech OS. Your workspace is ready.")
            return redirect("dashboard")
    else:
        form = RegistrationForm()

    return render(request, "core/registration/register.html", {"form": form})


@login_required
def dashboard(request):
    profile = request.user.profile
    return render(request, "core/dashboard.html", {"profile": profile})
