# coding:utf-8
import qrcode
import cStringIO as StringIO
print qrcode.__file__
def gen_and_save_jpeg_pic(link,file_path_name):
    """ 生成本地二维码图片 """
    qr = qrcode.QRCode(version=1, box_size=8, border=1)
    qr.add_data(link)
    qr.make(fit=True)
    x = qr.make_image()
    
    with open(file_path_name, 'wb') as img_file:
        x.save(img_file, 'JPEG')

from .upload import upload_public_to_remote, generate_public_url

def push_qrcode_to_remote(key,qrlink):
    """ 根据链接生成二维码，上传到第三方，并返回图片链接 """
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