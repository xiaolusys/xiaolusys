# coding=utf-8
"""
代理相关的推送信息
"""
from celery.task import task
from flashsale.xiaolumm.models import XiaoluMama
from flashsale.push import push_mama
from flashsale.xiaolumm.util_emoji import gen_emoji, match_emoji
from shopapp.weixin.models import WeixinUnionID


@task
def task_push_ninpic_remind(ninpic):
    """
    当有九张图更新的时候推送
    因为考虑到一天有很多的九张图推送，暂定一天值推送第一次九张图
    """
    title = ninpic.title
    emoji_message = gen_emoji(title)
    message = match_emoji(emoji_message)
    push_mama.push_msg_to_topic_mama(message)


@task
def task_push_mama_order_msg(saletrade):
    """
    当代理有订单成功付款后则推送消息
    """
    mm_linkid = saletrade.extras_info.get('mm_linkid')
    if not mm_linkid:
        return
    mamas = XiaoluMama.objects.filter(charge_status=XiaoluMama.CHARGED, id=mm_linkid)
    map(push_mama.push_msg_to_mama(None), mamas)


@task
def task_push_mama_cashout_msg(envelop):
    """ 代理提现成功推送 """
    recipient = envelop.recipient
    weixin_records = WeixinUnionID.objects.filter(openid=recipient)
    if weixin_records.exists():
        unionid = weixin_records[0].unionid
        mamas = XiaoluMama.objects.filter(openid=unionid)
        map(push_mama.push_msg_to_mama(None), mamas)
