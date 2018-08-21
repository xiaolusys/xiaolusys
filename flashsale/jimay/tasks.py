# coding: utf8
from __future__ import absolute_import, unicode_literals

import urllib2
import json
import cStringIO as StringIO
import datetime

from shopmanager import celery_app as app
from django.conf import settings
from django.core.cache import cache

from flashsale.pay.models import Customer
from flashsale.jimay.models import JimayAgent
from shopapp.weixin.models.base import WeixinQRcodeTemplate

import logging
logger = logging.getLogger(__name__)

@app.task
def task_generate_jimay_agent_certification(agent_id):
    """ 创建己美医学特约代理授权证书 """

    from shopapp.weixin.models.base import WeixinQRcodeTemplate
    from shopapp.weixin.utils import generate_colorful_qrcode
    from core.upload.upload import upload_public_to_remote, generate_public_url

    agent = JimayAgent.objects.get(id=agent_id)
    cert_qr = WeixinQRcodeTemplate.get_agent_cert_templates().first()
    if not cert_qr:
        logger.error('己美医学授权证书无法生成，请先去[微信二维码模板]创建证书模板: agent_id=%s' % agent_id)
        return ''

    params = json.loads(cert_qr.params)
    certification_urls = params.get('certification_urls', [])
    if certification_urls and agent.level < len(certification_urls):
        params['background_url'] = certification_urls[agent.level]

    params['texts'][0]['content'] = agent.name
    params['texts'][1]['content'] = agent.idcard_no
    params['texts'][2]['content'] = agent.weixin

    start_dt = agent.created
    end_dt   = datetime.datetime(start_dt.year + 1, start_dt.month, start_dt.day)
    params['texts'][3]['content'] = str(start_dt.year)
    params['texts'][4]['content'] = str(start_dt.month)
    params['texts'][5]['content'] = str(start_dt.day)
    params['texts'][6]['content'] = str(end_dt.year)
    params['texts'][7]['content'] = str(end_dt.month)
    params['texts'][8]['content'] = str(end_dt.day)

    qrcode_io = generate_colorful_qrcode(params)
    filename = agent.gen_certification_filename()

    upload_public_to_remote(filename, qrcode_io)
    preview_url = generate_public_url(filename)

    agent.set_certification(preview_url)

    return preview_url


@app.task
def task_weixin_asynchronous_send_certification(wx_pubid, agent_id):

    from shopapp.weixin.apis.wxpubsdk import WeiXinAPI
    from shopapp.weixin.models import WeixinUnionID, WeiXinAutoResponse

    agent = JimayAgent.objects.get(id=agent_id)
    wx_api = WeiXinAPI(wxpubId=wx_pubid)

    cacke_key = agent.gen_certification_filename()
    cache_value = cache.get(cacke_key)
    if not cache_value:
        certification_url = agent.certification
        if not certification_url:
            certification_url = task_generate_jimay_agent_certification(agent.id)

        media_body = urllib2.urlopen(certification_url).read()
        media_stream = StringIO.StringIO(media_body)

        response = wx_api.upload_media(media_stream)
        cache_value = response['media_id']
        cache.set(cacke_key, cache_value, 60 * 60)

    openid = WeixinUnionID.get_openid_by_unionid(agent.buyer.unionid, wx_api.getAppKey())
    try:
        # 调用客服回复接口返回二维码图片消息
        wx_api.send_custom_message({
            "touser": openid,
            "msgtype": WeiXinAutoResponse.WX_IMAGE,
            "image": {
                "media_id": cache_value
            }
        })
    except Exception, exc:
        logger.error(str(exc), exc_info=True)
        wx_api.send_custom_message({
            "touser": openid,
            'msgtype': WeiXinAutoResponse.WX_TEXT,
            'text': {
                "content": u'[委屈]授权证书创建失败， 请稍后重试或联系客服，谢谢！'
            }
        })


@app.task
def task_weixin_asynchronous_send_payqrcode(wx_pubid, buyer_id, pay_key, tips=''):

    from shopapp.weixin.apis.wxpubsdk import WeiXinAPI
    from shopapp.weixin.models import WeixinUnionID, WeiXinAutoResponse

    pay_key = pay_key.lower()
    buyer = Customer.objects.get(id=buyer_id)
    wx_api = WeiXinAPI(wxpubId=wx_pubid)

    cacke_key = JimayAgent.gen_pay_qrcode_cache_key(wx_pubid, pay_key)
    cache_value = cache.get(cacke_key)
    if not cache_value:
        pay_qr = WeixinQRcodeTemplate.get_agent_pay_templates().first()
        if not pay_qr:
            logger.error('己美医学授权证书无法生成，请先去[微信二维码模板]创建证书模板: buyer_id=%s' % buyer_id)
            return ''

        params = json.loads(pay_qr.params)
        pay_qrcode_url = params.get('pay_qrocdes', {}).get(pay_key, '')

        media_body = urllib2.urlopen(pay_qrcode_url).read()
        media_stream = StringIO.StringIO(media_body)

        response = wx_api.upload_media(media_stream)
        cache_value = response['media_id']
        cache.set(cacke_key, cache_value, 60 * 60)

    openid = WeixinUnionID.get_openid_by_unionid(buyer.unionid, wx_api.getAppKey())
    try:
        # 调用客服回复接口返回二维码图片消息
        wx_api.send_custom_message({
            "touser": openid,
            "msgtype": WeiXinAutoResponse.WX_IMAGE,
            "image": {
                "media_id": cache_value
            }
        })
        # 支付文字提示
        if tips:
            wx_api.send_custom_message({
                "touser": openid,
                'msgtype': WeiXinAutoResponse.WX_TEXT,
                'text': {
                    "content": tips
                }
            })

    except Exception, exc:
        logger.error(str(exc), exc_info=True)
        wx_api.send_custom_message({
            "touser": openid,
            'msgtype': WeiXinAutoResponse.WX_TEXT,
            'text': {
                "content": u'[委屈]支付码创建失败， 请稍后重试或联系客服，谢谢！'
            }
        })


@app.task
def task_generate_jimay_award_certificate(agent_id):
    """ 创建己美医学特约代理授权证书 """

    from shopapp.weixin.models.base import WeixinQRcodeTemplate
    from shopapp.weixin.utils import generate_colorful_qrcode
    from core.upload.upload import upload_public_to_remote, generate_public_url

    agent = JimayAgent.objects.get(id=agent_id)
    award_qr = WeixinQRcodeTemplate.get_agent_award_templates().first()
    if not award_qr:
        logger.error('己美医学结业证书无法生成，请先去[微信二维码模板]创建证书模板: agent_id=%s' % agent_id)
        return ''

    start_time = agent.time_graduated_st
    start_end  = agent.time_graduated_en

    params = json.loads(award_qr.params)
    params['texts'][0]['content'] = agent.name
    params['texts'][1]['content'] = str(start_time.year)
    params['texts'][2]['content'] = str(start_time.month)
    params['texts'][3]['content'] = str(start_time.day)
    params['texts'][4]['content'] = str(start_end.month)
    params['texts'][5]['content'] = str(start_end.day)

    qrcode_io = generate_colorful_qrcode(params)
    filename = agent.gen_awardgraduated_filename()

    upload_public_to_remote(filename, qrcode_io)
    preview_url = generate_public_url(filename)
    agent.set_certification(preview_url)

    return preview_url


@app.task
def task_weixin_asynchronous_send_awardcomplete(wx_pubid, agent_id):

    from shopapp.weixin.apis.wxpubsdk import WeiXinAPI
    from shopapp.weixin.models import WeixinUnionID, WeiXinAutoResponse

    agent = JimayAgent.objects.get(id=agent_id)
    wx_api = WeiXinAPI(wxpubId=wx_pubid)

    cacke_key = agent.gen_graduated_cert_cache_key()
    cache_value = cache.get(cacke_key)
    if not cache_value:
        certification_url = task_generate_jimay_award_certificate(agent.id)

        media_body = urllib2.urlopen(certification_url).read()
        media_stream = StringIO.StringIO(media_body)

        response = wx_api.upload_media(media_stream)
        cache_value = response['media_id']
        cache.set(cacke_key, cache_value, 60 * 60)

    openid = WeixinUnionID.get_openid_by_unionid(agent.buyer.unionid, wx_api.getAppKey())
    try:
        # 调用客服回复接口返回二维码图片消息
        wx_api.send_custom_message({
            "touser": openid,
            "msgtype": WeiXinAutoResponse.WX_IMAGE,
            "image": {
                "media_id": cache_value
            }
        })
    except Exception, exc:
        logger.error(str(exc), exc_info=True)
        wx_api.send_custom_message({
            "touser": openid,
            'msgtype': WeiXinAutoResponse.WX_TEXT,
            'text': {
                "content": u'[委屈]结业证书创建失败， 请稍后重试或联系客服，谢谢！'
            }
        })