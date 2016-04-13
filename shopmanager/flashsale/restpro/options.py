import hashlib


def gen_wxlogin_sha1_sign(params, secret):
    key_pairs = ['%s=%s' % (k, v) for k, v in params.iteritems()]
    key_pairs.append('secret=%s' % secret)
    key_pairs.sort()
    sign_string = '&'.join(key_pairs)
    return hashlib.sha1(sign_string).hexdigest()


import qrcode


def gen_and_save_jpeg_pic(link, file_path_name):
    qr = qrcode.QRCode(version=1, box_size=8, border=1)
    qr.add_data(link)
    qr.make(fit=True)
    x = qr.make_image()

    with open(file_path_name, 'wb') as img_file:
        x.save(img_file, 'JPEG')
