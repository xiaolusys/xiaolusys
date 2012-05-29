

DEBUG = True
TEMPLATE_DEBUG = DEBUG

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'shopmgr',                      # Or path to database file if using sqlite3.
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
    'celery_sentry',

    'shopback.task',
    'shopback.items',
    'shopback.orders',
    'shopback.users',
    'shopback.categorys',

    'autolist',
    'search',

    'devserver',
    'django.contrib.admin',
)

#APPKEY = '12447689'
#APPSECRET = '67d32cd6e795f60414ce60c2ef51f941'

APPKEY = '12581301'
APPSECRET = '018feaa22be64ab2c5ac6982579dd80f'

REDIRECT_URL = 'http://container.open.taobao.com/container'
TAOBAO_API_ENDPOINT = 'http://gw.api.taobao.com/router/rest'


REFRESH_URL = 'http://container.open.taobao.com/container/refresh'

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



