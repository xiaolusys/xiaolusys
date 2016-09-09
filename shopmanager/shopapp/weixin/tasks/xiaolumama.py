# coding: utf8
import datetime
from celery.task import task

from django.contrib.auth.models import User
from flashsale.pay.models import Customer
from flashsale.xiaolumm.models import XiaoluMama, PotentialMama, XlmmFans
from flashsale.pay.models import BudgetLog

from ..weixin_apis import WeiXinAPI
from ..models import WeixinUnionID, WeixinUserInfo, WeixinFans, WeiXinAutoResponse
from ..utils import fetch_wxpub_mama_custom_qrcode_media_id, fetch_wxpub_mama_manager_qrcode_media_id

import logging
logger = logging.getLogger(__name__)

    

    
@task
def task_create_scan_customer(wx_userinfo):
    unionid = wx_userinfo['unionid']
    thumbnail = wx_userinfo['headimgurl']
    nick = wx_userinfo['nickname']
    
    cu = Customer.objects.filter(unionid=unionid).first()
    if not cu:
        user, state = User.objects.get_or_create(username=unionid, is_active=True)
        cu = Customer(unionid=unionid, user=user, thumbnail=thumbnail, nick=nick)
        cu.save()

@task
def task_create_scan_xiaolumama(wx_userinfo):
    unionid = wx_userinfo['unionid']
    mama = XiaoluMama.objects.filter(openid=unionid).first()
    if not mama:
        mama = XiaoluMama(openid=unionid, progress=XiaoluMama.PROFILE, last_renew_type=XiaoluMama.SCAN)
        mama.save()


@task
def task_get_unserinfo_and_create_accounts(openid, wx_pubid):
    wx_api = WeiXinAPI()
    wx_api.setAccountId(wxpubId=wx_pubid)
    app_key = wx_api.getAccount().app_id

    wx_userinfo = None
    fan = WeixinFans.objects.filter(app_key=app_key, openid=openid).first()
    if fan:
        wx_userinfo = WeixinUserInfo.objects.filter(unionid=fan.unionid).first()
        if wx_userinfo:
            unionid = wx_userinfo.unionid
            headimgurl = wx_userinfo.thumbnail
            nickname = wx_userinfo.nick
            wx_userinfo = {'unionid':unionid, 'headimgurl':headimgurl, 'nickname':nickname}
        
    if not wx_userinfo:
        wx_userinfo = wx_api.getCustomerInfo(openid)
        from shopapp.weixin.tasks.base import task_snsauth_update_weixin_userinfo
        task_snsauth_update_weixin_userinfo.delay(wx_userinfo, app_key)
    
    task_create_scan_customer.delay(wx_userinfo)
    task_create_scan_xiaolumama.delay(wx_userinfo)
    
    
@task    
def task_create_scan_potential_mama(referal_from_mama_id, potential_mama_id, wx_userinfo):
    uni_key = PotentialMama.gen_uni_key(potential_mama_id, referal_from_mama_id)
    pm = PotentialMama.objects.filter(uni_key=uni_key).first()
    if not pm:
        thumbnail = wx_userinfo['headimgurl']
        nick = wx_userinfo['nickname']
        pm = PotentialMama(potential_mama=potential_mama_id, referal_mama=referal_from_mama_id, uni_key=uni_key,
                           nick=nick, thumbnail=thumbnail, last_renew_type=XiaoluMama.SCAN)
        pm.save()


@task
def task_create_or_update_weixinfans(wx_pubid, openid, qr_scene, wx_userinfo):
    wx_api = WeiXinAPI()
    wx_api.setAccountId(wxpubId=wx_pubid)
    app_key = wx_api.getAccount().app_id

    fan = WeixinFans.objects.filter(app_key=app_key, openid=openid).first()
    if fan:
        if not fan.get_qrscene() and qr_scene:
            fan.set_qrscene(qr_scene)
            fan.save()
        return

    subscribe_time = datetime.datetime.now()
    fan = WeixinFans(openid=openid,app_key=app_key,unionid=unionid,subscribe=True,subscribe_time=subscribe_time)
    fan.set_qrscene(qr_scene)
    fan.save()


@task
def task_unsubscribe_update_weixinfans(openid):
    wx_api = WeiXinAPI()
    wx_api.setAccountId(wxpubId=wx_pubid)
    app_key = wx_api.getAccount().app_id

    unsubscribe_time = datetime.datetime.now()
    WeixinFans.objects.filter(app_key=app_key, openid=openid).update(subscribe=False, unsubscribe_time=unsubscribe_time)
    

@task
def task_activate_xiaolumama(mama_id):
    renew_date = datetime.date.today() + datetime.timedelta(days=3)
    renew_time = datetime.datetime(renew_date.year, renew_date.month, renew_date.day)
    cnt = XiaoluMama.objects.filter(id=mama_id).update(charge_status=XiaoluMama.CHARGED, renew_time=renew_time)
    if cnt > 0:
        # send weixin notification: shop is activated.
        pass

@task
def task_weixinfans_update_xlmmfans(referal_from_mama_id, referal_to_unionid):
    customer = Customer.objects.filter(unionid=referal_to_unionid).first()
    if not customer:
        return
    fans_cusid = customer.id
    fans_nick = customer.nick
    fans_thumbnail = customer.thumbnail
    
    fan = XlmmFans.objects.filter(fans_cusid=fans_cusid).first()
    if fan:
        return
    
    from_mama = XiaoluMama.objects.filter(id=referal_from_mama_id).first()
    if not from_mama:
        return

    from_customer = from_mama.get_mama_customer()
    if not from_customer:
        return
    
    xlmm_cusid = from_customer.id
    fan = XlmmFans(xlmm=referal_from_mama_id, xlmm_cusid=xlmm_cusid, refreal_cusid=xlmm_cusid, fans_cusid=fans_cusid,
                   fans_nick=fans_nick, fans_thumbnail=fans_thumbnail)
    fan.save()


@task
def task_weixinfans_create_budgetlog(customer_unionid, reference_unionid, budget_log_type):
    customer = Customer.objects.filter(unionid=customer_unionid).first()
    reference = Customer.objects.filter(unionid=reference_unionid).first()
    log = BudgetLog.objects.filter(customer_id=customer.id, referal_id=reference.id, budget_log_type=budget_log_type).first()
    if log:
        return

    flow_amount = 0
    if budget_log_type == BudgetLog.BG_REFERAL_FANS:
        # 推荐人得1元
        flow_amount = 100
    elif budget_log_type == BudgetLog.BG_SUBSCRIBE:
        # 被推荐人得0.5元
        flow_amount = 50
    else:
        return
        
    budget_type = BudgetLog.BUDGET_IN
    budget_date = datetime.date.today()

    log = BudgetLog(customer_id=customer.id, flow_amount=flow_amount, budget_type=budget_type,
                    budget_log_type=budget_log_type, budget_date=budget_date, referal_id=reference.id)
    log.save()

    
def get_or_create_weixin_xiaolumm(wxpubId, openid, event, eventKey):
    wx_api = WeiXinAPI()
    wx_api.setAccountId(wxpubId=wxpubId)
    app_key = wx_api.getAccount().app_id

    # 获取或创建用户信息,
    fans_obj = WeixinFans.objects.filter(openid=openid, app_key=app_key).first()
    qrscene_id = eventKey and eventKey.lower().replace('qrscene_', '') or ''
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
        if not fans_obj.get_qrscene() and event.upper() == 'SCAN' and qrscene_id:
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
