__author__ = 'zfz'

import os

DEBUG = False
TEMPLATE_DEBUG = DEBUG

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'shopmgr',                      # Or path to database file if using sqlite3.
        'USER': 'shopmgr',                      # Not used with sqlite3.
        'PASSWORD': '123123',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

APPKEY = '12517640'
APPSECRET = 'e50beebdf9226e3fc991834375e32b5a'
REDIRECT_URL = 'http://container.open.taobao.com/container'
TAOBAO_API_ENDPOINT = 'http://gw.api.taobao.com/router/rest'
REFRESH_URL = 'http://container.open.taobao.com/container/refresh'
