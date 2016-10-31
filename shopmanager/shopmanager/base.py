# encoding=utf8
# Django settings for shopmanager project.
import sys
import os


reload(sys)
sys.setdefaultencoding('utf-8')

# try:
#     import gevent_blocktracer
# except ImportError:
#     pass

import os.path
import posixpath

from global_setup import install_pymysqldb, cancel_pingpp_charge_ssl_verify
install_pymysqldb()
cancel_pingpp_charge_ssl_verify()

PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('meixqhi', 'xiuqing.mei@xiaolumeimei.com'),
)

MANAGERS = ADMINS

ALLOWED_HOSTS = ['.huyi.so', '.xiaolu.so', '.xiaolumeimei.com', '.xiaolumm.com', '.xip.io']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
    # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'shopmgr',  # Or path to database file if using sqlite3.
        'USER': 'shopmgr',  # Not used with sqlite3.
        'PASSWORD': '123123',  # Not used with sqlite3.
        'HOST': '',  # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',  # Set to empty string for default. Not used with sqlite3.
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

TIME_ZONE = 'Asia/Shanghai'

# DATETIME_INPUT_FORMATS = '%Y-%m-%d %H:%M:%S'
# DATE_INPUT_FORMATS = '%Y-%m-%d'
DATETIME_FORMAT = 'Y-m-d H:i:s'
DATE_FORMAT = 'Y-m-d'

LANGUAGE_CODE = 'en-us'
SITE_ID = 1
USE_I18N = True

# USE_L10N = True

MEDIA_ROOT = os.path.join(PROJECT_ROOT, "site_media", "media")

MEDIA_URL = "/media/"

# STATIC_ROOT = os.path.join(PROJECT_ROOT,"static")

STATIC_URL = '/static/'

DOWNLOAD_ROOT = os.path.join(PROJECT_ROOT, "site_media", 'download')

ADMIN_MEDIA_PREFIX = posixpath.join(STATIC_URL, "admin/")

STATIC_DOC_ROOT = os.path.join(PROJECT_ROOT, "site_media", "static")

STATICFILES_DIRS = (
    # os.path.join(PROJECT_ROOT,"site_media","static"),
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
    'core.middleware.middleware.XForwardedForMiddleware',
    'core.middleware.middleware.AttachContentTypeMiddleware',
    'raven.contrib.django.middleware.SentryResponseErrorIdMiddleware',
    'core.middleware.middleware.DisableDRFCSRFCheck',
    # 'core.middleware.middleware.XSessionMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    # 'django.middleware.locale.LocaleMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'shopmanager.urls'
WSGI_APPLICATION = 'shopmanager.wsgi.application'

TEMPLATES_ROOT = os.path.join(PROJECT_ROOT, "site_media", "templates")
TEMPLATE_DIRS = (
    os.path.join(PROJECT_ROOT, "templates"),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    #    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
    # 'core.middleware.context_processors.session',
)

INSTALLED_APPS =[
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.sites',
    'django.contrib.staticfiles',

    # 'provider',
    # 'provider.oauth2',
    'oauth2_provider',
    'chartit',
    'gunicorn',
    'raven.contrib.django.raven_compat',
    'rest_framework',
    'djcelery',
    'djkombu',
    'httpproxy',
    'django_statsd',
    'shopmanager.statsd',
    'core.ormcache',
    'core',
    'tagging',

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
    'shopback.warehouse',
    # 'shopback.aftersale',

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
    'shopapp.STOthermal',

    'supplychain.wavepick',
    'supplychain.supplier',
    'supplychain.category',
    # 'supplychain.temai',
    'games.paint',
    'games.bomb',
    'games.luckyawards',
    'games.weixingroup',
    'games.renewremind',

    # 'flashsale.supplier',
    'flashsale.complain',
    'flashsale.pay',
    'flashsale.finance',
    'flashsale.xiaolumm',
    'flashsale.dinghuo',
    'flashsale.workorder',
    'flashsale.luntan',
    'flashsale.clickcount',
    'flashsale.clickrebeta',
    'flashsale.mmexam',
    'flashsale.daystats',
    'flashsale.restpro',
    'flashsale.kefu',
    'flashsale.push',
    'flashsale.promotion',
    'flashsale.apprelease',
    'flashsale.protocol',
    'flashsale.coupon',
    'flashsale.forecast',
    # 'test.celery',
    'shopapp.notify',
    # 'shopapp.zhongtong'
    'statistics',
]

AUTH_PROFILE_MODULE = 'users.user'

AUTHENTICATION_BACKENDS = (
    'flashsale.pay.backends.FlashSaleBackend',
    'flashsale.pay.backends.SMSLoginBackend',
    'flashsale.pay.backends.WeixinPubBackend',
    'flashsale.pay.backends.WeixinAppBackend',
    'auth.accounts.backends.TaoBaoBackend',
    'shopapp.jingdong.backends.JingDongBackend',
    'django.contrib.auth.backends.ModelBackend'
)

LOGIN_REDIRECT_URL = '/home/'
LOGIN_URL = '/admin/login/'
LOGOUT_URL = '/accounts/logout/'


####################### TRADE HANDLERS CONFIG ########################
TRADE_HANDLERS_PATH = (
    'shopback.trades.handlers.InitHandler',
    'shopback.trades.handlers.ConfirmHandler',
    'shopback.trades.handlers.SplitHandler',
    'shopback.trades.handlers.MemoHandler',
    'shopback.trades.handlers.DefectHandler',
    'shopback.trades.handlers.RuleMatchHandler',
    'shopback.trades.handlers.StockOutHandler',
    'shopback.trades.handlers.MergeHandler',
    'shopback.trades.handlers.RefundHandler',
    'shopback.trades.handlers.LogisticsHandler',
    #    'shopback.trades.handlers.InterceptHandler',
    'shopback.trades.handlers.RegularSaleHandler',
    'shopback.trades.handlers.FinalHandler',
    #    'shopback.trades.handlers.FlashSaleHandler',
)


#################### TAOBAO SETTINGS ###################
APPKEY = '21532915'   #app name super ERP test ,younixiaoxiao
APPSECRET = '7232a740a644ee9ad370b08a1db1cf2d'

TAOBAO_API_HOSTNAME = 'eco.taobao.com'
AUTHRIZE_URL = 'https://oauth.taobao.com/authorize'
AUTHRIZE_TOKEN_URL = 'https://oauth.taobao.com/token'
REDIRECT_URI = '/accounts/login/auth/'
TAOBAO_API_ENDPOINT = 'https://%s/router/rest' % TAOBAO_API_HOSTNAME
TAOBAO_NOTIFY_URL = 'http://stream.api.taobao.com/stream'

SCOPE = 'item,promotion,usergrade'
REFRESH_URL = 'https://oauth.taobao.com/token'

#################### JINGDONG SETTINGS ###################
JD_API_HOSTNAME = 'gw.api.360buy.com'
JD_AUTHRIZE_URL = 'https://auth.360buy.com/oauth/authorize'
JD_AUTHRIZE_TOKEN_URL = 'https://auth.360buy.com/oauth/token'
JD_REDIRECT_URI = '/app/jd/login/auth/'
JD_API_ENDPOINT = 'http://%s/routerjson' % JD_API_HOSTNAME

#################### PRINT CONFIG ###################
BASE_FONT_PATH = '/data/fonts/'
FANGZHENG_LANTINGHEI_FONT_PATH = '/data/fonts/方正兰亭黑.TTF'
FONT_PATH = '/usr/share/fonts/truetype/ttf-dejavu/DejaVuSerif-Bold.ttf'
ASYNC_FILE_PATH = os.path.join(PROJECT_ROOT, "site_media", "asyncfile")

################### HTTPS/SSL SETTINGS ##################
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
HTTPS_SUPPORT = False
SECURE_REQUIRED_PATHS = (
    '/admin/',
)

################### WEIXIN SETTINGS ##################
WEIXIN_API_HOST = "https://api.weixin.qq.com"
WEIXIN_MEDIA_HOST = "http://file.api.weixin.qq.com"
WEIXIN_QRCODE_HOST = "https://mp.weixin.qq.com"
WEIXIN_AUTHORIZE_URL = "https://open.weixin.qq.com/connect/oauth2/authorize"

################### Ntalker SETTINGS ##################
NTALKER_NOTIFY_URL = 'http://wx.ntalker.com/agent/weixin'
WX_MESSAGE_URL = 'https://api.weixin.qq.com/cgi-bin/message/custom/send'
WX_MEDIA_UPLOAD_URL = 'https://api.weixin.qq.com/cgi-bin/media/upload'
WX_MEDIA_GET_URL = 'https://api.weixin.qq.com/cgi-bin/media/get'

############################# EXTENSION CONFIG ##############################
TAOBAO_PAGE_SIZE = 50  # the page_size of  per request
# sale order regular days
REGULAR_DAYS = 10

############################# TASK SETTINGS ##############################
from .task_settings import *  # celery config

############################## RESTFRAMEWORK CONFIG #########################
REST_FRAMEWORK = {
    #     'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.AllowAny',),
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
    'DEFAULT_FILTER_BACKENDS': ('rest_framework.filters.DjangoFilterBackend',),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        # 'rest_framework.renderers.TemplateHTMLRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'EXCEPTION_HANDLER': 'flashsale.restpro.exceptions.my_exception_handler',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10, # Default to 10
    'PAGINATE_BY_PARAM': 'page_size',  # Allow client to override, using `?page_size=xxx`.
    'MAX_PAGINATE_BY': 100,
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'oauth2_provider.ext.rest_framework.OAuth2Authentication',
    ),
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': '3600/hour',
        'user': '3600/hour'
    }
}

REST_FRAMEWORK_EXTENSIONS = {
    'DEFAULT_USE_CACHE': 'default',
    'DEFAULT_CACHE_ERRORS': False,
    'DEFAULT_CACHE_RESPONSE_TIMEOUT': 60 * 15,
    'DEFAULT_CACHE_KEY_FUNC': 'rest_framework_extensions.utils.default_cache_key_func'
}
JSONFIELD_ENCODER_CLASS = 'django.core.serializers.json.DjangoJSONEncoder'
