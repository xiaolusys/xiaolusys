# coding=utf-8
"""
代理相关的推送信息
"""
from celery.task import task
from flashsale.xiaolumm.models import XiaoluMama
from flashsale.push.mipush import mipush_of_ios, mipush_of_android
from flashsale.protocol import get_target_url
from flashsale.protocol import constants
from flashsale.xiaolumm.util_emoji import match_emoji
from shopmanager import settings
from shopapp.weixin.models import WeixinUnionID

def push_msg_to_mama(message):
    """ 发送九张图更新app推送 """

    def _wrapper(mama):
        customer = mama.get_mama_customer()
        if not customer:
            return
        customer_id = customer.id
        target_url = get_target_url(constants.TARGET_TYPE_HOME_TAB_1)
        if message:
            mipush_of_android.push_to_account(customer_id,
                                              {'target_url': target_url},
                                              description=message)
            mipush_of_ios.push_to_account(customer_id,
                                          {'target_url': target_url},
                                          description=message)

    return _wrapper


@task
def task_push_ninpic_remind(ninpic):
    """
    当有九张图更新的时候推送
    因为考虑到一天有很多的九张图推送，暂定一天值推送第一次九张图
    """
    description = ninpic.description
    message = match_emoji(description)
    turns_num = int(ninpic.turns_num)
    if turns_num != 1:  # 不是第一轮创建则不推送(每天仅仅推送一轮)
        return
    mamas = XiaoluMama.objects.filter(charge_status=XiaoluMama.CHARGED)
    map(push_msg_to_mama(message), mamas)


@task
def task_push_mama_order_msg(saletrade):
    """
    当代理有订单成功付款后则推送消息
    """
    mm_linkid = int(saletrade.extras_info.get('mm_linkid'))
    if not mm_linkid:
        return
    message = '又有顾客在您的专属链接下单啦~ 赶快看看提成吧~'
    mamas = XiaoluMama.objects.filter(charge_status=XiaoluMama.CHARGED, id=mm_linkid)
    map(push_msg_to_mama(message), mamas)


@task
def task_push_mama_cashout_msg(envelop):
    """ 代理提现成功推送 """
    recipient = envelop.recipient
    weixin_records = WeixinUnionID.objects.filter(openid=recipient)
    if weixin_records.exists():
        unionid = weixin_records[0].unionid
        mamas = XiaoluMama.objects.filter(openid=unionid)
        message = '提现红包已经发送啦 抓紧领取哦~'
        map(push_msg_to_mama(message), mamas)
