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

def refresh_session(request,settings):

    top_parameters = request.session['top_parameters']
    expires_time = top_parameters['expires_in']
    timestamp = top_parameters['ts']
    if int(expires_time)+int(timestamp) < time.time():
        params = {
            'appkey':settings.APPKEY,
            'refresh_token':top_parameters['refresh_token'],
            'sessionkey':request.session['top_session']
        }
        sign_result = getSignatureTaoBao(params,settings.APPSECRET,both_side=False)
        params['sign'] = sign_result
        refresh_url = '%s?%s'%(settings.REFRESH_URL,urllib.urlencode(params))

        req = urllib2.urlopen(refresh_url)
        content = req.read()
        params = json.loads(content)
        #sign_ret = params.pop('sign',None).strip()
        #sign_val = getSignatureTaoBao(params,settings.APPSECRET,both_side=False).strip()

        #if sign_ret != sign_val:
        #    return False
        request.session['top_session'] = params.get('top_session',None)
        request.session['top_parameters']['re_expires_id'] = params.get('re_expires_id',None)
        request.session['top_parameters']['expires_in'] = params.get('expires_id',None)
        request.session['top_parameters']['refresh_token'] = params.get('refresh_token',None)

    return True


def parse_datetime(dt):
    return datetime.datetime(*(time.strptime(dt, '%Y-%m-%d %H:%M:%S')[0:6]))

def format_datetime(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")