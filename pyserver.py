#!/usr/bin/python
"""WSGI server example"""
from __future__ import print_function
from gevent.pywsgi import WSGIServer
from shopmanager.wsgi import application


if __name__ == '__main__':
    print('Serving on 9000...')
    WSGIServer(('', 9000), application).serve_forever()
