# coding: utf8
from __future__ import absolute_import, unicode_literals


def make_response(info='error', code=1, extra={}):
    res = {
        'code': code,
        'info': info,
    }
    res.update(extra)
    return res


def success_response(info, extra={}):
    res = {
        'code': 0,
        'info': info,
    }
    res.update(extra)
    return res


SUCCESS_RESPONSE = make_response(info='SUCCESS', code=0)



