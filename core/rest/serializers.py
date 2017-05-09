# coding: utf8
from __future__ import absolute_import, unicode_literals

import datetime
import decimal
import json
import sys
import uuid

from django.utils import six
from django.utils.functional import Promise
from django.utils.timezone import is_aware

class RestApiJSONEncoder(json.JSONEncoder):
    """
    JSONEncoder subclass that knows how to encode date/time, decimal types and UUIDs.
    """
    def default(self, o):
        # See "Date Time String Format" in the ECMA-262 specification.
        if isinstance(o, datetime.datetime):
            r = o.isoformat()[:19]
            return r
        elif isinstance(o, datetime.date):
            return o.isoformat()
        elif isinstance(o, datetime.time):
            if is_aware(o):
                raise ValueError("JSON can't represent timezone-aware times.")
            r = o.isoformat()
            if o.microsecond:
                r = r[:12]
            return r
        elif isinstance(o, decimal.Decimal):
            return str(o)
        elif isinstance(o, uuid.UUID):
            return str(o)
        elif isinstance(o, Promise):
            return six.text_type(o)
        else:
            return super(RestApiJSONEncoder, self).default(o)

