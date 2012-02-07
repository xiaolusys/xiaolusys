import hashlib
import base64
import urllib
import urllib2
import datetime
import time
import json


def getSignatureTaoBao(params,secret,both_side=True):
    key_pairs = None

    if type(params) == dict:
        key_pairs = ['%s%s'%(k,v) for k,v in params.iteritems()]
    elif type(params) == list:
        key_pairs = params

    key_pairs.sort()
    if both_side:
        key_pairs.insert(0,secret)
    key_pairs.append(secret)

    md5_value = hashlib.md5(''.join(key_pairs))
    return md5_value.hexdigest().upper()

def verifySignature(string,sign):

    str_sign = base64.encodestring(hashlib.md5(string).digest()).strip()

    return str_sign == sign

def decodeBase64String(string):

    return base64.decodestring(string)


def parse_urlparams(string):

    arr = string.split('&')
    map = dict([(s.split('=')[0],s.split('=')[1]) for s in arr if s.find('=')>0])

    return map

def refresh_session(session,settings):

    top_parameters = session['top_parameters']
    expires_time = top_parameters['expires_in']
    timestamp = top_parameters['ts']

    if int(expires_time)+int(timestamp) < time.time():
        params = {
            'appkey':settings.APPKEY,
            'refresh_token':top_parameters['refresh_token'],
            'sessionkey':session['top_session']
        }
        sign_result = getSignatureTaoBao(params,settings.APPSECRET,both_side=False)
        params['sign'] = sign_result
        refresh_url = '%s?%s'%(settings.REFRESH_URL,urllib.urlencode(params))

        req = urllib2.urlopen(refresh_url)
        content = req.read()
        params = json.loads(content)

        session['top_session'] = params.get['top_session']
        session['top_parameters']['re_expires_id'] = params['re_expires_id']
        session['top_parameters']['expires_in'] = params['expires_id']
        session['top_parameters']['refresh_token'] = params['refresh_token']
        return True

    return False


def parse_datetime(dt):
    return datetime.datetime(*(time.strptime(dt, '%Y-%m-%d %H:%M:%S')[0:6]))

def format_datetime(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def get_all_time_slots():
    return {"11:50":0, "12:20":1, "14:50":2, "15:20":3, "15:50":4,
            "16:20":5, "16:50":6, "21:00":7, "21:30":8, "22:00":9}

def get_closest_time_slot(t):
    y,m,d = t.year, t.month, t.day
    slots = [datetime.datetime(y,m,d, 11, 50),
             datetime.datetime(y,m,d, 12, 20),
             datetime.datetime(y,m,d, 14, 50),
             datetime.datetime(y,m,d, 15, 20),
             datetime.datetime(y,m,d, 15, 50),
             datetime.datetime(y,m,d, 16, 20),
             datetime.datetime(y,m,d, 16, 50),
             datetime.datetime(y,m,d, 21, 0),
             datetime.datetime(y,m,d, 21, 30),
             datetime.datetime(y,m,d, 22, 0)]
    for x in slots:
        if t > x - datetime.timedelta(minutes=10) and t < x + datetime.timedelta(minutes=10):
            return x, False
        if t < x:
            return x, True

    t += datetime.timedelta(days=1)
    return datetime.datetime(t.year(), t.month(), t.day(), 11, 50)
