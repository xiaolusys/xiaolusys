# coding:utf-8
from __future__ import unicode_literals

import os
import sys
import urllib2

TARGET = os.environ.get('TARGET')

def is_undeploy_enviroment():
    """　是否非正式环境 """
    return TARGET not in ('production', 'django18', 'k8s-production')

def is_staging_environment():
    return TARGET in ('staging', 'k8s')

def setup_djagno_environ():
    if TARGET in ('production',):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.production")

    elif TARGET in ('django18',):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.django18")

    elif TARGET in ('staging',):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.staging")

    elif TARGET in ('k8s',):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.staging")

    elif TARGET in ('k8s-production',):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.production")

    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.local_settings")


def install_pymysqldb():
    if not TARGET in ('production', 'django18', 'staging', 'k8s', 'k8s-production'):
        return
    try:
        import pymysql
        pymysql.install_as_MySQLdb()
    except ImportError:
        print 'pymysql module not found'


def install_redis_with_gevent_socket():
    if not TARGET in ('production', 'django18', 'staging', 'k8s', 'k8s-production'):
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




