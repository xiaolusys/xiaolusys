# coding:utf-8
import qrcode
import cStringIO as StringIO

def gen_and_save_jpeg_pic(link, file_path_name):
    """ 生成本地二维码图片 """
    qr = qrcode.QRCode(version=1, box_size=8, border=1)
    qr.add_data(link)
    qr.make(fit=True)
    x = qr.make_image()

    with open(file_path_name, 'wb') as img_file:
        x.save(img_file, 'JPEG')

def gen_qrcode_jpeg_iostream(qrcode_link, box_size=8):
    qr = qrcode.QRCode(version=1, box_size=box_size, border=1)
    qr.add_data(qrcode_link)
    qr.make(fit=True)
    x = qr.make_image()
    result = StringIO.StringIO()
    x.save(result, 'JPEG')
    return StringIO.StringIO(result.getvalue())