# Django settings for shopmanager project.
import sys
import os
reload(sys)
sys.setdefaultencoding('utf-8')

import os.path
import posixpath

PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

DEBUG = False
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

SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

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
    'core.middleware.middleware.AttachContentTypeMiddleware',
    'raven.contrib.django.middleware.SentryResponseErrorIdMiddleware',
    'core.middleware.middleware.SecureRequiredMiddleware',
    'core.middleware.middleware.DisableDRFCSRFCheck',
    'django.middleware.common.CommonMiddleware',
    #'django.contrib.sessions.middleware.SessionMiddleware',
    'core.middleware.middleware.XSessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.RemoteUserMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)


ROOT_URLCONF = 'shopmanager.urls'

TEMPLATES_ROOT = os.path.join(PROJECT_ROOT, "site_media", "templates")
TEMPLATE_DIRS  = (
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
    'core.middleware.context_processors.session',
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

    #'shopapp.zhongtong',

    'shopapp.jingdong',
    'shopapp.intercept',
    'shopapp.examination',
    'shopapp.weixin_sales',
    'shopapp.weixin_score',
    'shopapp.weixin_examination',
    'shopapp.sampleproduct',

    #'shopapp.second_time_sort',
    'supplychain.wavepick',
    'supplychain.supplier',
    'supplychain.category',
    #'supplychain.temai',
    'games.paint',
    'games.bomb',
    'games.luckyawards',

    #'flashsale.supplier',
    'flashsale.complain',
    'flashsale.pay',
    'flashsale.xiaolumm',
    'flashsale.dinghuo',
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
    'extrafunc.renewremind',
    #'test.celery',
    #'shopapp.notify',
)


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
LOGIN_URL = '/admin/'
LOGOUT_URL = '/accounts/logout/'

############################# EXTENSION CONFIG ##############################

TAOBAO_PAGE_SIZE = 50              # the page_size of  per request

from task_settings import *      # celery config

REST_FRAMEWORK = {
#     'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.AllowAny',),
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
    'DEFAULT_FILTER_BACKENDS': ('rest_framework.filters.DjangoFilterBackend',),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
#         'rest_framework.renderers.TemplateHTMLRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'EXCEPTION_HANDLER': 'flashsale.restpro.exceptions.my_exception_handler',
    'PAGINATE_BY': 10,                 # Default to 10
    'PAGINATE_BY_PARAM': 'page_size',  # Allow client to override, using `?page_size=xxx`.
    'MAX_PAGINATE_BY': 100
}

REST_FRAMEWORK_EXTENSIONS = {
    'DEFAULT_USE_CACHE':'default',
    'DEFAULT_CACHE_ERRORS': False,
    'DEFAULT_CACHE_RESPONSE_TIMEOUT': 60 * 15,
    'DEFAULT_CACHE_KEY_FUNC':'rest_framework_extensions.utils.default_cache_key_func'
}

JSONFIELD_ENCODER_CLASS = 'django.core.serializers.json.DjangoJSONEncoder'

if os.environ.get('TARGET') == 'staging':
    DEBUG = False
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
            'NAME': 'shopmgr',                      # Or path to database file if using sqlite3.
            'USER': 'xiaoludev',                      # Not used with sqlite3.
            'PASSWORD': 'xiaolu_test123',                  # Not used with sqlite3.
            'HOST': 'rdsvrl2p9pu6536n7d99.mysql.rds.aliyuncs.com',                      # Set to empty string for localhost. Not used with sqlite3. #192.168.0.28
            'PORT': '3306',                      # Set to empty string for default. Not used with sqlite3.
            'OPTIONS':  {'init_command': 'SET storage_engine=Innodb;', 
                         'charset': 'utf8'}, #storage_engine need mysql>5.4,and table_type need mysql<5.4
        }
    }
    CACHES = {
        'default': {
            'BACKEND': 'redis_cache.RedisCache',
            'LOCATION': '55a32ec47c8d41f7.m.cnhza.kvstore.aliyuncs.com:6379',
            'OPTIONS':{
                'DB': 9,
                'PASSWORD': '55a32ec47c8d41f7:Huyiinc12345',
            }
        }
    }    
    BROKER_URL = 'redis://:55a32ec47c8d41f7:Huyiinc12345@55a32ec47c8d41f7.m.cnhza.kvstore.aliyuncs.com:6379/8'
    import raven
    RAVEN_CONFIG = {
        'dsn': 'http://e419f1ed03004d03bad7b4b563f74241:12fbfa94d636472d92ae964757627367@sentry.xiaolumm.com/3',
        # If you are using git, you can also automatically configure the
        # release based on the git info.
        'release': raven.fetch_git_sha(os.path.dirname(PROJECT_ROOT)),
    }

if os.environ.get('TARGET') == 'django18':
    DEBUG = False
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
        # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
            'NAME': 'shopmgr',  # Or path to database file if using sqlite3.
            'USER': 'xiaoludev',  # Not used with sqlite3.
            'PASSWORD': 'xiaolu_test123',  # Not used with sqlite3.
            'HOST': 'rdsvrl2p9pu6536n7d99.mysql.rds.aliyuncs.com',
        # Set to empty string for localhost. Not used with sqlite3. #192.168.0.28
            'PORT': '3306',  # Set to empty string for default. Not used with sqlite3.
            'OPTIONS': {'init_command': 'SET storage_engine=Innodb;',
                        'charset': 'utf8'},  # storage_engine need mysql>5.4,and table_type need mysql<5.4
        }
    }
    CACHES = {
        'default': {
            'BACKEND': 'redis_cache.RedisCache',
            'LOCATION': '55a32ec47c8d41f7.m.cnhza.kvstore.aliyuncs.com:6379',
            'OPTIONS': {
                'DB': 9,
                'PASSWORD': '55a32ec47c8d41f7:Huyiinc12345',
            }
        }
    }
    BROKER_URL = 'redis://:55a32ec47c8d41f7:Huyiinc12345@55a32ec47c8d41f7.m.cnhza.kvstore.aliyuncs.com:6379/8'
    import raven
    RAVEN_CONFIG = {
        'dsn': 'http://e419f1ed03004d03bad7b4b563f74241:12fbfa94d636472d92ae964757627367@sentry.xiaolumm.com/3',
        # If you are using git, you can also automatically configure the
        # release based on the git info.
        'release': raven.fetch_git_sha(os.path.dirname(PROJECT_ROOT)),
    }

if os.environ.get('TARGET') == 'production':
    DEBUG = False
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
            'NAME': 'shopmgr',                      # Or path to database file if using sqlite3.
            'USER': 'qiyue',                      # Not used with sqlite3.
            'PASSWORD': 'youni_2014qy',                  # Not used with sqlite3.
            'HOST': 'jconnfymhz868.mysql.rds.aliyuncs.com',                      # Set to empty string for localhost. Not used with sqlite3. #192.168.0.28
            'PORT': '3306',                      # Set to empty string for default. Not used with sqlite3.
            'OPTIONS':  {'init_command': 'SET storage_engine=Innodb;', 
                         'charset': 'utf8'}, #storage_engine need mysql>5.4,and table_type need mysql<5.4
        }
    }
    CACHES = {
        'default': {
            'BACKEND': 'redis_cache.RedisCache',
            'LOCATION': '55a32ec47c8d41f7.m.cnhza.kvstore.aliyuncs.com:6379',
            'OPTIONS':{
                'DB': 1,
                'PASSWORD': '55a32ec47c8d41f7:Huyiinc12345',
            }
        }
    }    
    BROKER_URL = 'redis://:55a32ec47c8d41f7:Huyiinc12345@55a32ec47c8d41f7.m.cnhza.kvstore.aliyuncs.com:6379/2'

    import raven
    RAVEN_CONFIG = {
        'dsn': 'http://b24693ab54e6461484b277a3668ba383:ec4163971e8a4fdc98dd0a7a90a03201@sentry.xiaolumm.com/2',
        # If you are using git, you can also automatically configure the
        # release based on the git info.
        'release': raven.fetch_git_sha(os.path.dirname(PROJECT_ROOT)),
    }

if not DEBUG:
    TEMPLATE_DEBUG = DEBUG
    ORMCACHE_ENABLE = False
    SESSION_EXPIRE_AT_BROWSER_CLOSE = False  
    SESSION_COOKIE_AGE = 24*15*60*60             

    STATICFILES_DIRS = (
       os.path.join(PROJECT_ROOT,"site_media","static"),
    )
    STATIC_ROOT = "/data/site_media/static"
    M_STATIC_URL = '/'

    ALLOWED_HOSTS = ['.huyi.so','.xiaolu.so','.xiaolumeimei.com','.xiaolumm.com','121.199.168.159']

    #WEB DNS
    SITE_URL = 'http://youni.huyi.so/' 
    #WAP DNS
    M_SITE_URL = 'http://m.xiaolumeimei.com'  
    
    ########################### ONEAPM Statsd ##############################
    STATSD_HOST = '192.168.0.1'
    STATSD_PORT = 8251
    STATSD_CLIENT = 'shopmanager.statsd.oneapm'
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
    #    'shopback.trades.handlers.InterceptHandler',
       'shopback.trades.handlers.RegularSaleHandler',
       'shopback.trades.handlers.FinalHandler',
    #    'shopback.trades.handlers.FlashSaleHandler',
    )
    
    ################### SALEORDER CONFIG ##################
    #sale order regular days
    REGULAR_DAYS = 10
    
    #################### TAOBAO SETTINGS ###################
    #APPKEY = '21532915'   #app name super ERP test ,younixiaoxiao
    #APPSECRET = '7232a740a644ee9ad370b08a1db1cf2d'
    
    APPKEY = '12545735'   #app name guanyi erp ,younishijie
    APPSECRET = '5d845250d49aea44c3a07d8c1d513db5'
    
    TAOBAO_API_HOSTNAME = 'eco.taobao.com'
    AUTHRIZE_URL   = 'https://oauth.taobao.com/authorize'
    AUTHRIZE_TOKEN_URL  = 'https://oauth.taobao.com/token'
    REDIRECT_URI        = '/accounts/login/auth/'
    TAOBAO_API_ENDPOINT = 'https://%s/router/rest'%TAOBAO_API_HOSTNAME
    TAOBAO_NOTIFY_URL   = 'http://stream.api.taobao.com/stream'
    
    SCOPE = 'item,promotion,usergrade'
    REFRESH_URL = 'https://oauth.taobao.com/token'
    
    BASE_FONT_PATH = '/data/fonts/'
    FONT_PATH = '/usr/share/fonts/truetype/ttf-dejavu/DejaVuSerif-Bold.ttf'
    ASYNC_FILE_PATH = os.path.join(PROJECT_ROOT,"site_media","asyncfile")
    
    ################### HTTPS/SSL SETTINGS ##################
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    HTTPS_SUPPORT = False
    SECURE_REQUIRED_PATHS = (
        '/admin/',
    )
    
    ################### WEIXIN SETTINGS ##################
    
    WEIXIN_API_HOST    = "https://api.weixin.qq.com"
    WEIXIN_MEDIA_HOST  = "http://file.api.weixin.qq.com"
    WEIXIN_QRCODE_HOST = "https://mp.weixin.qq.com"
    WEIXIN_AUTHORIZE_URL = "https://open.weixin.qq.com/connect/oauth2/authorize"
    WEIXIN_APPID       = 'wxc2848fa1e1aa94b5'
    WEIXIN_SECRET      = 'bc41b3a535b095afc55cd40d2e808d9c'
    
    WXPAY_APPID    = "wx3f91056a2928ad2d"
    WXPAY_SECRET   = "e8e1f648a5e02492e1584e5413cef158"
    
    WXAPP_ID       = "wx25fcb32689872499"
    WXAPP_SECRET   = "3c7b4e3eb5ae4cfb132b2ac060a872ee"
    
    ################### JINGDONG SETTINGS #################
    
    JD_APP_KEY = 'F9653439C316A32BF49DFFDE8381CBC9'
    JD_APP_SECRET = 'f4fe333676af4f4eaeaa00ed20c82086'
    
    JD_API_HOSTNAME = 'gw.api.360buy.com'
    JD_AUTHRIZE_URL = 'https://auth.360buy.com/oauth/authorize'
    JD_AUTHRIZE_TOKEN_URL = 'https://auth.360buy.com/oauth/token'
    JD_REDIRECT_URI    = '/app/jd/login/auth/'
    JD_API_ENDPOINT = 'http://%s/routerjson'%JD_API_HOSTNAME
    
    ################### PING++ SETTINGS ##################
    
    PINGPP_CLENTIP = "121.199.168.159"
    PINGPP_APPID   = "app_LOOajDn9u9WDjfHa"
    #PINGPP_APPKEY = "sk_test_8y58u9zbPWTKTGGa1GrTi1mT"
    PINGPP_APPKEY  = "sk_live_HOS4OSW10u5CDyrn5Gn9izLC"
    
    ################### Ntalker SETTINGS ##################
    
    NTALKER_NOTIFY_URL = 'http://wx.ntalker.com/agent/weixin'
    WX_MESSAGE_URL = 'https://api.weixin.qq.com/cgi-bin/message/custom/send'
    WX_MEDIA_UPLOAD_URL = 'https://api.weixin.qq.com/cgi-bin/media/upload'
    WX_MEDIA_GET_URL = 'https://api.weixin.qq.com/cgi-bin/media/get'
    
    ################### QINIU SETTINGS ##################
    
    QINIU_ACCESS_KEY = "M7M4hlQTLlz_wa5-rGKaQ2sh8zzTrdY8JNKNtvKN"
    QINIU_SECRET_KEY = "8MkzPO_X7KhYQjINrnxsJ2eq5bsxKU1XmE8oMi4x"
    QINIU_PRIVATE_BUCKET = 'invoiceroom' 
    QINIU_PRIVATE_DOMAIN = '7xrpt3.com2.z0.glb.qiniucdn.com'
    QINIU_PUBLIC_BUCKET = 'xiaolumama'
    QINIU_PUBLIC_DOMAIN = '7xrst8.com2.z0.glb.qiniucdn.com'
    
    LOGGER_HANDLERS = [
        ('shopback','sentry'),
        ('shopapp','sentry'),
        ('flashsale','sentry'),
        ('core','sentry'),
        ('auth','sentry'),
        ('supplychain','sentry'),
        ('models','sentry'),
        ('queryset','sentry'),
        ('django.request','sentry,file'),
        ('sentry.errors','sentry'),
        ('celery.handler','sentry'),
        ('notifyserver.handler','sentry'),
        ('yunda.handler','sentry'),
        ('mail.handler','sentry'),
        ('xhtml2pdf','sentry'),
        ('restapi.errors','sentry'),
        ('weixin.proxy','sentry'),
    ]
    
    LOGGER_TEMPLATE = {
        'handlers': ['sentry'],
        'level': 'DEBUG',
        'propagate': True,
    }
    
    def comb_logger(log_tuple,temp):
        if isinstance(log_tuple,(list,tuple)) and len(log_tuple) == 2:
            temp.update(handlers=log_tuple[1].split(','))
            return log_tuple[0],temp
        return log_tuple[0],temp
    
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
        },
        'handlers': {
            'file': {
                'level': 'DEBUG',
                'class': 'logging.FileHandler',
                'filename': '/tmp/django-debug.log',
                'formatter': 'simple'
            },
            'sentry': {
                'level': 'WARN',
                'class': 'raven.contrib.django.handlers.SentryHandler'
            },
            'console':{
                'level':'DEBUG',
                'class':'logging.StreamHandler',
                'formatter': 'simple'
            },
            'mail_admins': {
                'level': 'INFO',
                'class': 'django.utils.log.AdminEmailHandler',
                'include_html': True,
            }
        },
        'loggers': dict([comb_logger(handler,LOGGER_TEMPLATE.copy()) for handler in LOGGER_HANDLERS]),
    }


try:
    from local_settings import *
except ImportError,err:
    pass

