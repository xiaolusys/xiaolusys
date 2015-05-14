# Django settings for shopmanager project.

import os.path
import posixpath

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
     ('meixqhi', 'xiuqing.mei@huyi.so'),
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

#DATETIME_INPUT_FORMATS = '%Y-%m-%d %H:%M:%S'
#DATE_INPUT_FORMATS = '%Y-%m-%d'
DATETIME_FORMAT    = 'Y-m-d H:i:s'
DATE_FORMAT        = 'Y-m-d'

LANGUAGE_CODE = 'en-us'

SITE_ID = 1

USE_I18N = True

#USE_L10N = True

MEDIA_ROOT = os.path.join(PROJECT_ROOT, "site_media", "media")

MEDIA_URL = "/media/"

#STATIC_ROOT = os.path.join(PROJECT_ROOT,"static")

STATIC_URL = '/static/'

DOWNLOAD_ROOT   = os.path.join(PROJECT_ROOT,"site_media",'download')

ADMIN_MEDIA_PREFIX = posixpath.join(STATIC_URL, "admin/")

STATIC_DOC_ROOT = os.path.join(PROJECT_ROOT,"site_media","static")

STATICFILES_DIRS = (
       #os.path.join(PROJECT_ROOT,"site_media","static"),
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
    'raven.contrib.django.middleware.SentryResponseErrorIdMiddleware',
    'middleware.middleware.SecureRequiredMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.RemoteUserMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)


ROOT_URLCONF = 'shopmanager.urls'

TEMPLATE_DIRS = (
       os.path.join(PROJECT_ROOT, "templates"),
)

INSTALLED_APPS = (
    'django.contrib.admin',
    #'django.contrib.admindocs',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    'chartit',
    'south',
    'gunicorn',
    'raven.contrib.django',
    'djangorestframework',
    'rest_framework',
    'djcelery',
    'djkombu',
    'deamon',
    'deamon.celery_sentry',
    
    'common',
    'shopback.amounts',
    'shopback.categorys',
    'shopback.fenxiao',
    'shopback.items',
    'shopback.logistics',
    'shopback.monitor',
    'shopback.orders',
    'shopback.trades',
    'shopback.refunds',
    'shopback.users',
    'shopback.archives',
    'shopback.purchases',
    #'shopback.aftersale',
    
    'shopapp.autolist',
    'shopapp.collector',
    'shopapp.memorule',
    'shopapp.report',
    'shopapp.asynctask',
    'shopapp.modifyfee',
    'shopapp.calendar',
    'shopapp.babylist',
    'shopapp.juhuasuan',
    'shopapp.smsmgr',
    'shopapp.yunda',
    'shopapp.comments',
    'shopapp.weixin',
    'shopapp.tmcnotify',
    
    'shopapp.jingdong',
    'shopapp.intercept',
    'shopapp.examination',
    'shopapp.weixin_sales',
    'shopapp.weixin_score',
    'shopapp.weixin_examination',
    'shopapp.sampleproduct',
    
    
    #'shopapp.second_time_sort',
    'supplychain.wavepick',
    #'supplychain.temai',
    'games.paint',
    'games.bomb',

#     'flashsale.supplier',
    'flashsale.pay',
    'flashsale.xiaolumm',
    'flashsale.dinghuo',
    'flashsale.clickcount',
    'flashsale.clickrebeta',
    'flashsale.mmexam',

    'mathfilters',

    #'test.celery',
    #'shopapp.notify',
)


AUTH_PROFILE_MODULE = 'users.user'

AUTHENTICATION_BACKENDS = (
    'flashsale.pay.backends.FlashSaleBackend',
    'flashsale.pay.backends.WeixinPubBackend',
    'auth.accounts.backends.TaoBaoBackend',
    'shopapp.jingdong.backends.JingDongBackend',
    'django.contrib.auth.backends.ModelBackend')

LOGIN_REDIRECT_URL = '/home/'
LOGIN_URL = '/admin/'
LOGOUT_URL = '/accounts/logout/'


TAOBAO_PAGE_SIZE = 100              #the page_size of  per request
NO_PIC_PATH = 'img/nopic.jpg'


from prod_settings import *

try:
    from local_settings import *
except ImportError:
    if DEBUG:
        raise Exception("LOCAL SETTINGS IS REQUIRED!")

from task_settings import *

if DEBUG:
    BROKER_URL = 'amqp://user1:passwd1@192.168.1.101:5672/vtest1'
    
REST_FRAMEWORK = {
    #'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.AllowAny',),
    'DEFAULT_FILTER_BACKENDS': ('rest_framework.filters.DjangoFilterBackend',),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.TemplateHTMLRenderer',
        'rest_framework.renderers.YAMLRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'PAGINATE_BY': 10,                 # Default to 10
    'PAGINATE_BY_PARAM': 'page_size',  # Allow client to override, using `?page_size=xxx`.
    'MAX_PAGINATE_BY': 100     
}


if DEBUG:
    MIDDLEWARE_CLASSES = ('middleware.middleware.ProfileMiddleware',
                          'middleware.middleware.QueryCountDebugMiddleware',) + MIDDLEWARE_CLASSES


