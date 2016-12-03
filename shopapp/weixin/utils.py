# coding: utf8
from __future__ import absolute_import, unicode_literals
from shopmanager import celery_app as app

import re
import hashlib
import urllib2
import random
from django.conf import settings
from django.core.cache import cache
import cStringIO as StringIO
import requests
from PIL import (
    Image,
    ImageColor,
    ImageDraw,
    ImageFont
)
import simplejson

from flashsale.xiaolumm.models import XiaoluMama
from shopapp.weixin.weixin_apis import WeiXinAPI
from shopapp.weixin.models_base import WeixinQRcodeTemplate
from core.logger import log_consume_time
from core.upload.upload import upload_public_to_remote, generate_public_url

import logging
logger = logging.getLogger(__name__)


DEFAULT_MAMA_THUMBNAIL = 'http://img.xiaolumeimei.com/undefined1472268058597lADOa301H8zIzMg_200_200.jpg_620x10000q90g.jpg?imageMogr2/thumbnail/80/crop/80x80/format/jpg'


def get_mama_customer(mama_id):
    mama = XiaoluMama.objects.filter(id=mama_id).first()
    if mama:
        return mama.get_customer()
    else:
        return None


@log_consume_time
def gen_mama_custom_qrcode_url(mama_id):
    cache_key = 'wxpub_qrcode_link_by_mama_id_%s' % (mama_id)
    cache_value = cache.get(cache_key)

    if cache_value:
        qrcode_link, content = cache_value.get('qrcode_link', ''), cache_value.get('content', '')
    else:
        wx_api = WeiXinAPI()
        wx_api.setAccountId(appKey=settings.WX_PUB_APPID)
        resp = wx_api.createQRcode('QR_SCENE', mama_id)

        qrcode_link = ''
        if 'ticket' in resp:
            qrcode_link = wx_api.genQRcodeAccesssUrl(resp['ticket'])
        content = resp.get('url', '')

        cache_value = {'qrcode_link': qrcode_link, 'content': content}
        cache.set(cache_key, cache_value, 24 * 3600)
    return qrcode_link, content


@app.task(max_retries=3, default_retry_delay=5, ignore_result=False)
def fetch_wxpub_mama_custom_qrcode_url(mama_id):
    """
    为小鹿妈妈创建带背景图的开店二维码，并上传七牛，返回七牛链接
    """
    mama = XiaoluMama.objects.filter(id=mama_id).first()
    if not mama:
        return

    customer = mama.get_customer()
    thumbnail = customer.thumbnail or DEFAULT_MAMA_THUMBNAIL

    qrcode_tpls = WeixinQRcodeTemplate.objects.filter(status=True)
    qrcode_tpl = random.choice(qrcode_tpls)
    params = simplejson.loads(qrcode_tpl.params)
    if params.get('avatar'):
        params['avatar']['url'] = thumbnail
    if params.get('qrcode'):
        params['qrcode']['url'], _ = gen_mama_custom_qrcode_url(mama_id)
    if params.get('text'):
        params['text']['content'] = params['text']['content'].format(**{'nickname': customer.nick})
    media_stream = generate_colorful_qrcode(params)

    # 上传七牛
    filepath = 'qrcode/%s.jpg' % md5(simplejson.dumps(params))
    upload_public_to_remote(filepath, media_stream)

    return generate_public_url(filepath)


@log_consume_time
def fetch_wxpub_mama_custom_qrcode_media_id(mama_id, userinfo, wxpubId):
    cache_key = 'wxpub_mama_referal_qrcode_mama_id_%s_%s' % (wxpubId, mama_id)
    cache_value = cache.get(cache_key)
    if not cache_value:
        logger.info('fetch_wxpub_mama_custom_qrcode_media_id cache miss: %s, %s' % (wxpubId, mama_id))
        thumbnail = userinfo['headimgurl'] or DEFAULT_MAMA_THUMBNAIL

        qrcode_tpls = WeixinQRcodeTemplate.objects.filter(status=True)
        qrcode_tpl = random.choice(qrcode_tpls)
        params = simplejson.loads(qrcode_tpl.params)
        if params.get('avatar'):
            params['avatar']['url'] = thumbnail
        if params.get('qrcode'):
            params['qrcode']['url'], _ = gen_mama_custom_qrcode_url(mama_id)
        if params.get('text'):
            params['text']['content'] = params['text']['content'].format(**{'nickname': userinfo['nickname']})
        media_stream = generate_colorful_qrcode(params)

        wx_api = WeiXinAPI()
        wx_api.setAccountId(wxpubId=wxpubId)
        response = wx_api.upload_media(media_stream)
        cache_value = response['media_id']
        cache.set(cache_key, cache_value, 3600)
    else:
        logger.info('fetch_wxpub_mama_custom_qrcode_media_id cache hit:  %s, %s' % (wxpubId, mama_id))
    return cache_value


@log_consume_time
def fetch_wxpub_mama_manager_qrcode_media_id(mama_id, wxpubId):

    from flashsale.xiaolumm.models import MamaAdministrator
    xiaolumama = XiaoluMama.objects.get(id=mama_id)
    mama_administrator = MamaAdministrator.get_or_create_by_mama(xiaolumama)
    if not mama_administrator:
        logger.warn('fetch_wxpub_mama_manager_qrcode_media_id administrator loss:  %s, %s' % (wxpubId, mama_id))
        return

    mama_manager_qrcode = mama_administrator.weixin_qr_img
    cache_key = hashlib.sha1('%s-%s'%(mama_manager_qrcode, wxpubId)).hexdigest()
    cache_value = cache.get(cache_key)
    if not cache_value:
        logger.info('fetch_wxpub_mama_manager_qrcode_media_id cache miss:  %s, %s' % (wxpubId, mama_id))
        media_body = urllib2.urlopen(mama_manager_qrcode).read()
        media_stream = StringIO.StringIO(media_body)

        wx_api = WeiXinAPI(wxpubId=wxpubId)
        response = wx_api.upload_media(media_stream)
        cache_value = response['media_id']
        cache.set(cache_key, cache_value, 2 * 24 * 3600)
    else:
        logger.info('fetch_wxpub_mama_manager_qrcode_media_id cache hit:  %s, %s' % (wxpubId, mama_id))
    return cache_value


def generate_qrcode(words, picture=None):
    from MyQR import myqr

    path = str('/tmp/')
    version, level, qr_name = myqr.run(
        str(words),
        version=10,
        level=str('H'),
        picture=str(picture),
        colorized=True,
        contrast=1.0,
        brightness=1.0,
        save_name=None,
        save_dir=path
    )
    return qr_name


def md5(str):
    m = hashlib.md5()
    m.update(str)
    return m.hexdigest()


def generate_colorful_qrcode(params):
    """
    params:
    {
        'background_url': '',
        'text': {
            'content': u'',
            'font': '/home/aladdin/download/fonts/方正兰亭黑.TTF',  # 选填
            'font_size': 24,  # 选填
            'y': 174,  # Y坐标
            'color': '#f1c40f'
        },
        'avatar': {
            'url': '',
            'size': 120,
            'x': 240,
            'y': 30
        },
        'qrcode': {
            'url': '',
            'size': 430,
            'x': 85,
            'y': 409,
        }
    }
    """
    background_url = params.get('background_url')

    cache_key = 'wxpub_mama_referal_qrcode_background_%s' % md5(background_url)
    cache_value = cache.get(cache_key)

    if not cache_value:
        resp = requests.get(background_url, verify=False)
        bg_img = Image.open(StringIO.StringIO(resp.content))
        cache.set(cache_key, resp.content, 24*3600)
    else:
        bg_img = Image.open(StringIO.StringIO(cache_value))
    bg_width, bg_height = bg_img.size

    avatar_size = params.get('avatar', {}).get('size', 120)
    size = (avatar_size, avatar_size)

    avatar_url = params.get('avatar', {}).get('url')
    avatar_x   = params.get('avatar', {}).get('x') or 240
    avatar_y   = params.get('avatar', {}).get('y') or 30
    if avatar_url:
        try:
            avatar_url = re.sub('/[0-9]+$', '/96', avatar_url)
            resp   = requests.get(avatar_url, verify=False)
            avatar = Image.open(StringIO.StringIO(resp.content)).resize(size)
        except Exception, exc:
            avatar = None
    else:
        avatar = None

    text = params.get('text', {}).get('content', '')
    text_x = params.get('text', {}).get('x', None)
    text_y = params.get('text', {}).get('y', 174)
    text_align = params.get('text', {}).get('align', 'center')
    text_color = params.get('text', {}).get('color', '#f1c40f')
    text_spacing = params.get('text', {}).get('spacing', 4)
    font_path = params.get('text', {}).get('font', settings.FANGZHENG_LANTINGHEI_FONT_PATH)
    font_size = params.get('text', {}).get('font_size', 24)
    font = ImageFont.truetype(type(font_path) == unicode and font_path.encode('utf8') or font_path, font_size)

    qrcode_url = params.get('qrcode', {}).get('url', '')
    qrcode_text = params.get('qrcode', {}).get('text', '')
    qrcode_img = params.get('qrcode', {}).get('img', '')
    qrcode_size = params.get('qrcode', {}).get('size', 430)
    qrcode_x = params.get('qrcode', {}).get('x', 85)
    qrcode_y = params.get('qrcode', {}).get('y', 409)
    if qrcode_url:
        resp = requests.get(qrcode_url, verify=False)
        qrcode = Image.open(StringIO.StringIO(resp.content)).resize((qrcode_size, qrcode_size))
    elif qrcode_text:
        if qrcode_img:
            resp = requests.get(qrcode_img, verify=False)
            picture = Image.open(StringIO.StringIO(resp.content))
            path = '/tmp/%s.jpg' % md5(qrcode_img)
            picture.save(path)
            qr_path = generate_qrcode(qrcode_text, picture=path)
        else:
            qr_path = generate_qrcode(qrcode_text)
        qrcode = Image.open(qr_path).resize((qrcode_size, qrcode_size))
    else:
        qrcode = None

    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + size, fill=255)

    if text:
        draw = ImageDraw.Draw(bg_img)
        text_size = draw.textsize(text, font)
        text_width, text_height = text_size
        text_x = (bg_width / 2 - text_width / 2) if not text_x else text_x
        draw.multiline_text(
            (text_x, text_y),
            text,
            fill=ImageColor.getrgb(text_color),
            font=font,
            align=text_align,
            spacing=text_spacing
        )

    if avatar:
        bg_img.paste(avatar, box=(avatar_x, avatar_y, avatar_x+avatar_size, avatar_y+avatar_size), mask=mask)
    if qrcode:
        bg_img.paste(qrcode, box=(qrcode_x, qrcode_y, qrcode_x+qrcode_size, qrcode_y+qrcode_size))

    # bg_img.show()
    result = StringIO.StringIO()
    bg_img.save(result, 'JPEG')
    return StringIO.StringIO(result.getvalue())
