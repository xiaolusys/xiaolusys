# coding=utf-8
from django.conf import settings

from qiniu import Auth, put_file, put_data, etag, urlsafe_base64_encode
import qiniu.config

def upload_data_to_remote(filepath, iostream):
    """ 上传私有文件到第三方 """
    #需要填写你的 Access Key 和 Secret Key
    access_key = str(settings.QINIU_ACCESS_KEY)
    secret_key = str(settings.QINIU_SECRET_KEY)
    filepath   = str(filepath)
    #要上传的空间
    bucket_name = str(settings.QINIU_PRIVATE_BUCKET)

    #构建鉴权对象
    q = Auth(access_key, secret_key)

    #生成上传 Token，可以指定过期时间等
    token = q.upload_token(bucket_name, filepath, 3600)

    ret, info = put_data(token, filepath, iostream)

    return info

def upload_public_to_remote(filepath, iostream):
    """ 上传公开文件到第三方 """
    #需要填写你的 Access Key 和 Secret Key
    access_key = str(settings.QINIU_ACCESS_KEY)
    secret_key = str(settings.QINIU_SECRET_KEY)
    filepath   = str(filepath)
    #要上传的空间
    bucket_name = str(settings.QINIU_BUCKET_NAME)

    #构建鉴权对象
    q = Auth(access_key, secret_key)

    #生成上传 Token，可以指定过期时间等
    token = q.upload_token(bucket_name, filepath)

    ret, info = put_data(token, filepath, iostream)

    return info



def generate_private_url(filepath):

    access_key = str(settings.QINIU_ACCESS_KEY)
    secret_key = str(settings.QINIU_SECRET_KEY)
    filepath = str(filepath)
    bucket_domain = str(settings.QINIU_PRIVATE_DOMAIN)

    q = Auth(access_key, secret_key)

    #有两种方式构造base_url的形式
    base_url = 'http://%s/%s' % (bucket_domain, filepath)

    #可以设置token过期时间
    private_url = q.private_download_url(base_url, expires=3600)

    return private_url

def generate_public_url(filepath):

    bucket_domain = settings.QINIU_BUCKET_DOMAIN
    #有两种方式构造base_url的形式
    base_url = 'http://%s/%s' % (bucket_domain, filepath)

    return base_url



