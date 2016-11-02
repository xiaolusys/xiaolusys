# -*- encoding: utf-8 -*-
import barcode
from barcode.writer import ImageWriter
from StringIO import StringIO
from barcode import generate


# 参考：https://pypi.python.org/pypi/pyBarcode/0.7
def createbar_code39(code):
    EAN = barcode.get_barcode_class('code39')

    ean = EAN(code, writer=ImageWriter())

    fullname = ean.save(code)
    fp = StringIO()
    ean.write(fp)
    return fullname


from PIL import Image
from io import BytesIO
from StringIO import StringIO
import base64
from hubarcode.code128 import Code128Encoder


# 错误：The _imaging extension was built for another  version of Pillow or PIL
# 错误解决：http://www.cnblogs.com/Mingxx/p/3646393.html，http://jinvan.com/post/install-pil-on-ubuntu，http://www.redicecn.com/html/Linux/20120425/395.html
# 创建条码
def createbar_code128(code):
    # 1 生成条形码
    text = code.upper()

    encoder = Code128Encoder(text, options={"ttf_font": "/home/timi06/timi/fonts/simsun.ttf", "ttf_fontsize": 15,
                                            "bottom_border": 1, "height": 99, "label_border": 1})
    fs = StringIO()
    encoder.save(fs)

    # 参考资料：http://ju.outofmemory.cn/entry/53301,http://firehuman.blog.163.com/blog/static/57331120105260736902/
    pngraw = fs.getvalue()
    fs.close()

    bs = StringIO()
    imgo = Image.open(BytesIO(pngraw))
    imgo.save(bs, 'jpeg')
    bss = bs.getvalue()
    imgbase64 = base64.b64encode(bss)
    bs.close()
    return imgbase64


import qrcode


# 生成二维码
def two_dimension_code(text):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image()
    fs = StringIO()
    img.save(fs, 'jpeg')
    t = fs.getvalue()
    imgbase = base64.b64encode(t)
    fs.close()

    # bs = StringIO()
    # imgo = Image.open(BytesIO(t))
    # imgo.save(bs,'jpeg')
    # bss = bs.getvalue()
    # imgbase = base64.b64encode(bss)
    # bs.close()


    return imgbase


if __name__ == "__main__":
    print createbar_code128(1)
