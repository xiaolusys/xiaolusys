# coding: utf-8

import os
from django.conf import settings
from django.core.wsgi import get_wsgi_application

os.environ['DJANGO_SETTINGS_MODULE'] = "settings"

application = get_wsgi_application()

# reset ROOT_URLCONF
settings.ROOT_URLCONF = 'urls'
