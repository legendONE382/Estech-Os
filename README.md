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
├── templates/
│   ├── base.html
│   ├── dashboard/
│   │   └── index.html
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
