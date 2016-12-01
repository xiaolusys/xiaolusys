# coding: utf8
from __future__ import absolute_import, unicode_literals

import time
import uuid

def create_signal_message(msg_type, data):
    return {
        "id": uuid.uuid4(),
        "created": time.time(),
        "type": msg_type,
        "data": data,
        "object": "signal",
    }