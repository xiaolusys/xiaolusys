# coding:utf-8

import os
from .base import *

DEBUG = False
TEMPLATE_DEBUG = DEBUG
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_AGE = 24 * 15 * 60 * 60

############################ FUNCTION SWITCH #############################
ORMCACHE_ENABLE = True # ORMCACHE SWITCH
INGORE_SIGNAL_EXCEPTION = False # signal异常捕获而且不再抛出
PUSH_SWITCH = False  # 推送开关
MAMA_MISSION_PUSH_SWITCH = False  # 妈妈周激励推送开关


STATICFILES_DIRS = (
    os.path.join(PROJECT_ROOT, "site_media", "static"),
)
STATIC_ROOT = "/data/site_media/static"
M_STATIC_URL = '/'

ALLOWED_HOSTS = ['.huyi.so', '.xiaolu.so', '.xiaolumeimei.com', '.xiaolumm.com', '121.199.168.159']

# WEB DNS
SITE_URL = 'http://staging.xiaolumeimei.com/'
#######################  WAP AND WEIXIN CONFIG ########################
M_SITE_URL = 'http://staging.xiaolumeimei.com'

CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

MYSQL_HOST = 'rm-bp17ea269uu21f9i1.mysql.rds.aliyuncs.com'
MYSQL_AUTH = 'Xiaolu_test123'
REDIS_HOST = '10.45.32.34:6379'
# REDIS_AUTH = os.environ.get('REDIS_AUTH')
REDIS_AUTH = ''

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
    # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'xiaoludb',  # Or path to database file if using sqlite3.
        'USER': 'xiaoludev',  # Not used with sqlite3.
        'PASSWORD': MYSQL_AUTH,  # Not used with sqlite3.
        'HOST': MYSQL_HOST,
    # Set to empty string for localhost. Not used with sqlite3. #192.168.0.28
        'PORT': '3306',  # Set to empty string for default. Not used with sqlite3.
        'OPTIONS': {'init_command': 'SET storage_engine=Innodb;',
                    'charset': 'utf8'},  # storage_engine need mysql>5.4,and table_type need mysql<5.4
        'TEST': {
            'NAME': 'test_xiaoludb',
            'CHARSET': 'utf8',
        }
    }
}

DJANGO_REDIS_IGNORE_EXCEPTIONS = True
CACHES = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': REDIS_HOST,
        'OPTIONS': {
            'DB': 11,
            'PASSWORD': REDIS_AUTH,
            "SOCKET_CONNECT_TIMEOUT": 5,  # in seconds
            "SOCKET_TIMEOUT": 5,  # in seconds
            # 'PARSER_CLASS': 'redis.connection.HiredisParser',
            'PICKLE_VERSION': 2,
            # 'CONNECTION_POOL_CLASS': 'redis.BlockingConnectionPool',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': 50,
                # 'timeout': 10,
            }
        }
    }
}

BROKER_URL = 'redis://%s%s/18'%(REDIS_AUTH and ':%s@'%REDIS_AUTH, REDIS_HOST)

import raven
RAVEN_CONFIG = {
    'dsn': 'http://2d63e1b731cd4e53a32b0bc096fd3566:a38d367f2c644d81b353dabfbb941070@sentry.xiaolumm.com/4',
    # If you are using git, you can also automatically configure the
    # release based on the git info.
    'release': raven.fetch_git_sha(os.path.dirname(PROJECT_ROOT)),
}
####################### WAP AND WEIXIN CONFIG ########################mp
WEIXIN_APPID = 'wxc2848fa1e1aa94b5'
WEIXIN_SECRET = 'bc41b3a535b095afc55cd40d2e808d9c'

WXPAY_APPID  = "wxc2848fa1e1aa94b5"
WXPAY_SECRET = "bc41b3a535b095afc55cd40d2e808d9c"

WXAPP_ID     = "wx25fcb32689872499"
WXAPP_SECRET = "3c7b4e3eb5ae4cfb132b2ac060a872ee"


# ================ 小米推送　======================

# 小米推送
IOS_APP_SECRET = ''
ANDROID_APP_SECRET = ''

# ================ 小米推送 END ==================

############################## PING++ SETTINGS #########################
PINGPP_CLENTIP = "121.199.168.159"
PINGPP_APPID = "app_LOOajDn9u9WDjfHa"
PINGPP_APPKEY = "sk_test_8y58u9zbPWTKTGGa1GrTi1mT"

#################### TAOBAO SETTINGS ###################
APPKEY = '21532915'   #app name super ERP test ,younixiaoxiao
APPSECRET = '7232a740a644ee9ad370b08a1db1cf2d'

################### JINGDONG SETTINGS #################
JD_APP_KEY = 'F9653439C316A32BF49DFFDE8381CBC9'
JD_APP_SECRET = 'f4fe333676af4f4eaeaa00ed20c82086'

################### QINIU SETTINGS ##################
QINIU_ACCESS_KEY = "M7M4hlQTLlz_wa5-rGKaQ2sh8zzTrdY8JNKNtvKN"
QINIU_SECRET_KEY = "8MkzPO_X7KhYQjINrnxsJ2eq5bsxKU1XmE8oMi4x"
QINIU_PRIVATE_BUCKET = 'invoiceroom'
QINIU_PRIVATE_DOMAIN = '7xrpt3.com2.z0.glb.qiniucdn.com'
QINIU_PUBLIC_BUCKET = 'xiaolumama'
QINIU_PUBLIC_DOMAIN = '7xrst8.com2.z0.glb.qiniucdn.com'

############### REMOTE MEDIA STORAGE ################
QINIU_BUCKET_NAME   = 'mediaroom'
QINIU_BUCKET_DOMAIN = '7xogkj.com1.z0.glb.clouddn.com'
QINIU_SECURE_URL    = 0
DEFAULT_FILE_STORAGE = 'qiniustorage.backends.QiniuStorage'
MEDIA_URL = "http://%s/" % QINIU_BUCKET_DOMAIN

LOGGER_HANDLERS = [
    ('service', 'jsonfile'),
    ('shopback', 'sentry,file'),
    ('shopapp', 'sentry,file'),
    ('flashsale', 'sentry,file'),
    ('core', 'sentry,file'),
    ('auth', 'sentry,file'),
    ('supplychain', 'sentry,file'),
    ('statistics', 'sentry,file'),
    ('django.request', 'sentry,file'),
    ('sentry.errors', 'sentry,file'),
    ('celery.handler', 'sentry,file'),
    ('notifyserver.handler', 'sentry,file'),
    ('yunda.handler', 'sentry,file'),
    ('mail.handler', 'sentry,file'),
    ('xhtml2pdf', 'sentry,file'),
    ('restapi.errors', 'sentry,file'),
    ('weixin.proxy', 'sentry,file'),
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


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(asctime)s %(message)s'
        },
        'json': {
            '()': 'core.logger.JsonFormatter',
            'format': '%(levelname)s %(asctime)s  %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/data/log/django/debug-staging.log',
            'formatter': 'json'
        },
        'jsonfile': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/data/log/django/service-staging.log',
            'formatter': 'json'
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
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        }
    },
    'loggers': dict([comb_logger(handler, LOGGER_TEMPLATE.copy()) for handler in LOGGER_HANDLERS]),
}

