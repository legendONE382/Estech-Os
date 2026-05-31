# Estech OS

Phase 1 initializes the Django foundation, multi-tenant schema, Vercel WSGI deployment files, Supabase database configuration, and registration onboarding. Phase 2 adds the premium Neon-Glass workspace shell, HTMX navigation, and tenant-scoped dashboard analytics.

## Folder structure

```text
.
├── api/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── core/
│   ├── migrations/
│   │   ├── __init__.py
│   │   └── 0001_initial.py
│   ├── templates/core/
│   │   ├── dashboard.html
│   │   └── registration/
│   │       ├── login.html
│   │       └── register.html
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── context_processors.py
│   ├── forms.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── leads/
│   ├── __init__.py
│   ├── apps.py
│   ├── forms.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── automation/
│   ├── __init__.py
│   ├── apps.py
│   ├── engine.py
│   ├── forms.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── tasks/
│   ├── __init__.py
│   ├── apps.py
│   ├── forms.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── templates/
│   ├── base.html
│   ├── dashboard/
│   │   └── index.html
│   ├── automation/
│   │   ├── rule_list.html
│   │   ├── rule_page.html
│   │   └── partials/
│   │       ├── rule_card.html
│   │       ├── rule_create_success.html
│   │       └── rule_form.html
│   ├── leads/
│   │   ├── lead_list.html
│   │   ├── lead_page.html
│   │   └── partials/
│   │       ├── lead_card.html
│   │       ├── lead_create_success.html
│   │       ├── lead_form.html
│   │       ├── lead_status_update.html
│   │       └── status_badge.html
│   ├── tasks/
│   │   ├── task_list.html
│   │   ├── task_page.html
│   │   └── partials/
│   │       ├── task_card.html
│   │       ├── task_create_success.html
│   │       ├── task_form.html
│   │       └── task_toast.html
│   └── workspace/
│       ├── module.html
│       ├── module_page.html
│       ├── nav_link.html
│       ├── session_error.html
│       └── session_error_fragment.html
├── build_files.sh
├── manage.py
├── requirements.txt
└── vercel.json
```

## Local setup commands

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Phase 1 behavior

- Register at `/register/`.
- The registration form creates the Django `User`.
- The same transaction creates an `Organization` owned by that user.
- A `UserProfile` links the user to the organization with the `admin` role.
- The user is logged in and redirected to `/`.

## Phase 2 behavior

- Authenticated users see a fixed dark-mode workspace shell with sidebar navigation.
- Sidebar links use HTMX to replace `#main-content` and push browser history without reloading the application shell.
- Dashboard metrics and activity streams are scoped to `request.user.profile.organization`.
- If an authenticated user has no tenant profile, the workspace returns a clean recovery screen instead of raising an unhandled error.

## Phase 3 behavior

- The `/tasks/` workspace is powered by the dedicated `tasks` app.
- Task list queries are tenant-scoped and use `select_related('assigned_to__profile')` for inline assignee rendering.
- Task creation limits assignees to users in the active organization and injects the organization server-side before saving.
- HTMX task creation appends the new task card and shows a temporary success toast without reloading the shell.
- HTMX completion and status changes return only the updated `task_card.html` fragment with `outerHTML` swaps and activity logging.

## Phases 4 and 5 behavior

- The `/leads/` workspace is powered by the dedicated `leads` app and supports HTMX lead creation plus inline pipeline status changes.
- Every lead query and mutation is scoped to `request.user.profile.organization`; cross-tenant lead updates return a 404.
- The `/automated-rules/` workspace is powered by the dedicated `automation` app and creates simple active `WorkflowRule` records.
- `automation.engine.execute_workflows()` runs synchronously inside the request lifecycle for Vercel compatibility.
- Active `lead_created` rules with the `assign_member` action create a follow-up `Task` assigned to the organization owner/admin and log execution to `SystemActivityLog`.
- Lead and automation mutations return HTMX fragments with out-of-band toasts and navigation count updates.
