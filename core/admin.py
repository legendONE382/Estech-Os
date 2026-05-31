from django.contrib import admin

from .models import (
    Lead,
    Organization,
    SystemActivityLog,
    Task,
    UserProfile,
    WorkflowRule,
)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "owner", "created_at")
    search_fields = ("name", "slug", "owner__username", "owner__email")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "organization", "role")
    list_filter = ("role", "organization")
    search_fields = ("user__username", "user__email", "organization__name")


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("name", "company_name", "organization", "status", "created_at")
    list_filter = ("status", "organization")
    search_fields = ("name", "company_name", "email", "phone")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "organization", "assigned_to", "priority", "status", "due_date")
    list_filter = ("priority", "status", "organization")
    search_fields = ("title", "description", "assigned_to__username")


@admin.register(WorkflowRule)
class WorkflowRuleAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "trigger", "action", "is_active")
    list_filter = ("is_active", "organization")
    search_fields = ("name", "trigger", "action")


@admin.register(SystemActivityLog)
class SystemActivityLogAdmin(admin.ModelAdmin):
    list_display = ("organization", "actor", "description", "created_at")
    list_filter = ("organization", "created_at")
    search_fields = ("description", "actor__username", "organization__name")
