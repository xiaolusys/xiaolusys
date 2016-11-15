# -*- coding:utf-8 -*-
from __future__ import absolute_import, unicode_literals
from celery import shared_task as task

import random
import logging
import datetime
from django.db.models import F
from django.template import Context, Template
from common.utils import update_model_fields
from flashsale.pay.models import Register
from shopapp.smsmgr.service import SMS_CODE_MANAGER_TUPLE
from shopback import paramconfig as pcfg
from shopback.trades.models import SendLaterTrade
from shopapp.smsmgr.models import SMSPlatform, SMSActivity, SMS_NOTIFY_POST, SMS_NOTIFY_VERIFY_CODE, \
    SMS_NOTIFY_GOODS_LATER, SMS_NOTIFY_DELAY_POST, SMS_NOTIFY_LACK_REFUND

logger = logging.getLogger(__name__)


def call_send_a_sms(manager, params, sms_notify_type):
    """ 调用短信发送
    :param sms_notify_type: sms_notify_type
    :param params: params
    :param manager: manager
    """
    success = False
    succnums = 0
    sms_record = manager.create_record(  # 创建一条短信发送记录
        params['mobile'],
        params['taskName'],
        sms_notify_type,
        params['content']
    )
    try:  # 调用发送短信接口
        success, task_id, succnums, response = manager.batch_send(**params)
    except Exception, exc:
        sms_record.status = pcfg.SMS_ERROR
        sms_record.memo = exc.message
        logger.error(exc.message, exc_info=True)
    else:
        sms_record.task_id = task_id
        sms_record.succnums = succnums
        sms_record.retmsg = response
        sms_record.status = success and pcfg.SMS_COMMIT or pcfg.SMS_ERROR
    sms_record.save()
    return succnums, success


def gen_package_post_sms_content(package_order, package_sku_item, delay_days):
    """
    :param delay_days: now - package_sku_item.pay_time
    :param package_sku_item: PackageSkuItem instance
    :param package_order: PackageOrder instance
    通过包裹单 和 短信模板 生成一条 短信内容信息
    """
    # 查找短信模板
    if not package_order.logistics_company:
        raise Exception(u'gen_package_post_sms_content:'
                        u'logistics_company not found, package_order id is %s' % package_order.id)
    if delay_days <= 3:
        sms_tpls = SMSActivity.objects.filter(sms_type=SMS_NOTIFY_POST, status=True)
        # 报！女王大人，前方{{logistics_company_name}}快递护卫队发来捷报，说已成功发出您的{{title}}，物流单号{{out_sid}}，
        # 现正火速送往您处，相信不日便可抵达。女王大人，请一定要保持电话通畅哦~【小鹿美美】
    else:
        sms_tpls = SMSActivity.objects.filter(sms_type=SMS_NOTIFY_DELAY_POST, status=True)
        # 公主大人，小鹿子有事禀报：您订的{{title}}衣，因厂家热销，供货紧缺，耽搁了{{later_days}}天。
        # 小鹿子现已责令{{logistics_company_name}}快递小哥快马加鞭送货。因此事造成的延误，恳请公主大人原谅！【小鹿美美】
    text_tmpls = [tpl.text_tmpl for tpl in sms_tpls]
    if not text_tmpls:
        logger.warn(u'gen_package_post_sms_content:'
                    u'sms template not found, package_order id is %s .' % package_order.id)
        return
    tpl_text = random.sample(text_tmpls, 1)[0]  # 随机选取一个模板
    if not tpl_text:
        return None

    logistics_company_full_name = package_order.logistics_company.name
    logistics_company_name = logistics_company_full_name[0:2] if logistics_company_full_name else ''

    package_order_dict = {
        'logistics_company_name': logistics_company_name,
        'title': package_sku_item.title.split("/")[0],
        'out_sid': package_order.out_sid,
        'later_days': delay_days
    }
    template = Template(tpl_text)
    context = Context(package_order_dict)
    return template.render(context)


@task()
def task_notify_package_post(package_order):
    """
    :param package_order: PackageOrder instance
    功能: 用户的订单发货了, 发送发货的短信通知 , package_order 称重的时候触发此任务执行.
    """
    platform = SMSPlatform.objects.filter(is_default=True).order_by('-id').first()  # step1: 选择默认短信平台商
    if not platform:
        logger.error(u"task_notify_package_post: SMSPlatform object not found !")
        return
    if package_order.is_send_sms or len(str(package_order.receiver_mobile).strip()) != 11:
        return  # 已经发过短信 或者 手机号不正确

    sms_manager = dict(SMS_CODE_MANAGER_TUPLE).get(platform.code, None)
    if not sms_manager:
        raise Exception(u'未找到短信服务商接口实现')

    package_sku_item = package_order.package_sku_items.first()
    if not package_sku_item:
        logger.warn(u'gen_package_post_sms_content:'
                    u'package_sku_item not found, package_order id is %s .' % package_order.id)
    now = datetime.datetime.now()
    delay_days = (now - package_sku_item.pay_time).days
    task_name = u"发货短信提示" if delay_days <= 3 else u'延迟发货通知'
    sms_notify_type = SMS_NOTIFY_POST if delay_days <= 3 else SMS_NOTIFY_DELAY_POST

    content = gen_package_post_sms_content(package_order, package_sku_item, delay_days)
    if not content:
        return
    manager = sms_manager()
    params = {
        'content': content,
        'userid': platform.user_id,
        'account': platform.account,
        'password': platform.password,
        'mobile': package_order.receiver_mobile,
        'taskName': task_name,
        'mobilenumber': 1,
        'countnumber': 1,
        'telephonenumber': 0,
        'action': 'send',
        'checkcontent': '0'
    }
    succnums, success = call_send_a_sms(manager, params, sms_notify_type)  # 调用短信发送
    if success:
        SMSPlatform.objects.filter(code=platform.code).update(sendnums=F('sendnums') + int(succnums))
        package_order.is_send_sms = True
        update_model_fields(package_order, update_fields=['is_send_sms'])
    return


def gen_lack_refund_sms_content(sale_order):
    """
    订货缺货退款短信通知内容
    """
    # 查找短信模板
    sms_tpls = SMSActivity.objects.filter(sms_type=SMS_NOTIFY_LACK_REFUND, status=True)
        # 公主大人，小鹿子有事禀报：您订的{{title}}衣，因厂家热销，供货紧缺，耽搁了{{later_days}}天。
        # 小鹿子现已责令{{logistics_company_name}}快递小哥快马加鞭送货。因此事造成的延误，恳请公主大人原谅！【小鹿美美】
    text_tmpls = [tpl.text_tmpl for tpl in sms_tpls]
    if not text_tmpls:
        logger.warn(u'gen_lack_refund_sms_content:'
                    u'sms template not found, sale_order id is %s .' % sale_order.id)
        return
    tpl_text = random.sample(text_tmpls, 1)[0]  # 随机选取一个模板
    if not tpl_text:
        return None

    title = sale_order.title
    payment  = round(sale_order.payment, 1)

    sale_order_dict = {
        'title': title,
        'payment': payment
    }
    template = Template(tpl_text)
    context = Context(sale_order_dict)
    return template.render(context)


@task()
def task_notify_lack_refund(sale_order):
    """
    :param package_order: PackageOrder instance
    功能: 用户的订单发货了, 发送发货的短信通知 , package_order 称重的时候触发此任务执行.
    """
    platform = SMSPlatform.objects.filter(is_default=True).order_by('-id').first()  # step1: 选择默认短信平台商
    if not platform:
        logger.error(u"task_notify_lack_refund: SMSPlatform object not found !")
        return
    if len(str(sale_order.sale_trade.receiver_mobile).strip()) != 11:
        return  # 已经发过短信 或者 手机号不正确

    sms_manager = dict(SMS_CODE_MANAGER_TUPLE).get(platform.code, None)
    if not sms_manager:
        raise Exception(u'未找到短信服务商接口实现')

    task_name = u"缺货短信提示"
    sms_notify_type = SMS_NOTIFY_LACK_REFUND
    content = gen_lack_refund_sms_content(sale_order)
    if not content:
        return
    manager = sms_manager()
    params = {
        'content': content,
        'userid': platform.user_id,
        'account': platform.account,
        'password': platform.password,
        'mobile': sale_order.sale_trade.receiver_mobile,
        'taskName': task_name,
        'mobilenumber': 1,
        'countnumber': 1,
        'telephonenumber': 0,
        'action': 'send',
        'checkcontent': '0'
    }
    succnums, success = call_send_a_sms(manager, params, sms_notify_type)  # 调用短信发送
    if success:
        SMSPlatform.objects.filter(code=platform.code).update(sendnums=F('sendnums') + int(succnums))
    return


def gen_later_not_post_sms_content(sale_order, trade):
    """
    :param trade: SaleOrder.SaleTrade
    :type sale_order: object SaleOrder
    生成 SaleOrder 的延迟没有发货 短信内容
    """
    sms_tpls = SMSActivity.objects.filter(
        sms_type=SMS_NOTIFY_GOODS_LATER,
        status=True
    )
    # 报！女王大人，因您购买的{{title}}衣实在太美，在半路被氪星人劫持。经小鹿子和蝙蝠侠的奋勇拼搏，终于成功夺回，现责
    # 令{{logistics_company_name}}快递小哥快马加鞭送货。因此事造成了{{later_days}}天延误，恳请女王大人原谅！【小鹿美美】
    text_tmpls = [tpl.text_tmpl for tpl in sms_tpls]
    if not text_tmpls:
        logger.warn(u'send_later_post_notify:'
                    u'sms template not found, sale_order id is %s .' % sale_order.id)
        return
    tpl_text = random.sample(text_tmpls, 1)[0]  # 随机选取一个模板
    if not tpl_text:
        return
    if not trade.logistics_company:
        logistics_company_name = u''
    else:
        logistics_company_name = trade.logistics_company.name[0:2]
    now = datetime.datetime.now()
    later_days = (now - trade.pay_time).days
    template = Template(tpl_text)

    sale_order_dict = {
        'logistics_company_name': logistics_company_name,
        'title': sale_order.title.split("/")[0],
        'later_days': later_days,
    }
    context = Context(sale_order_dict)
    return template.render(context)


def send_later_not_post_notify(sale_order):
    """
    :param sale_order: SaleOrder instance
    发送 还没有发货 短信通知
    """
    platform = SMSPlatform.objects.filter(is_default=True).order_by('-id').first()  # step1: 选择默认短信平台商
    if not platform:
        logger.error(u"send_later_post_notify: SMSPlatform object not found !")
        return
    try:
        trade = sale_order.sale_trade
        already_send = SendLaterTrade.objects.filter(trade_id=trade.id, success=True).first()
        if already_send:
            return  # 如果已经发送过了 则 return
        mobile = trade.receiver_mobile
        if len(str(trade.receiver_mobile).strip()) != 11:
            return  # 已经发过短信 或者 手机号不正确
        sms_manager = dict(SMS_CODE_MANAGER_TUPLE).get(platform.code, None)
        if not sms_manager:
            raise Exception(u'未找到短信服务商接口实现')
        content = gen_later_not_post_sms_content(sale_order, trade)
        if not content:
            return
        manager = sms_manager()
        params = {
            'content': content,
            'userid': platform.user_id,
            'account': platform.account,
            'password': platform.password,
            'mobile': mobile,
            'taskName': "小鹿美美延迟未发货通知",
            'mobilenumber': 1,
            'countnumber': 1,
            'telephonenumber': 0,
            'action': 'send',
            'checkcontent': '0'
        }
        succnums, success = call_send_a_sms(manager, params, SMS_NOTIFY_GOODS_LATER)  # 调用短信发送
        if success:
            SMSPlatform.objects.filter(code=platform.code).update(sendnums=F('sendnums') + int(succnums))
            # 记录是否发送
            send_success = SendLaterTrade(trade_id=trade.id, success=True)
            send_success.save()
    except Exception, exc:
        logger.error(exc.message or u'send_later_post_notify: sale id is :%s' % sale_order.id, exc_info=True)

# TODO 缺货退款通知

@task()
def task_deliver_goods_later():
    """ 付款五天未发货通知 """
    if True:  # 不发送该 短信通知 即 超 时 没有发货的订单不会提醒用户短信
        return
    from flashsale.pay.models import SaleOrder
    today = datetime.date.today()
    all_orders = SaleOrder.objects.filter(  # 已付款  在 前 5 天 到 4 天之间的 sale_order
        status=SaleOrder.WAIT_SELLER_SEND_GOODS,
        pay_time__gte=today - datetime.timedelta(days=5),
        pay_time__lt=today - datetime.timedelta(days=4)
    )

    for order in all_orders:
        trade = order.sale_trade
        already_send = SendLaterTrade.objects.filter(trade_id=trade.id, success=True).first()
        if already_send:  # 如果已经发送过了 则 return
            return
        send_later_not_post_notify(order)


@task()
def task_register_code(mobile, send_type="1"):
    """ 短信验证码 """
    # 选择默认短信平台商，如果没有，任务退出
    platform = SMSPlatform.objects.filter(is_default=True).order_by('-id').first()
    if not platform:
        logger.error(u"task_notify_package_post: SMSPlatform object not found !")
        return
    try:
        reg = Register.objects.filter(vmobile=mobile).order_by('-modified')[0]
        if send_type == "1":
            content = u"验证码：" + reg.verify_code + "，请在注册页面输入完成验证。如非本人操作请忽略。"
        elif send_type == "2":
            content = u"验证码：" + reg.verify_code + "，请即时输入并重置密码，为保证您的账户安全，请勿外泄。如有疑问请致电400-823-5355"
        elif send_type == "3":
            content = u"验证码：" + reg.verify_code + "，请在手机验证页面输入校验。如非本人操作请忽略。"
        elif send_type == "4":
            content = u"验证码：" + reg.verify_code + "，请在提现页面输入校验。如非本人操作请忽略。"

        if not content:
            return
        params = {
            'content': content,
            'userid': platform.user_id,
            'account': platform.account,
            'password': platform.password,
            'mobile': mobile,
            'taskName': "小鹿美美验证码",
            'mobilenumber': 1,
            'countnumber': 1,
            'telephonenumber': 0,
            'action': 'send',
            'checkcontent': '0'
        }

        sms_manager = dict(SMS_CODE_MANAGER_TUPLE).get(platform.code, None)
        if not sms_manager:
            raise Exception('未找到短信服务商接口实现')

        manager = sms_manager()
        success = False

        # 创建一条短信发送记录
        sms_record = manager.create_record(params['mobile'], params['taskName'], SMS_NOTIFY_VERIFY_CODE,
                                           params['content'])
        # 发送短信接口
        try:
            success, task_id, succnums, response = manager.batch_send(**params)
        except Exception, exc:
            sms_record.status = pcfg.SMS_ERROR
            sms_record.memo = exc.message
            logger.error(exc.message, exc_info=True)
        else:
            sms_record.task_id = task_id
            sms_record.succnums = succnums
            sms_record.retmsg = response
            sms_record.status = success and pcfg.SMS_COMMIT or pcfg.SMS_ERROR
        sms_record.save()
        if success:
            SMSPlatform.objects.filter(code=platform.code).update(sendnums=F('sendnums') + int(succnums))
    except Exception, exc:
        logger.error(exc.message or 'empty error', exc_info=True)
