# coding: utf-8

from functools import wraps
import json
import traceback

from django.http import HttpResponse

def jsonapi(f):
    @wraps(f)
    def _wrapper(*args, **kwargs):
        try:
            r = f(*args, **kwargs)
        except Exception, e:
            r = {'code': 1, 'msg': '%s, Traceback: %s' % (e, traceback.print_exc())}
        return HttpResponse(json.dumps(r), content_type='application/json')
    return _wrapper
