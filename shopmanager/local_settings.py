import os.path
import posixpath

DEBUG = True
TEMPLATE_DEBUG = DEBUG

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
#
#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
#        'NAME': os.path.join(PROJECT_ROOT, 'database.db'),                      # Or path to database file if using sqlite3.
#        'USER': '',                      # Not used with sqlite3.
#        'PASSWORD': '',                  # Not used with sqlite3.
#        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
#        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
#    }
#}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'taobaoshop',                      # Or path to database file if using sqlite3.
        'USER': 'meixqhi',                      # Not used with sqlite3.
        'PASSWORD': '123123',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}


INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'chartit',
    'south',
    'gunicorn',
    'sentry',
    'raven.contrib.django',
    'djangorestframework',
    'djcelery',
    'djkombu',
    'deamon',
    'deamon.celery_sentry',

    'shopback.users',
    'shopback.items',
    'shopback.amounts',
    'shopback.categorys',
    'shopback.fenxiao',
    'shopback.logistics',
    'shopback.monitor',
    'shopback.orders',
    'shopback.refunds',


    'shopapp.autolist',
    'shopapp.collector',
    'shopapp.memorule',
    'shopapp.report',
    'shopapp.syncnum',

    #'devserver',
    'django.contrib.admin',
)


APPKEY = '21036602'
APPSECRET = 'daa98d080842335088c3b80c2676b005'

#APPKEY = '12686841'
#APPSECRET = '501b8d23212601443eec4fef13e7c84d'

AUTHRIZE_URL = 'https://oauth.taobao.com/authorize'
AUTHRIZE_TOKEN_URL = 'https://oauth.taobao.com/token'
REDIRECT_URI = 'http://localhost:8000/accounts/login/taobao/'
TAOBAO_API_ENDPOINT = 'http://gw.api.taobao.com/router/rest'

SCOPE = 'item,promotion,usergrade'

REFRESH_URL = 'https://oauth.taobao.com/token'

FONT_PATH = '/usr/share/fonts/truetype/ttf-dejavu/DejaVuSerifCondensed-BoldItalic.ttf'



DEVSERVER_MODULES = (
    'devserver.modules.sql.SQLRealTimeModule',
    'devserver.modules.sql.SQLSummaryModule',
    #'devserver.modules.profile.ProfileSummaryModule',

    # Modules not enabled by default
    'devserver.modules.ajax.AjaxDumpModule',
    'devserver.modules.profile.MemoryUseModule',
    'devserver.modules.cache.CacheSummaryModule',
    #'devserver.modules.profile.LineProfilerModule',
)



