# coding:utf-8
import qrcode

def gen_and_save_jpeg_pic(link,file_path_name):
    """ 生成本地二维码图片 """
    qr = qrcode.QRCode(version=1, box_size=8, border=1)
    qr.add_data(link)
    qr.make(fit=True)
    x = qr.make_image()

    with open(file_path_name, 'wb') as img_file:
        x.save(img_file, 'JPEG')