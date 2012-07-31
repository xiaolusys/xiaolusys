__author__ = 'zfz'

import os

DEBUG = False
TEMPLATE_DEBUG = DEBUG

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
STATICFILES_DIRS = ()
STATIC_ROOT = os.path.join(PROJECT_ROOT, "site_media","static")

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

SITE_URL = 'http://autolist.huyi.so/'

APPKEY = '12686908'
APPSECRET = 'b3ddef5982a23c636739289949c01f59'
#APPKEY = '21072630'
#APPSECRET  = '6e9e3a028202d91395820d477162385a'

AUTHRIZE_URL = 'https://oauth.taobao.com/authorize'
AUTHRIZE_TOKEN_URL = 'https://oauth.taobao.com/token'
REDIRECT_URI = 'http://autolist.huyi.so/accounts/login/taobao/'
TAOBAO_API_ENDPOINT = 'https://eco.taobao.com/router/rest'

SCOPE = 'item,promotion,usergrade'
REFRESH_URL = 'https://oauth.taobao.com/token'

FONT_PATH = '/usr/share/fonts/truetype/ttf-dejavu/DejaVuSerif-Bold.ttf'