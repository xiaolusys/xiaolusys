import hashlib


def gen_wxlogin_sha1_sign(params, secret):
    key_pairs = ['%s=%s' % (k, v) for k, v in params.iteritems()]
    key_pairs.append('secret=%s' % secret)
    key_pairs.sort()
    sign_string = '&'.join(key_pairs)
    return hashlib.sha1(sign_string).hexdigest()


