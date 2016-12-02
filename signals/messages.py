# coding: utf8
from __future__ import absolute_import, unicode_literals

import datetime
import uuid

def create_signal_message(msg_type, data):
    return {
        "id": uuid.uuid4(),
        "created": datetime.datetime.now(),
        "type": msg_type,
        "data": data,
        "object": "signal",
    }