__author__ = 'zfz'

import os

DEBUG = False
TEMPLATE_DEBUG = DEBUG

SESSION_EXPIRE_AT_BROWSER_CLOSE = False  
SESSION_COOKIE_AGE = 12*60*60             

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'shopmgr',                      # Or path to database file if using sqlite3.
        'USER': 'meixqhi',                      # Not used with sqlite3.
        'PASSWORD': '123123',                  # Not used with sqlite3.
        'HOST': '192.168.0.28',                      # Set to empty string for localhost. Not used with sqlite3. #192.168.0.28
        'PORT': '3306',                      # Set to empty string for default. Not used with sqlite3.
        'OPTIONS':  { 'init_command': 'SET storage_engine=MyISAM;', 'charset': 'utf8'}, #storage_engine need mysql>5.4,and table_type need mysql<5.4
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
    'dsn': 'http://43c3e070137d4d0384bafe98b55d1d31:fc1f5d35403f4d09816925115324bfdb@sentry.huyi.so/2',
    'register_signals': True,
}


SITE_URL = 'http://qiyue.f3322.org/' 


#APPKEY = '21532915'   #app name super ERP test ,younixiaoxiao
#APPSECRET = '7232a740a644ee9ad370b08a1db1cf2d'

APPKEY = '12545735'   #app name guanyi erp ,younishijie
APPSECRET = '2b966d4f5f05d201a48a75fe8b5251af'

TAOBAO_API_HOSTNAME = 'eco.taobao.com'
AUTHRIZE_URL   = 'https://oauth.taobao.com/authorize'
AUTHRIZE_TOKEN_URL = 'https://oauth.taobao.com/token'
REDIRECT_URI = ''.join([SITE_URL,'accounts/login/auth/'])
TAOBAO_API_ENDPOINT = 'https://%s/router/rest'%TAOBAO_API_HOSTNAME
TAOBAO_NOTIFY_URL   = 'http://stream.api.taobao.com/stream'


SCOPE = 'item,promotion,usergrade'
REFRESH_URL = 'https://oauth.taobao.com/token'

FONT_PATH = '/usr/share/fonts/truetype/ttf-dejavu/DejaVuSerif-Bold.ttf'
ASYNC_FILE_PATH = '/home/user1/deploy/taobao/site_media/asyncfile'

