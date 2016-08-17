"""
WSGI config for t project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

from global_setup import setup_djagno_environ
setup_djagno_environ()

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
