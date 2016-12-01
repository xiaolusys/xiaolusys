# coding:utf-8
from __future__ import unicode_literals

import os
import sys
import urllib2

TARGET = os.environ.get('TARGET')

def is_staging_environment():
    return TARGET == 'staging'

def setup_djagno_environ():
    if TARGET in ('production',):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.production")

    elif TARGET in ('django18',):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.django18")

    elif TARGET in ('staging',):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.staging")

    elif TARGET in ('prometheus',):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.prometheus")

    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.local_settings")


def install_pymysqldb():
    if not TARGET in ('production', 'django18', 'staging', 'prometheus'):
        return
    try:
        import pymysql
        pymysql.install_as_MySQLdb()
    except ImportError:
        print 'pymysql module not found'


def install_redis_with_gevent_socket():
    if not TARGET in ('production', 'django18', 'staging', 'prometheus'):
        return
    try:
        from gevent import socket
        import redis.connection
        redis.connection.socket = socket
    except ImportError:
        print 'gevent or redis.connection module not found'


def enable_urllib2_debugmode():
    httpHandler = urllib2.HTTPHandler(debuglevel=1)
    httpsHandler = urllib2.HTTPSHandler(debuglevel=1)
    opener = urllib2.build_opener(httpHandler, httpsHandler)

    urllib2.install_opener(opener)

def cancel_pingpp_charge_ssl_verify():
    try:
        import pingpp
        pingpp.verify_ssl_certs = False
    except Exception, exc:
        print 'cancel pingpp verify error:%s'% exc

def patch_redis_compat_nativestr():
    if sys.version_info[0] < 3:
        def _nativestr(x):
            if isinstance(x, str):
                return x
            if isinstance(x, (list, tuple)):
                return '%s' % x
            return x.encode('utf-8', 'replace')

        from redis import _compat
        _compat.nativestr = _nativestr



