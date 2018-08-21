# coding=utf-8
import qrcode
import cStringIO as StringIO

from .upload import upload_public_to_remote, generate_public_url
from core.utils.image import gen_qrcode_jpeg_iostream

from core.logger import log_consume_time

@log_consume_time
def push_qrcode_to_remote(bucket_path, qrcode_link, box_size=8):
    """ 根据链接生成二维码，上传到第三方，并返回图片链接:
        key: 二维码存储文件名;
        qrlink： 二维码链接内容;
    """
    img_stream = gen_qrcode_jpeg_iostream(qrcode_link, box_size=box_size)
    upload_public_to_remote(bucket_path, img_stream)
    plink = generate_public_url(bucket_path)
    return plink