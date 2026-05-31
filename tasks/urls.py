from django.urls import path

from . import views

app_name = "tasks"

urlpatterns = [
    path("", views.TaskListView.as_view(), name="list"),
    path("create/", views.TaskCreateView.as_view(), name="create"),
    path("<int:pk>/toggle-complete/", views.TaskToggleCompleteView.as_view(), name="toggle_complete"),
    path("<int:pk>/status/", views.TaskStatusUpdateView.as_view(), name="update_status"),
]
