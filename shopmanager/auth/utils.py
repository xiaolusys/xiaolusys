import hashlib
import base64
import datetime
import time

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


def parse_datetime(dt):
    return datetime.datetime(*(time.strptime(dt, '%Y-%m-%d %H:%M:%S')[0:6]))

def format_datetime(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")