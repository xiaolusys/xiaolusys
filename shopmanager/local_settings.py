__author__ = 'zfz'


import os

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': os.path.join(PROJECT_ROOT, 'database.db'),                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

APPKEY = '12476025'
APPSECRET = '6ad15e39391d79fece77c1d092ef13b9'
REDIRECT_URL = 'http://container.open.taobao.com/container'
TAOBAO_API_ENDPOINT = 'http://gw.api.taobao.com/router/rest'
REFRESH_URL = 'http://container.open.taobao.com/container/refresh'