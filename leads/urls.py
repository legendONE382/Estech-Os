from django.urls import path

from . import views

app_name = "leads"

urlpatterns = [
    path("", views.LeadListView.as_view(), name="list"),
    path("create/", views.LeadCreateView.as_view(), name="create"),
    path("<int:pk>/status/", views.LeadStatusUpdateView.as_view(), name="update_status"),
]
