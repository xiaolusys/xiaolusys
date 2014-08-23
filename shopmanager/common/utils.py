import os
import re
import hashlib
import base64
import datetime
import time
import json
import urllib
import urllib2
import decimal
import random
import cStringIO


from taskutils  import single_instance_task
from modelutils import update_model_fields
from csvutils   import gen_cvs_tuple,CSVUnicodeWriter
from .customutils import (verifySignature,
                      decodeBase64String,
                      getSignatureTaoBao,
                      getSignatureWeixin,
                      refresh_session,
                      get_yesterday_interval_time,
                      get_all_time_slots,
                      get_closest_time_slot,
                      map_int2str,
                      gen_string_image)

BASE_STRING = 'abcdefghijklmnopqrstuvwxyz1234567890-'
REGEX_INVALID_XML_CHAR = r'$><^;\&\[\]\?\!\"\:'

def parse_urlparams(string):
    arr = string.split('&')
    map = dict([(s.split('=')[0],s.split('=')[1]) for s in arr if s.find('=')>0])
    return map

def valid_xml_string(xml_str):
    return re.sub(REGEX_INVALID_XML_CHAR,'*',xml_str)


def parse_datetime(dt):
    return datetime.datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')

def parse_date(dt):
    return datetime.datetime.strptime(dt, '%Y-%m-%d')

def format_datetime(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def format_date(dt):
    return dt.strftime("%Y-%m-%d")

def format_year_month(dt):
    return dt.strftime("%Y-%m")

def format_time(dt):
    return dt.strftime("%H:%M")

def unquote(text):
        def unicode_unquoter(match):
            return unichr(int(match.group(1),16))
        return re.sub(r'%5Cu([0-9a-fA-F]{4})',unicode_unquoter,text)

def pinghost(hostid):
    try:
        pingurl = 'ping %s -c 2'%hostid
        ret = os.system(pingurl)
    except:
        ret = -1
    return ret

def valid_mobile(m):
    rg = re.compile('^1[3458][0-9]{9}$')
    return rg.match(m)

def group_list(l,block):
    size = len(l)
    return [l[i:i+block] for i in range(0,size,block)]

def randomString():
    return ''.join(random.sample(list(BASE_STRING),10))

def replace_utf8mb4(v):
    """Replace 4-byte unicode characters by REPLACEMENT CHARACTER"""
    import re
    INVALID_UTF8_RE = re.compile(u'[^\u0000-\uD7FF\uE000-\uFFFF]', re.UNICODE)
    return INVALID_UTF8_RE.sub(u'\uFFFD', v)
