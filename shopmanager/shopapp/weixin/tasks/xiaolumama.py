# coding: utf8
import datetime
from celery.task import task

from django.contrib.auth.models import User
from flashsale.pay.models import Customer
from flashsale.xiaolumm.models import XiaoluMama, PotentialMama
from ..weixin_apis import WeiXinAPI
from ..models import WeixinUnionID, WeixinUserInfo, WeixinFans, WeiXinAutoResponse
from ..utils import fetch_wxpub_mama_custom_qrcode_media_id, fetch_wxpub_mama_manager_qrcode_media_id

import logging
logger = logging.getLogger(__name__)

def create_customer_profile(unionid, wx_userinfo):
    profile = Customer.objects.filter(unionid=unionid).first()
    if not profile:
        user, state = User.objects.get_or_create(username=unionid, is_active=True)
        profile = Customer(
            unionid=unionid,
            user=user,
            thumbnail=wx_userinfo['headimgurl'],
            nick=wx_userinfo['nickname']
        )
        profile.save()
    return profile

def create_xiaolumama(unionid):
    mama = XiaoluMama.objects.filter(openid=unionid).first()
    if not mama:
        mama = XiaoluMama.objects.create(
            openid=unionid,
            progress=XiaoluMama.PROFILE,
            last_renew_type=XiaoluMama.SCAN,
        )
    return mama

def create_potential_mama():
    pass


def get_or_create_weixin_xiaolumm(wxpubId, openid, event, eventKey):
    wx_api = WeiXinAPI()
    wx_api.setAccountId(wxpubId=wxpubId)
    app_key = wx_api.getAccount().app_id

    # 获取或创建用户信息,
    fans_obj = WeixinFans.objects.filter(openid=openid, app_key=app_key).first()
    qrscene_id = eventKey and eventKey.replace('qrscene_', '') or ''
    wx_userinfo = wx_api.getCustomerInfo(openid)
    unionid = wx_userinfo['unionid']

    if not fans_obj:
        fans_obj = WeixinFans()
        fans_obj.openid = openid
        fans_obj.app_key = app_key
        fans_obj.unionid = unionid
        fans_obj.subscribe = True
        fans_obj.subscribe_time = datetime.datetime.now()
        fans_obj.set_qrscene(qrscene_id)
        fans_obj.save()

        WeixinUnionID.objects.get_or_create(
            openid=openid,
            app_key=app_key,
            unionid=unionid,
        )
    else:
        if not fans_obj.get_qrscene() and event.upper() == 'SCAN' and eventKey:
            fans_obj.set_qrscene(qrscene_id)
            fans_obj.save()

    referal_from_mama = fans_obj.get_qrscene()
    if not referal_from_mama.isdigit():
        referal_from_mama = '0'
    # 创建用户信息
    profile = Customer.objects.filter(unionid=unionid).first()
    if not profile:
        user, state = User.objects.get_or_create(username=unionid, is_active=True)
        profile = Customer(
            unionid=unionid,
            user=user,
            thumbnail=wx_userinfo['headimgurl'],
            nick=wx_userinfo['nickname']
        )
        profile.save()

    # 创建小鹿妈妈记录
    referal_from_mama_obj = XiaoluMama.objects.filter(id=referal_from_mama).first()
    referal_from_mama_id  = referal_from_mama_obj and referal_from_mama_obj.id or 0
    xiaolumm = XiaoluMama.objects.filter(openid=unionid).first()
    if not xiaolumm:
        xiaolumm = XiaoluMama.objects.create(
            mobile=profile.mobile,
            referal_from=referal_from_mama_obj and referal_from_mama_obj.mobile or '',
            progress=XiaoluMama.PROFILE,
            openid=unionid,
            # TODO@meron 非付款妈妈状态更新
            last_renew_type=XiaoluMama.SCAN,
        )
    # 添加妈妈推荐关系
    if xiaolumm.is_chargeable():
        potentailmama = PotentialMama.objects.filter(potential_mama=xiaolumm.id).first()
        if potentailmama:
            return xiaolumm
        if referal_from_mama_id and int(referal_from_mama_id) != xiaolumm.id:
            protentialmama = PotentialMama(
                potential_mama=xiaolumm.id,
                referal_mama=referal_from_mama_id,
                nick=wx_userinfo['nickname'],
                thumbnail=wx_userinfo['headimgurl'],
                last_renew_type=XiaoluMama.SCAN,
                uni_key=PotentialMama.gen_uni_key(xiaolumm.id, referal_from_mama_id))
            protentialmama.save()
        #  修改该小鹿妈妈的接管状态
        xiaolumm.chargemama()
        xiaolumm.update_renew_day(XiaoluMama.SCAN)

    return xiaolumm

@task(max_retries=3, default_retry_delay=5)
def task_create_mama_referal_qrcode_and_response_weixin(wxpubId, openid, event, eventKey):
    """ to_username: 公众号id, from_username: 关注用户id """
    try:
        xiaolumm = get_or_create_weixin_xiaolumm(wxpubId, openid, event, eventKey)

        # 获取创建用户小鹿妈妈信息,
        media_id = fetch_wxpub_mama_custom_qrcode_media_id(xiaolumm, wxpubId)

        wx_api = WeiXinAPI()
        wx_api.setAccountId(wxpubId=wxpubId)
        # 调用客服回复接口返回二维码图片消息
        wx_api.send_custom_message({
            "touser": openid,
            "msgtype":"image",
            "image":{
              "media_id":media_id
            }
        })
    except Exception,exc:
        logger.error(str(exc), exc_info=True)
        raise task_create_mama_referal_qrcode_and_response_weixin.retry(exc=exc)

@task(max_retries=3, default_retry_delay=5)
def task_create_mama_and_response_manager_qrcode(wxpubId, openid, event, eventKey):
    """ to_username: 公众号id, from_username: 关注用户id """
    try:
        xiaolumm = get_or_create_weixin_xiaolumm(wxpubId, openid, event, eventKey)

        # 获取创建用户小鹿妈妈信息,
        media_id = fetch_wxpub_mama_manager_qrcode_media_id(xiaolumm, wxpubId)

        wx_api = WeiXinAPI()
        wx_api.setAccountId(wxpubId=wxpubId)
        if not media_id:
            wx_api.send_custom_message({
                "touser": openid,
                'MsgType': WeiXinAutoResponse.WX_TEXT,
                'Content': u'[委屈]二维码生成出错了， 请稍后重试或联系客服，谢谢！'
            })
            return

        # 调用客服回复接口返回二维码图片消息
        wx_api.send_custom_message({
            "touser": openid,
            "msgtype": "image",
            "image": {
                "media_id": media_id
            }
        })

    except Exception, exc:
        logger.error(str(exc), exc_info=True)
        raise task_create_mama_and_response_manager_qrcode.retry(exc=exc)
