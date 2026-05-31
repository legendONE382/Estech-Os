# Estech OS

Phase 1 initializes the Django foundation, multi-tenant schema, Vercel WSGI deployment files, Supabase database configuration, and registration onboarding.

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
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   └── registration/
│   │       ├── login.html
│   │       └── register.html
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
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
