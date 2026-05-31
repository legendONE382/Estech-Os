from django.urls import path

from . import views

app_name = "automation"

urlpatterns = [
    path("", views.WorkflowRuleListView.as_view(), name="list"),
    path("create/", views.WorkflowRuleCreateView.as_view(), name="create"),
]
