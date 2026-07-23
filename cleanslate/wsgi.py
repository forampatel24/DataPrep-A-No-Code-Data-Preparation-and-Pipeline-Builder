"""
WSGI config for cleanslate project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cleanslate.settings')

application = get_wsgi_application()

# Force S3 storage backend directly after Django is fully initialised.
# The DefaultStorage lazy proxy can race with gunicorn's forking and
# bind to FileSystemStorage despite DEFAULT_FILE_STORAGE being set to S3.
from django.conf import settings
if getattr(settings, 'USE_S3', False):
    from django.core.files.storage import default_storage
    from django.utils.module_loading import import_string
    cls = import_string(settings.DEFAULT_FILE_STORAGE)
    default_storage._wrapped = cls()
