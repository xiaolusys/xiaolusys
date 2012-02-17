# Django settings for shopmanager project.

import os.path
import posixpath

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

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


TIME_ZONE = 'Asia/Shanghai'

LANGUAGE_CODE = 'en-us'

SITE_ID = 1

USE_I18N = True

USE_L10N = True

MEDIA_ROOT = os.path.join(PROJECT_ROOT, "site_media", "media")

MEDIA_URL = "/media/"

STATIC_ROOT = os.path.join(PROJECT_ROOT, "site_media", "static")

STATIC_URL = '/static/'


ADMIN_MEDIA_PREFIX = posixpath.join(STATIC_URL, "admin/")


STATIC_DOC_ROOT = os.path.join(PROJECT_ROOT, "static")

STATICFILES_DIRS = (
       os.path.join(PROJECT_ROOT, "static"),
)


STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

SECRET_KEY = 'zze(^rvhdz(hxx16a788w6jyqhtq%*v_pl^2#t1dskpb!473f8'


TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    #'shopback.base.middlewares.RecordExceptionMiddleware',
)

ROOT_URLCONF = 'shopmanager.urls'

TEMPLATE_DIRS = (
       os.path.join(PROJECT_ROOT, "templates"),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'chartit',
    'south',
    'gunicorn',
    'sentry',
    'raven.contrib.django',
    'djangorestframework',
    'djcelery',
    'djkombu',

    'celery_daemon.celery_sentry',
    'shopback.task',
    'shopback.items',
    'shopback.orders',
    'shopback.users',
    'autolist',
    'search',


)

APPKEY = '12476025'
APPSECRET = '6ad15e39391d79fece77c1d092ef13b9'
REDIRECT_URL = 'http://container.open.taobao.com/container'
TAOBAO_API_ENDPOINT = 'http://gw.api.taobao.com/router/rest'
REFRESH_URL = 'http://container.open.taobao.com/container/refresh'


AUTH_PROFILE_MODULE = 'users.user'

AUTHENTICATION_BACKENDS = (
    'auth.accounts.backends.TaoBaoBackend',
    'django.contrib.auth.backends.ModelBackend')

LOGIN_REDIRECT_URL = '/home/'

LOGIN_URL = '/accounts/login/'

LOGOUT_URL = '/accounts/logout/'


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'sentry': {
            'level': 'DEBUG',
            'class': 'raven.contrib.django.handlers.SentryHandler'
        },
        'console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['sentry'],
            'level': 'ERROR',
            'propagate': True,
        },
        'updatelisting': {
            'handlers': ['sentry'],
            'level': 'ERROR',
            'propagate': True,
        },
        'updateitemnum': {
            'handlers': ['sentry'],
            'level': 'ERROR',
            'propagate': True,
        },
        'sentry.errors': {
            'handlers': ['sentry'],
            'level': 'ERROR',
            'propagate': True,
        },
        'taobao.auth': {
            'handlers': ['sentry'],
            'level': 'ERROR',
            'propagate': True,
        },
        'auth.apis': {
            'handlers': ['sentry'],
            'level': 'ERROR',
            'propagate': True,
        },
        'permission': {
            'handlers': ['sentry'],
            'level': 'ERROR',
            'propagate': True,
        },
        'exception.middleware': {
            'handlers': ['sentry'],
            'level': 'ERROR',
            'propagate': True,
        },
        'outeridmultiple': {
            'handlers': ['sentry'],
            'level': 'ERROR',
            'propagate': True,
        },
        'period.search': {
            'handlers': ['sentry'],
            'level': 'ERROR',
            'propagate': True,
        },

    }
}


try:
    from task_settings import *
except :
    pass

try:
    from local_settings import *
except :
    pass
