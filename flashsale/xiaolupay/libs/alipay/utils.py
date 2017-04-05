# coding: utf8
from __future__ import absolute_import, unicode_literals

import os
from urllib import quote
import six

def encode_dict(params):
    return {k: six.u(v).encode('utf-8')
            if isinstance(v, str) else v.encode('utf-8')
            if isinstance(v, six.string_types) else v
            for k, v in six.iteritems(params)}

def serial_dict(params, value_quote=False):
    sign_params = []
    for k, v in sorted(params.iteritems()):
        if value_quote:
            v = quote(v)
        sign_params.append('%s=%s' % (k, v))
    sign_content = '&'.join(sign_params)
    return sign_content
