"""WSGI config for Estech OS, used by Vercel's Python runtime."""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.settings")

app = application = get_wsgi_application()
