"""WSGI config for Resource Partner AI."""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "resource_partner_ai.settings")

application = get_wsgi_application()
