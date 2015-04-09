__author__ = 'zfz'

import os

DEBUG = False
TEMPLATE_DEBUG = DEBUG

SESSION_EXPIRE_AT_BROWSER_CLOSE = False  
SESSION_COOKIE_AGE = 48*60*60             

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'shopmgr',                      # Or path to database file if using sqlite3.
        'USER': 'qiyue',                      # Not used with sqlite3.
        'PASSWORD': 'youni_2014qy',                  # Not used with sqlite3.
        'HOST': 'jconnfymhz868.mysql.rds.aliyuncs.com',                      # Set to empty string for localhost. Not used with sqlite3. #192.168.0.28
        'PORT': '3306',                      # Set to empty string for default. Not used with sqlite3.
        'OPTIONS':  {'init_command': 'SET storage_engine=MyISAM;', 
                     'charset': 'utf8'}, #storage_engine need mysql>5.4,and table_type need mysql<5.4
    }
}

if DEBUG:
    STATICFILES_DIRS = (
       os.path.join(PROJECT_ROOT,"site_media","static"),
    )
else :
    STATIC_ROOT = os.path.join(PROJECT_ROOT,"site_media","static")



CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}
    
RAVEN_CONFIG = {
    'dsn': 'http://53382bea24ca4a1f851f1e627a8dc0a1:0c2de1f22e884835a32d1fa396487101@sentry.huyi.so:8089/10',
    'register_signals': True,
}


SITE_URL = 'http://youni.huyi.so/' 

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
   'shopback.trades.handlers.RegularSaleHandler',
   'shopback.trades.handlers.FinalHandler',
)


#################### TAOBAO SETTINGS ###################
#APPKEY = '21532915'   #app name super ERP test ,younixiaoxiao
#APPSECRET = '7232a740a644ee9ad370b08a1db1cf2d'

APPKEY = '12545735'   #app name guanyi erp ,younishijie
APPSECRET = '2b966d4f5f05d201a48a75fe8b5251af'

TAOBAO_API_HOSTNAME = 'eco.taobao.com'
AUTHRIZE_URL   = 'https://oauth.taobao.com/authorize'
AUTHRIZE_TOKEN_URL  = 'https://oauth.taobao.com/token'
REDIRECT_URI        = '/accounts/login/auth/'
TAOBAO_API_ENDPOINT = 'https://%s/router/rest'%TAOBAO_API_HOSTNAME
TAOBAO_NOTIFY_URL   = 'http://stream.api.taobao.com/stream'

SCOPE = 'item,promotion,usergrade'
REFRESH_URL = 'https://oauth.taobao.com/token'


FONT_PATH = '/usr/share/fonts/truetype/ttf-dejavu/DejaVuSerif-Bold.ttf'
ASYNC_FILE_PATH = os.path.join(PROJECT_ROOT,"site_media","asyncfile")

################### HTTPS/SSL SETTINGS ##################
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
HTTPS_SUPPORT = True
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

################### JINGDONG SETTINGS #################

JD_APP_KEY = 'F9653439C316A32BF49DFFDE8381CBC9'
JD_APP_SECRET = 'f4fe333676af4f4eaeaa00ed20c82086'

JD_API_HOSTNAME = 'gw.api.360buy.com'
JD_AUTHRIZE_URL = 'https://auth.360buy.com/oauth/authorize'
JD_AUTHRIZE_TOKEN_URL = 'https://auth.360buy.com/oauth/token'
JD_REDIRECT_URI    = '/app/jd/login/auth/'
JD_API_ENDPOINT = 'http://%s/routerjson'%JD_API_HOSTNAME

################### PING++ SETTINGS ##################
WXPAY_APPID    = "wx3f91056a2928ad2d"
WXPAY_SECRET   = "726f44ea3e5f077dd4b93e03e3c4b096"

PINGPP_CLENTIP = "121.199.168.159"
PINGPP_APPID   = "app_LOOajDn9u9WDjfHa"
#PINGPP_APPKEY = "sk_test_8y58u9zbPWTKTGGa1GrTi1mT"
PINGPP_APPKEY  = "sk_live_HOS4OSW10u5CDyrn5Gn9izLC" 
