"""
WSGI config for t project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

if os.environ.get('TARGET') in ('production', 'django18'):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.production")

elif os.environ.get('TARGET') in ('staging',):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.staging")

else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.local_settings")

application = get_wsgi_application()
