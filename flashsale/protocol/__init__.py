# coding: utf-8
import urllib

from . import constants

def get_target_url(target_type, params=None, raw=True):
    path = constants.TARGET_PATHS[target_type]
    url = '%s%s' % (constants.TARGET_SCHEMA, path)
    if params:
        qs = urllib.urlencode(params)
        if raw:
            qs = qs.replace('+', '%20')
        url = '%s?%s' % (url, qs)
    return url
