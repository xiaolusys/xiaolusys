# coding: utf-8

from functools import wraps
import requests
import traceback

from django.conf import settings


def mask(bits=0):
    def _wrapper(f):
        @wraps(f)
        def _inner(self, *args, **kwargs):
            n = f(self, *args, **kwargs)
            return n | bits

        return _inner

    return _wrapper


def retry(times=3):
    def _wrapper(f):
        @wraps(f)
        def _inner(self, *args, **kwargs):
            result = {}
            for i in range(times):
                r = f(self, *args, **kwargs)
                if r.status_code == requests.codes.ok:
                    try:
                        result = r.json()
                    except:
                        import traceback
                        traceback.print_exc()
                        continue
                    if settings.DEBUG:
                        print result
                    code = result.get('code', -1)
                    if code:
                        print result
                        continue
                    else:
                        return result
            return result

        return _inner

    return _wrapper
