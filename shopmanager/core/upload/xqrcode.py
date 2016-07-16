# coding:utf-8
import qrcode
import cStringIO as StringIO

from .upload import upload_public_to_remote, generate_public_url

def push_qrcode_to_remote(key, qrlink):
    """ 根据链接生成二维码，上传到第三方，并返回图片链接:
        key: 二维码存储文件名;
        qrlink： 二维码链接内容;
    """
    qr = qrcode.QRCode(version=1, box_size=8, border=1)
    qr.add_data(qrlink)
    qr.make(fit=True)
    x = qr.make_image()
    result = StringIO.StringIO()
    x.save(result, 'JPEG')
    img_stream = StringIO.StringIO(result.getvalue())
    upload_public_to_remote(key, img_stream)
    plink = generate_public_url(key)
    return plink