#!/usr/bin/python
"""WSGI server example"""
from gevent import monkey
monkey.patch_all()

from __future__ import print_function
from gevent.pywsgi import WSGIServer
from shopmanager.wsgi import application

from global_setup import install_redis_with_gevent_socket

install_redis_with_gevent_socket()

if __name__ == '__main__':
    print('Serving on 9000...')
    WSGIServer(('', 9000), application).serve_forever()
