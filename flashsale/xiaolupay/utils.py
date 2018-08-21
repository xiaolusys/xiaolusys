# coding: utf8
from __future__ import absolute_import, unicode_literals

import time
import random
STRINGS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'

def genNonceStr():
    return ''.join(random.sample(list(STRINGS), 20))


def get_time_number():
    return int(time.time())