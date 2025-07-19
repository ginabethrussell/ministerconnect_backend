"""
WSGI config for ministerconnect_backend project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import logging

from django.core.wsgi import get_wsgi_application
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ministerconnect_backend.settings")

application = get_wsgi_application()

# Log storage backend at startup
logger = logging.getLogger(__name__)
logger.warning(f"WSGI Startup - DEFAULT_FILE_STORAGE: {getattr(settings, 'DEFAULT_FILE_STORAGE', 'Not set')}")
logger.warning(f"WSGI Startup - DEBUG: {getattr(settings, 'DEBUG', 'Not set')}")
logger.warning(f"WSGI Startup - AWS_STORAGE_BUCKET_NAME: {getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'Not set')}")
