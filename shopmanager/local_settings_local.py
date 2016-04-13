# coding:utf-8
__author__ = 'zfz'
import os

DEBUG = True
SHOW_SQL = True
TEMPLATE_DEBUG = DEBUG

SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_AGE = 12 * 60 * 60

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',  # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
#         'NAME': 'shopmgr',  # Or path to database file if using sqlite3.
#         'USER': 'meixqhi',  # Not used with sqlite3.
#         'PASSWORD': '123123',  # Not used with sqlite3.
#         'HOST': '192.168.1.101',  # Set to empty string for localhost. Not used with sqlite3. #192.168.0.28
#         'PORT': '3306',  # Set to empty string for default. Not used with sqlite3.
#         'OPTIONS':  {'init_command': 'SET storage_engine=Innodb;',
#                      'charset': 'utf8'},  # storage_engine need mysql>5.4,and table_type need mysql<5.4
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
    # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'shopmgr_hy',  # Or path to database file if using sqlite3.
        'USER': 'meixqhi',  # Not used with sqlite3.
        'PASSWORD': '123123',  # Not used with sqlite3.
        'HOST': '192.168.1.101',  # Set to empty string for localhost. Not used with sqlite3. #192.168.0.28
        'PORT': '3306',  # Set to empty string for default. Not used with sqlite3.
        'OPTIONS': {'init_command': 'SET storage_engine=Innodb;',
                    'charset': 'utf8'},  # storage_engine need mysql>5.4,and table_type need mysql<5.4
    }
}

if DEBUG:
    STATICFILES_DIRS = (
        os.path.join(PROJECT_ROOT, "site_media", "static"),
    )
    STATIC_ROOT = os.path.join(PROJECT_ROOT, "site_media", "local")
else:
    STATIC_ROOT = os.path.join(PROJECT_ROOT, "site_media", "static")

M_STATIC_URL = '/static/wap/'

MIDDLEWARE_CLASSES = (
    'raven.contrib.django.middleware.SentryResponseErrorIdMiddleware',
    'core.middleware.middleware.SecureRequiredMiddleware',
    'core.middleware.middleware.DisableDRFCSRFCheck',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

if DEBUG:
    MIDDLEWARE_CLASSES = ('core.middleware.middleware.ProfileMiddleware',
                          'core.middleware.middleware.QueryCountDebugMiddleware',) + MIDDLEWARE_CLASSES

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}
ORMCACHE_ENABLE = True

RAVEN_CONFIG = {
    'dsn': 'http://ada7dc70824c43fd8ba430db3827cd62:283aaec97585411ca9e66bb8bb1a9c63@sentry.huyi.so:8089/3',
    'register_signals': True,
}

#################### change this site to yourself test domain #######################
# SITE_URL = 'http://192.168.1.11:9000/'
# M_SITE_URL = 'http://192.168.1.11:9000/'

SITE_URL = 'http://192.168.1.56:8000/'
M_SITE_URL = 'http://192.168.1.56:8000/'

MIDDLEWARE_CLASSES = (
    'raven.contrib.django.middleware.SentryResponseErrorIdMiddleware',
    'core.middleware.middleware.SecureRequiredMiddleware',
    'core.middleware.middleware.DisableDRFCSRFCheck',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.RemoteUserMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)
########################### ONEAPM Statsd ##############################
# STATSD_PORT = 8251
STATSD_CLIENT = 'statsd.oneapm'
STATSD_CELERY_SIGNALS = True
MIDDLEWARE_CLASSES = (
                         'django_statsd.middleware.GraphiteRequestTimingMiddleware',
                         'django_statsd.middleware.GraphiteMiddleware',
                     ) + MIDDLEWARE_CLASSES

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
    'shopback.trades.handlers.InterceptHandler',
    'shopback.trades.handlers.FinalHandler',
)

#################### TAOBAO SETTINGS ###################
# APPKEY = '21532915'   #app name super ERP test ,younixiaoxiao
# APPSECRET = '7232a740a644ee9ad370b08a1db1cf2d'

APPKEY = '1012545735'  # app name guanyi erp ,younishijie
APPSECRET = 'sandbox4a7f3927e06af6931eefb37f3'

TAOBAO_API_HOSTNAME = 'gw.api.tbsandbox.com'
AUTHRIZE_URL = 'https://oauth.tbsandbox.com/authorize'
AUTHRIZE_TOKEN_URL = 'https://oauth.tbsandbox.com/token'
REDIRECT_URI = '/accounts/login/auth/'
TAOBAO_API_ENDPOINT = 'https://%s/router/rest' % TAOBAO_API_HOSTNAME
TAOBAO_NOTIFY_URL = 'http://stream.api.taobao.com/stream'

SCOPE = 'item,promotion,usergrade'
REFRESH_URL = 'https://oauth.taobao.com/token'

BASE_FONT_PATH = '/home/meron/workspace/fonts/'
FONT_PATH = '/usr/share/fonts/truetype/ttf-dejavu/DejaVuSerif-Bold.ttf'
ASYNC_FILE_PATH = os.path.join(PROJECT_ROOT, "site_media", "asyncfile")

################### HTTPS/SSL SETTINGS ##################

HTTPS_SUPPORT = False
SECURE_REQUIRED_PATHS = (
    '/admin/',
)

REST_FRAMEWORK_EXTENSIONS = {
    'DEFAULT_USE_CACHE': 'default',
    'DEFAULT_CACHE_ERRORS': False,
    'DEFAULT_CACHE_RESPONSE_TIMEOUT': 60 * 0,
    'DEFAULT_CACHE_KEY_FUNC': 'rest_framework_extensions.utils.default_cache_key_func'
}
################### SALEORDER CONFIG ##################
# sale order regular days
REGULAR_DAYS = 20

################### WEIXIN SETTINGS ##################
# for weixin pub younishijie
WEIXIN_API_HOST = "https://api.weixin.qq.com"
WEIXIN_MEDIA_HOST = "http://file.api.weixin.qq.com"
WEIXIN_AUTHORIZE_URL = "https://open.weixin.qq.com/connect/oauth2/authorize"
WEIXIN_QRCODE_HOST = "https://mp.weixin.qq.com"
WEIXIN_APPID = 'wx91b20565c83072f6'
WEIXIN_SECRET = '38e6b5f94c0f4966460913b5c11284a9'
# for weixin pub xiaolumm,just for pay
WXPAY_APPID = "wx3f91056a2928ad2d"
WXPAY_SECRET = "e8e1f648a5e02492e1584e5413cef158"
# for weixin app
WXAPP_ID = "wx25fcb32689872499"
WXAPP_SECRET = "3c7b4e3eb5ae4cmeixqhisok060a872ee"

################### JINGDONG SETTINGS #################

JD_APP_KEY = 'FD41E99D04BF7EB6DECDA7043A4D57E1'
JD_APP_SECRET = 'e33d1f1b4abb4036b742787211624fe1'

JD_API_HOSTNAME = 'gw.api.360buy.com'
JD_AUTHRIZE_URL = 'https://auth.360buy.com/oauth/authorize'
JD_AUTHRIZE_TOKEN_URL = 'https://auth.360buy.com/oauth/token'
JD_REDIRECT_URI = '/app/jd/login/auth/'
JD_API_ENDPOINT = 'http://%s/routerjson' % JD_API_HOSTNAME

################### PING++ SETTINGS ##################

PINGPP_APPID = "app_qPCaj95Serj5PKOq"
PINGPP_APPKEY = "sk_test_8y58u9zbPWTKTGGa1GrTi1mT"  # TEST KEY
PINGPP_CLENTIP = "127.0.0.1"

################### Ntalker SETTINGS ##################

NTALKER_NOTIFY_URL = 'http://wx.ntalker.com/agent/weixin'
WX_MESSAGE_URL = 'https://api.weixin.qq.com/cgi-bin/message/custom/send'
WX_MEDIA_UPLOAD_URL = 'https://api.weixin.qq.com/cgi-bin/media/upload'
WX_MEDIA_GET_URL = 'https://api.weixin.qq.com/cgi-bin/media/get'

################### QINIU SETTINGS ##################

QINIU_ACCESS_KEY = "M7M4hlQTLlz_wa5-rGKaQ2sh8zzTrdY8JNKNtvKN"
QINIU_SECRET_KEY = "8MkzPO_X7KhYQjINrnxsJ2eq5bsxKU1XmE8oMi4x"

QINIU_PRIVATE_BUCKET = 'invoiceroom'  # 七牛私有空间
QINIU_PRIVATE_DOMAIN = '7xrpt3.com2.z0.glb.qiniucdn.com'

QINIU_PUBLIC_BUCKET = 'xiaolumama'  # 七牛公开空间,保存分享二维码,及其它商品信息
QINIU_PUBLIC_DOMAIN = '7xrst8.com2.z0.glb.qiniucdn.com'

LOGGER_HANDLERS = [
    ('models', 'sentry,console'),
    ('queryset', 'sentry,console'),
    ('django.request', 'sentry,console'),
    ('sentry.errors', 'sentry,console'),
    ('celery.handler', 'sentry,console'),
    ('notifyserver.handler', 'sentry,console'),
    ('yunda.handler', 'sentry,console'),
    ('mail.handler', 'sentry,console'),
    ('xhtml2pdf', 'sentry,console'),
    ('restapi.errors', 'sentry,console'),
    ('weixin.proxy', 'sentry,console'),
]

LOGGER_TEMPLATE = {
    'handlers': ['sentry'],
    'level': 'DEBUG',
    'propagate': True,
}


def comb_logger(log_tuple, temp):
    if isinstance(log_tuple, (list, tuple)) and len(log_tuple) == 2:
        temp.update(handlers=log_tuple[1].split(','))
        return log_tuple[0], temp
    return log_tuple[0], temp


mysql_log_set = {
    'django.db.backends': {
        'handlers': ['console'],
        'propagate': True,
        'level': 'DEBUG',
    }
}
loggers_ori_set = dict([comb_logger(handler, LOGGER_TEMPLATE.copy()) for handler in LOGGER_HANDLERS])
if SHOW_SQL:
    loggers_ori_set = mysql_log_set
    # loggers_ori_set.update(mysql_log_set)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(asctime)s  %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/tmp/django-debug.log',
            'formatter': 'simple'
        },
        'sentry': {
            'level': 'ERROR',
            'class': 'raven.contrib.django.handlers.SentryHandler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'mail_admins': {
            'level': 'INFO',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        }
    },
    'loggers': loggers_ori_set,
}

# for disable urllib3 ssl warning
import logging

logging.captureWarnings(True)
