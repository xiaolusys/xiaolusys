# coding: utf8
import re
import time
import base64
import urllib
from django.conf import settings
from django.core.cache import cache
import cStringIO as StringIO

from flashsale.xiaolumm.models import XiaoluMama
from shopapp.weixin.weixin_apis import WeiXinAPI
from core.upload import push_qrcode_to_remote
from core.logger import log_consume_time

import logging
logger = logging.getLogger(__name__)

DEFAULT_MAMA_THUMBNAIL = 'http://img.xiaolumeimei.com/undefined1472268058597lADOa301H8zIzMg_200_200.jpg_620x10000q90g.jpg?imageMogr2/thumbnail/80/crop/80x80/format/jpg'
BASE_MAMA_QRCODE_IMG_RUL = 'http://img.xiaolumeimei.com/MG_1472464661562-2-.jpg'
BASE_MAMA_QRCODE_TEMPLATE_URL = """
    {base_url}?imageView2/1/w/289/h/293/q/100/
    |watermark/3/text/5bCP6bm/{message}/font/5a6L5L2T/fontsize/10/gravity/NorthEast/dx/10/dy/10
    /image/{thumbnail}/dissolve/100/gravity/NorthWest/dx/10/dy/10
    /image/{qrcode}/dissolve/100/gravity/SouthEast/dx/10/dy/10/""".replace('\n','').replace(' ','')

def get_mama_customer(mama_id):
    mama = XiaoluMama.objects.filter(id=mama_id).first()
    return mama.get_customer()

@log_consume_time
def gen_mama_custom_qrcode_url(mama_id, thumbnail, message=''):
    wx_api = WeiXinAPI()
    wx_api.setAccountId(appKey=settings.WXPAY_APPID)
    resp = wx_api.createQRcode('QR_SCENE', mama_id)

    qrcode_link = ''
    if 'url' in resp:
        qrcode_link = push_qrcode_to_remote('xiaolumm/referal/%s'% mama_id, resp['url'], box_size=4)
        qrcode_link += '?imageMogr2/strip/format/jpg/quality/100/interlace/1/thumbnail/80/'
    if not qrcode_link:
        return ''

    thumbnail = re.sub('/0$', '/64', thumbnail)
    params = {
        'base_url': BASE_MAMA_QRCODE_IMG_RUL,
        'message': base64.urlsafe_b64encode(str(message)),
        'thumbnail': base64.urlsafe_b64encode(str(thumbnail)),
        'qrcode': base64.urlsafe_b64encode(str(qrcode_link))
    }
    return BASE_MAMA_QRCODE_TEMPLATE_URL.format(**params)

@log_consume_time
def fetch_wxpub_mama_custom_qrcode_media_id(xiaolumama):
    cache_key = 'wxpub_mama_referal_qrcode_mama_id_%s'%xiaolumama.id
    cache_value = cache.get(cache_key) and None
    if not cache_value:
        logger.info('fetch_wxpub_mama_custom_qrcode_media_id cache miss: %s' % xiaolumama)
        thumbnail = xiaolumama.thumbnail or DEFAULT_MAMA_THUMBNAIL
        media_url = gen_mama_custom_qrcode_url(xiaolumama.id, thumbnail)

        media_body = urllib.urlopen(media_url).read()
        media_stream = StringIO.StringIO()
        media_stream.write(media_body)

        wx_api = WeiXinAPI()
        wx_api.setAccountId(appKey=settings.WXPAY_APPID)
        response = wx_api.upload_media(media_stream)
        cache_value = response['media_id']
        cache.set(cache_key, cache_value, 2 * 24 *3600)
    else:
        logger.info('fetch_wxpub_mama_custom_qrcode_media_id cache hit: %s'% xiaolumama)
    return cache_value









