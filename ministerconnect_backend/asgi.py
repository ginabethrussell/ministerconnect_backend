"""
ASGI config for ministerconnect_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import logging

from django.core.asgi import get_asgi_application
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ministerconnect_backend.settings")

application = get_asgi_application()

# Log storage backend at startup
logger = logging.getLogger(__name__)
logger.warning(f"ASGI Startup - DEFAULT_FILE_STORAGE: {getattr(settings, 'DEFAULT_FILE_STORAGE', 'Not set')}")
logger.warning(f"ASGI Startup - DEBUG: {getattr(settings, 'DEBUG', 'Not set')}")
logger.warning(f"ASGI Startup - AWS_STORAGE_BUCKET_NAME: {getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'Not set')}")
