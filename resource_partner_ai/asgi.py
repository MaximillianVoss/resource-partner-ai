"""ASGI config for Resource Partner AI."""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "resource_partner_ai.settings")

application = get_asgi_application()
