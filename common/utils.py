# coding: utf-8

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
import urlparse

from taskutils import single_instance_task
from modelutils import update_model_fields
from xmlutils import xml2dict
from csvutils import gen_cvs_tuple, CSVUnicodeWriter
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
from .processlock import Lock, process_lock
from .cachelock import cache_lock

BASE_STRING = 'abcdefghijklmnopqrstuvwxyz1234567890-'
REGEX_INVALID_XML_CHAR = r'$><^;\&\[\]\?\!\"\:'


def parse_urlparams(string):
    query = urlparse.urlparse(string).query
    return dict([(k, v[0]) for k, v in urlparse.parse_qs(query).items()])


def valid_xml_string(xml_str):
    return re.sub(REGEX_INVALID_XML_CHAR, '*', xml_str)


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


def year_month_range(sdate, tdate):
    """ 计算两个日期之间年月组合列表 """
    syear, smonth = sdate.year, sdate.month
    eyear, emonth = tdate.year, tdate.month
    month_range = []
    for syear in range(syear, eyear + 1):
        for smonth in range(smonth, 13):
            if syear > eyear or (syear == eyear and smonth > emonth):
                break
            month_range.append((syear, smonth))
        smonth = 1
    return month_range


def pinghost(hostid):
    try:
        pingurl = 'ping %s -c 2' % hostid
        ret = os.system(pingurl)
    except:
        ret = -1
    return ret


def valid_mobile(m):
    if not m or m == '':
        return False
    rg = re.compile('^1[34578][0-9]{9}$')
    return rg.match(m) and True or False


def group_list(l, block):
    size = len(l)
    return [l[i:i + block] for i in range(0, size, block)]


def randomString():
    return ''.join(random.sample(list(BASE_STRING), 10))


def replace_utf8mb4(v):
    """Replace 4-byte unicode characters by REPLACEMENT CHARACTER"""
    import re
    INVALID_UTF8_RE = re.compile(u'[^\u0000-\uD7FF\uE000-\uFFFF]', re.UNICODE)
    return INVALID_UTF8_RE.sub(u'*', v)


def url_utf8_quote(link):
    """ quote url utf-8 chars  """
    req_http = link[:link.find(':')]
    link_tuple = link[link.find(':') + 1:].split('?')
    if len(link_tuple) == 1:
        return '%s:%s' % (req_http, urllib.quote(link_tuple[0]))
    link_params = link_tuple[1]
    if link_params.find('=') > -1:
        encode_params = parse_urlparams(link)
        link_params = urllib.urlencode(encode_params)
    return '%s:%s?%s' % (req_http, urllib.quote(link_tuple[0]), link_params)


def get_timestr(dt, now=datetime.datetime.now()):
    ONE_DAY_LATER = dt + datetime.timedelta(days=1)
    ONE_HOUR_LATER = dt + datetime.timedelta(hours=1)
    ONE_MINUTE_LATER = dt + datetime.timedelta(minutes=1)
    TEN_SECONDS_LATER = dt + datetime.timedelta(seconds=10)

    if now > ONE_DAY_LATER:
        return dt.strftime('%Y%m%d %H:%M:%S')
    elif now > ONE_HOUR_LATER:
        return '%d小时前' % ((now - dt).seconds / 3600)
    elif now > ONE_MINUTE_LATER:
        return '%d分钟前' % ((now - dt).seconds / 60)
    elif now > TEN_SECONDS_LATER:
        return '%d秒前' % (now - dt).seconds
    else:
        return '刚刚'


def get_admin_name(user):
    last_name = user.last_name
    first_name = user.first_name
    if len(last_name) > 1:
        names = [first_name, last_name]
    else:
        names = [last_name, first_name]
    return ''.join(filter(None, names)) or user.username
