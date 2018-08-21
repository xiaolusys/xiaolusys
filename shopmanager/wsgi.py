"""
WSGI config for t project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

from global_setup import setup_djagno_environ, install_redis_with_gevent_socket
setup_djagno_environ()

# this block celery worker receiver!!!
# install_redis_with_gevent_socket()

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
