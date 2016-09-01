import os
import urllib2

def setup_djagno_environ():
    if os.environ.get('TARGET') in ('production', 'django18'):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.production")

    elif os.environ.get('TARGET') in ('staging',):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.staging")

    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.local_settings")


def install_pymysqldb():
    try:
        import pymysql
        pymysql.install_as_MySQLdb()
    except ImportError:
        print 'pymysql module not found'


def install_redis_with_gevent_socket():
    try:
        from gevent import socket
    except ImportError:
        print 'gevent module not found'
        return
    try:
        import redis.connection
        redis.connection.socket = socket
    except ImportError:
        print 'redis.connection module not found'


def enable_urllib2_debugmode():
    httpHandler = urllib2.HTTPHandler(debuglevel=1)
    httpsHandler = urllib2.HTTPSHandler(debuglevel=1)
    opener = urllib2.build_opener(httpHandler, httpsHandler)

    urllib2.install_opener(opener)

