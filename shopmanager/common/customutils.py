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


def verifySignature(string, sign):
    str_sign = base64.encodestring(hashlib.md5(string).digest()).strip()
    return str_sign == sign


def decodeBase64String(string):
    return base64.decodestring(string)


def getSignatureTaoBao(params, secret, both_side=True):
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


def refresh_session(user, appkey, appsecret, refresh_url):
    top_parameters = json.loads(user.top_parameters)
    expires_in = top_parameters['expires_in']
    ts = top_parameters['ts']
    expire_time = int(expires_in) + ts - 10 * 60
    if expire_time < time.time():
        import logging
        from django.conf import settings
        logger = logging.getLogger("django.request")
        try:
            params = {
                'client_id': appkey,
                'client_secret': appsecret,
                'grant_type': 'refresh_token',
                'refresh_token': top_parameters['refresh_token'],
                'scope': settings.SCOPE,
                'state': 'autolist',
                'view': 'web',
            }
            req = urllib2.urlopen(refresh_url, urllib.urlencode(params))
            content = req.read()
            logger.warn('refreshed token : %s' % content)
            params = json.loads(content)
            user.top_session = params['access_token']
            params['ts'] = time.time()
            user.top_parameters = json.dumps(params)
            user.save()
            return True
        except Exception, exc:
            logger.error('refreshed token error: %s' % exc, exc_info=True)

    return False


def get_yesterday_interval_time():
    dt = datetime.datetime.now() - datetime.timedelta(1, 0, 0)
    year = dt.year
    month = dt.month
    day = dt.day
    st_f = datetime.datetime(year, month, day, 0, 0, 0)
    st_t = datetime.datetime(year, month, day, 23, 59, 59)
    return st_f, st_t


def get_all_time_slots():
    return {"11:50": 0, "12:20": 1, "14:50": 2, "15:20": 3, "15:50": 4,
            "16:20": 5, "16:50": 6, "21:00": 7, "21:30": 8, "22:00": 9}


def get_closest_time_slot(t):
    y, m, d = t.year, t.month, t.day
    slots = [datetime.datetime(y, m, d, 11, 50),
             datetime.datetime(y, m, d, 12, 20),
             datetime.datetime(y, m, d, 14, 50),
             datetime.datetime(y, m, d, 15, 20),
             datetime.datetime(y, m, d, 15, 50),
             datetime.datetime(y, m, d, 16, 20),
             datetime.datetime(y, m, d, 16, 50),
             datetime.datetime(y, m, d, 21, 0),
             datetime.datetime(y, m, d, 21, 30),
             datetime.datetime(y, m, d, 22, 0)]
    for x in slots:
        if t > x - datetime.timedelta(minutes=10) and t < x + datetime.timedelta(minutes=10):
            return x, False
        if t < x:
            return x, True

    t += datetime.timedelta(days=1)
    return datetime.datetime(t.year, t.month, t.day, 11, 50), True


def map_int2str(*t):
    names = {0: '0', 1: '01', 2: '02', 3: '03', 4: '04',
             5: '05', 6: '06', 7: '07', 8: '08', 9: '09'}
    num = t[0]
    l = list(num)
    ret = []
    for s in l:
        if int(s) < 10:
            s = names[int(s)]
        ret.append(s)
    return tuple(ret)


def gen_string_image(font_path, code_string):
    """
    gen string image
    """
    import Image
    import ImageDraw
    import ImageFont

    im = Image.new("RGB", (75, 24), "#ddd")
    draw = ImageDraw.Draw(im)
    sans16 = ImageFont.truetype(font_path, 16)

    for index, string in enumerate(code_string):
        draw.text((10 * (index + 1), 0), string, font=sans16, fill='red')

    del draw

    buf = cStringIO.StringIO()
    im.save(buf, 'png')

    return buf.getvalue()


######################## WEIXIN utils ########################

def getSignatureWeixin(params):
    key_pairs = None

    if type(params) == dict:
        key_pairs = ['%s=%s' % (k.lower(), v) for k, v in params.iteritems()]
    elif type(params) == list:
        key_pairs = params

    key_pairs.sort()

    sha1_value = hashlib.sha1('&'.join(key_pairs))
    return sha1_value.hexdigest()
