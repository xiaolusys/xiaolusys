import os
import re
import hashlib
import base64
import datetime
from common.utils import update_model_fields


def group_list(l, block):
    size = len(l)
    return [l[i:i + block] for i in range(0, size, block)]


def getJDSignature(params, secret, both_side=True):
    key_pairs = None

    if type(params) == dict:
        key_pairs = ['%s%s' % (k, v) for k, v in params.iteritems()]
    elif type(params) == list:
        key_pairs = params

    key_pairs.sort()
    if both_side:
        key_pairs.insert(0, secret)
    key_pairs.append(secret)

    md5_value = hashlib.md5(''.join(key_pairs))
    return md5_value.hexdigest().upper()
