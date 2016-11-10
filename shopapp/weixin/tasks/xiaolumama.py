# coding: utf8
import datetime
from celery.task import task

from django.contrib.auth.models import User
from flashsale.pay.models import Customer
from flashsale.xiaolumm.models import XiaoluMama, PotentialMama, XlmmFans, AwardCarry, WeixinPushEvent
from flashsale.pay.models import BudgetLog
from shopback.monitor.models import XiaoluSwitch

from ..weixin_apis import WeiXinAPI
from ..models import WeixinUnionID, WeixinUserInfo, WeixinFans, WeiXinAutoResponse
from ..utils import fetch_wxpub_mama_custom_qrcode_media_id, fetch_wxpub_mama_manager_qrcode_media_id

import logging
logger = logging.getLogger(__name__)



def get_userinfo_from_database(openid, app_key):
    """
    Try to find userinfo from local database.
    """
    userinfo = None
    record = WeixinUnionID.objects.filter(openid=openid, app_key=app_key).first()
    if record:
        userinfo = WeixinUserInfo.objects.filter(unionid=record.unionid).first()
        if userinfo:
            unionid = userinfo.unionid
            headimgurl = userinfo.thumbnail
            nickname = userinfo.nick
            userinfo = {'unionid':unionid, 'headimgurl':headimgurl, 'nickname':nickname}
    return userinfo


def get_or_fetch_userinfo(openid, wx_pubid):
    wx_api = WeiXinAPI()
    wx_api.setAccountId(wxpubId=wx_pubid)
    app_key = wx_api.getAppKey()

    userinfo = get_userinfo_from_database(openid, app_key)
    if not userinfo:
        userinfo = wx_api.getCustomerInfo(openid)

    return userinfo


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


@task(max_retries=3, default_retry_delay=15)
def task_get_unserinfo_and_create_accounts(openid, wx_pubid):
    """
    Initially, this task should be invoked for every weixin user.
    In the future, this task should only be invoked upon user subscribe.
    """
    try:
        wx_api = WeiXinAPI(wxpubId=wx_pubid)
        app_key = wx_api.getAppKey()

        userinfo = get_userinfo_from_database(openid, app_key)
        if not userinfo:
            userinfo = wx_api.getCustomerInfo(openid)
            if not userinfo or userinfo.get('subscribe') == 0:
                return

            from shopapp.weixin.tasks.base import task_snsauth_update_weixin_userinfo
            task_snsauth_update_weixin_userinfo.delay(userinfo, app_key)

        if not userinfo or not userinfo.get('headimgurl'):
            return

        task_create_scan_customer.delay(userinfo)
        task_create_scan_xiaolumama.delay(userinfo)
    except Exception, exc:
        raise task_get_unserinfo_and_create_accounts.retry(exc=exc)
    
    
@task    
def task_create_scan_potential_mama(referal_from_mama_id, potential_mama_id, potential_mama_unionid):
    if referal_from_mama_id == potential_mama_id:
        return
    
    uni_key = PotentialMama.gen_uni_key(potential_mama_id, referal_from_mama_id)
    pm = PotentialMama.objects.filter(uni_key=uni_key).first()
    if pm:
        return

    info = WeixinUserInfo.objects.filter(unionid=potential_mama_unionid).first()
    if not info:
        return
        
    thumbnail = info.thumbnail
    nick = info.nick
    pm = PotentialMama(potential_mama=potential_mama_id, referal_mama=referal_from_mama_id, uni_key=uni_key,
                       nick=nick, thumbnail=thumbnail, last_renew_type=XiaoluMama.SCAN)
    pm.save()


@task(max_retries=3, default_retry_delay=15)
def task_create_or_update_weixinfans_upon_subscribe_or_scan(openid, wx_pubid, event, eventkey):
    """
    For subscribe.
    """
    try:
        qrscene = eventkey.lower().replace('qrscene_', '')
        subscribe_time = datetime.datetime.now()

        wx_api = WeiXinAPI(wxpubId=wx_pubid)
        app_key = wx_api.getAppKey()

        userinfo = get_userinfo_from_database(openid, app_key)
        if not userinfo:
            userinfo = wx_api.getCustomerInfo(openid)

        # if not set headimg return
        if not (userinfo and userinfo.get('headimgurl') and userinfo.get('headimgurl').strip()):
            return

        fan = WeixinFans.objects.filter(app_key=app_key, openid=openid).first()
        if fan:
            if event == WeiXinAutoResponse.WX_EVENT_SUBSCRIBE.lower():
                fan.subscribe_time = subscribe_time
                fan.subscribe = True
            elif event == WeiXinAutoResponse.WX_EVENT_SCAN.lower():
                if not fan.subscribe:
                    fan.subscribe = True
            if not fan.get_qrscene() and qrscene:
                fan.set_qrscene(qrscene)
            fan.save()
            return

        unionid = userinfo['unionid']
        fan = WeixinFans(openid=openid,app_key=app_key,unionid=unionid,subscribe=True,subscribe_time=subscribe_time)
        fan.set_qrscene(qrscene)
        fan.save()
    except Exception, exc:
        raise task_create_or_update_weixinfans_upon_subscribe_or_scan.retry(exc=exc)

@task
def task_update_weixinfans_upon_unsubscribe(openid, wx_pubid):
    """
    For unsubscribe.
    """
    wx_api = WeiXinAPI()
    wx_api.setAccountId(wxpubId=wx_pubid)
    app_key = wx_api.getAppKey()

    unsubscribe_time = datetime.datetime.now()
    WeixinFans.objects.filter(app_key=app_key, openid=openid).update(subscribe=False, unsubscribe_time=unsubscribe_time)
    

@task
def task_activate_xiaolumama(openid, wx_pubid):
    wx_api = WeiXinAPI()
    wx_api.setAccountId(wxpubId=wx_pubid)
    app_key = wx_api.getAppKey()

    fan = WeixinFans.objects.filter(openid=openid, app_key=app_key).first()
    if not fan:
        return

    unionid = fan.unionid
    mama = XiaoluMama.objects.filter(openid=unionid,charge_status=XiaoluMama.UNCHARGE, status=XiaoluMama.EFFECT).first()
    if not mama:
        return

    # 内部测试 
    if XiaoluSwitch.is_switch_open(2):
        return 

    mama_id = mama.id
    charge_time = datetime.datetime.now()
    renew_date = datetime.date.today() + datetime.timedelta(days=3)
    renew_time = datetime.datetime(renew_date.year, renew_date.month, renew_date.day)
    XiaoluMama.objects.filter(id=mama_id).update(charge_status=XiaoluMama.CHARGED,
                                                 charge_time=charge_time,
                                                 last_renew_type=XiaoluMama.SCAN,
                                                 renew_time=renew_time, agencylevel=XiaoluMama.A_LEVEL)

    referal_from_mama_id = None
    qrscene = fan.get_qrscene()
    if qrscene and qrscene.isdigit():
        referal_from_mama_id = int(qrscene)
    else:
        return
    
    if referal_from_mama_id < 1:
        return

    potential_mama_id = mama.id
    potential_mama_unionid = unionid
    task_create_scan_potential_mama.delay(referal_from_mama_id, potential_mama_id, potential_mama_unionid)
    
    #referal_mama = XiaoluMama.objects.filter(id=referal_from_mama_id).first()
    #if referal_mama and referal_mama.openid:
    #    task_weixinfans_create_budgetlog.delay(referal_mama.openid, potential_mama_unionid, BudgetLog.BG_REFERAL_FANS)
    

@task(max_retries=3, default_retry_delay=6)
def task_weixinfans_update_xlmmfans(referal_from_mama_id, referal_to_unionid):

    try:
        customer = Customer.objects.filter(unionid=referal_to_unionid).first()
        if not customer:
            raise Customer.DoesNotExist()

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
        if xlmm_cusid == fans_cusid:
            return
    
        fan = XlmmFans(xlmm=referal_from_mama_id, xlmm_cusid=xlmm_cusid, refreal_cusid=xlmm_cusid, fans_cusid=fans_cusid,
                       fans_nick=fans_nick, fans_thumbnail=fans_thumbnail)
        fan.save()
    except Exception as exc:
        raise task_weixinfans_update_xlmmfans.retry(exc=exc)

def create_push_event_subscribe(mama_id, unionid, carry_num, date_field):
    customer = Customer.objects.filter(unionid=unionid, status=Customer.NORMAL).first()
    if not customer:
        return
    
    customer_id = customer.id 
    
    event_type = WeixinPushEvent.FANS_SUBSCRIBE_NOTIFY
    uni_key = WeixinPushEvent.gen_subscribe_notify_unikey(event_type, customer_id)
    event = WeixinPushEvent.objects.filter(uni_key=uni_key).first()
    if event:
        return

    now = datetime.datetime.now()
    tid = WeixinPushEvent.TEMPLATE_SUBSCRIBE_ID

    params = {'keyword1': {'value': u'%.2f元' % (carry_num * 0.01), 'color':'#FA5858'},
              'keyword2': {'value': u'关注小鹿美美系列公众号', 'color': '#394359'},
              'keyword3': {'value':now.strftime('%Y-%m-%d %H:%M:%S'), 'color':'#394359'}}
    
    to_url = 'http://m.xiaolumeimei.com/rest/v2/mama/redirect_stats_link?link_id=1'
    event = WeixinPushEvent(customer_id=customer_id,mama_id=mama_id,uni_key=uni_key,tid=tid,
                            event_type=event_type,date_field=date_field,params=params,to_url=to_url)
    event.save()
    

    
@task(max_retries=3, default_retry_delay=60)
def task_weixinfans_create_subscribe_awardcarry(unionid):
    carry_num = 100
    carry_type = AwardCarry.AWARD_SUBSCRIBE # 关注公众号
    
    try:
        mama = XiaoluMama.objects.filter(openid=unionid).first()
        if not mama:
            raise XiaoluMama.DoesNotExist()

        mama_id = mama.id
        # We get here too fast that WeixinUserInfo objects have not been created yet,
        # and when we try to access, error comes.        
        userinfo = WeixinUserInfo.objects.filter(unionid=unionid).first()

        uni_key = AwardCarry.gen_uni_key(mama_id, carry_type)
        ac = AwardCarry.objects.filter(uni_key=uni_key).first()
        if ac:
            return

        date_field = datetime.date.today()
        carry_description = u'谢谢关注！每天分享好东西，赚佣么么哒！'
        carry_plan_name = u'小鹿千万粉丝计划'
        contributor_mama_id = mama_id
        contributor_nick = userinfo.nick
        contributor_img = userinfo.thumbnail
    
        ac = AwardCarry(mama_id=mama_id,carry_num=carry_num, carry_type=carry_type, carry_description=carry_description,
                        contributor_nick=contributor_nick, contributor_img=contributor_img,
                        contributor_mama_id=contributor_mama_id, carry_plan_name=carry_plan_name,
                        date_field=date_field, uni_key=uni_key, status=AwardCarry.CONFIRMED)
        ac.save()
        create_push_event_subscribe(mama_id, unionid, carry_num, date_field)
        
    except Exception,exc:
        #logger.error(str(exc), exc_info=True)
        raise task_weixinfans_create_subscribe_awardcarry.retry(exc=exc)
    

def get_max_today_fans_invites(mama_id):
    # 每日最多邀请20名
    return 20


def create_push_event_invite_fans(mama_id, contributor_nick, contributor_mama_id, date_field, today_invites):
    mama = XiaoluMama.objects.filter(id=mama_id, status=XiaoluMama.EFFECT).first()
    if not mama:
        return
    
    customer = Customer.objects.filter(unionid=mama.unionid, status=Customer.NORMAL).first()
    if not customer:
        return
    
    customer_id = customer.id 
    
    event_type = WeixinPushEvent.INVITE_FANS_NOTIFY
    uni_key = WeixinPushEvent.gen_invite_fans_notify_unikey(event_type, customer_id, today_invites, date_field)
    event = WeixinPushEvent.objects.filter(uni_key=uni_key).first()
    if event:
        return

    footer = u'马上就成超级大咖啦！粉丝过千，日赚千元！'
    footer_color = '#394359'
    
    max_today_fans_invites = get_max_today_fans_invites(mama_id)
    if today_invites > max_today_fans_invites * 0.6:
        footer = u'你的二维码推广每日只能新增%d名好友，超过将不能再得奖励，请知悉哦！你今日已增加%d名好友。详情请联系App客服MM咨询。' % (max_today_fans_invites, today_invites)
        footer_color = '#FA5858'
        
    now = datetime.datetime.now()
    tid = WeixinPushEvent.TEMPLATE_INVITE_FANS_ID
    header = u"Great! 好友[%s]扫描二维码成为你的粉丝！" % contributor_nick

    params = {'first': {'value':header, 'color':"#394359"},
              'keyword1': {'value':contributor_mama_id, 'color':'#394359'},
              'keyword2': {'value':now.strftime('%Y-%m-%d %H:%M:%S'), 'color':'#394359'},
              'remark': {'value':footer, 'color':footer_color}}
    
    #to_url = 'http://m.xiaolumeimei.com/rest/v1/users/weixin_login/?next=/mama_shop/html/personal.html'
    event = WeixinPushEvent(customer_id=customer_id,mama_id=mama_id,uni_key=uni_key,tid=tid,
                            event_type=event_type,date_field=date_field,params=params)
    event.save()
    

    
@task(max_retries=3, default_retry_delay=5)
def task_weixinfans_create_fans_awardcarry(referal_from_mama_id, referal_to_unionid):
    if referal_from_mama_id < 1:
        return
    
    carry_num = 30
    carry_type = AwardCarry.AWARD_INVITE_FANS # 邀请关注成为粉丝
    mama_id = referal_from_mama_id

    date_field = datetime.date.today()
    today_invites = AwardCarry.objects.filter(mama_id=mama_id,carry_type=carry_type,date_field=date_field).count() + 1        
    
    max_today_fans_invites = get_max_today_fans_invites(mama_id)
    if today_invites > max_today_fans_invites:
        return
    
    try:
        # We get here too fast that WeixinUserInfo or referal XiaoluMama objects have not
        # been created yet, and when we try to access , error comes.        
        referal_to_mama = XiaoluMama.objects.filter(openid=referal_to_unionid).first()
        userinfo = WeixinUserInfo.objects.filter(unionid=referal_to_unionid).first()
        if not referal_to_mama :
            raise XiaoluMama.DoesNotExist()

        if not userinfo:
            raise WeixinUserInfo.DoesNotExist()

        uni_key = AwardCarry.gen_uni_key(referal_to_mama.id, carry_type)
        ac = AwardCarry.objects.filter(uni_key=uni_key).first()
        if ac:
            return

        carry_description = u'恭喜，又增加一名粉丝！'
        carry_plan_name = u'小鹿千万粉丝计划'
        contributor_mama_id = referal_to_mama.id
        contributor_nick = userinfo.nick
        contributor_img = userinfo.thumbnail

        # send weixin push
        create_push_event_invite_fans(mama_id, contributor_nick, contributor_mama_id, date_field, today_invites)
        
        ac = AwardCarry(mama_id=mama_id,carry_num=carry_num, carry_type=carry_type, carry_description=carry_description,
                        contributor_nick=contributor_nick, contributor_img=contributor_img,
                        contributor_mama_id=contributor_mama_id, carry_plan_name=carry_plan_name,
                        date_field=date_field, uni_key=uni_key, status=AwardCarry.CONFIRMED)
        ac.save()

    except Exception,exc:
        #logger.error(str(exc), exc_info=True)
        raise task_weixinfans_create_fans_awardcarry.retry(exc=exc)


def get_or_create_weixin_xiaolumm(wxpubId, openid, event, eventKey):
    wx_api = WeiXinAPI()
    wx_api.setAccountId(wxpubId=wxpubId)
    app_key = wx_api.getAppKey()

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
    if XiaoluSwitch.is_switch_open(3):
        return
    
    try:
        #xiaolumm = get_or_create_weixin_xiaolumm(wxpubId, openid, event, eventKey)
        
        userinfo = get_or_fetch_userinfo(openid, wxpubId)
        unionid = userinfo['unionid']
        if not userinfo or not userinfo.get('headimgurl'):
            return

        mama = XiaoluMama.objects.filter(openid=unionid).first()
        if not mama:
            raise XiaoluMama.DoesNotExist()

        # 获取创建用户小鹿妈妈信息,
        media_id = fetch_wxpub_mama_custom_qrcode_media_id(mama.id, userinfo, wxpubId)

        wx_api = WeiXinAPI(wxpubId=wxpubId)
        # 调用客服回复接口返回二维码图片消息
        try:
            wx_api.send_custom_message({
                "touser": openid,
                "msgtype":"image",
                "image":{
                  "media_id":media_id
                }
            })
        except Exception, exc:
            pass
    except Exception,exc:
        raise task_create_mama_referal_qrcode_and_response_weixin.retry(exc=exc)


@task(max_retries=3, default_retry_delay=5)
def task_create_mama_and_response_manager_qrcode(wxpubId, openid, event, eventKey):
    """ to_username: 公众号id, from_username: 关注用户id """
    try:
        #xiaolumm = get_or_create_weixin_xiaolumm(wxpubId, openid, event, eventKey)

        userinfo = get_or_fetch_userinfo(openid, wxpubId)
        unionid = userinfo['unionid']
        if not userinfo or not userinfo.get('headimgurl'):
            return
        mama = XiaoluMama.objects.filter(openid=unionid).first()
        # 获取创建用户小鹿妈妈信息,
        media_id = fetch_wxpub_mama_manager_qrcode_media_id(mama.id, wxpubId)

        wx_api = WeiXinAPI(wxpubId=wxpubId)
        try:
            if not media_id:
                wx_api.send_custom_message({
                    "touser": openid,
                    'msgtype': WeiXinAutoResponse.WX_TEXT,
                    'text': {
                         "content":u'[委屈]二维码生成出错了， 请稍后重试或联系客服，谢谢！'
                    }
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
            pass
    except Exception, exc:
        raise task_create_mama_and_response_manager_qrcode.retry(exc=exc)
