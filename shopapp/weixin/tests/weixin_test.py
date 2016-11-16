# encoding=utf8
from __future__ import unicode_literals

import os
import sys
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shopmanager.local_settings')
# from shopapp.weixin.weixin_apis import WeiXinAPI
from shopapp.weixin.weixin_push import WeixinPush
from flashsale.pay.models.trade import SaleTrade, SaleOrder
from flashsale.pay.models.refund import SaleRefund
from flashsale.pay.models.user import Customer
from flashsale.xiaolumm.models.models_fortune import OrderCarry, AwardCarry


def test_main():
    ordercarry = OrderCarry.objects.get(id=10)
    push = WeixinPush()
    remarks = u'来自好友%s，快打开App看看她买了啥～' % ordercarry.contributor_nick
    to_url = 'http://m.xiaolumeimei.com/sale/promotion/appdownload/'
    # push.push_mama_ordercarry(ordercarry, remarks, to_url)
    mama_id = 1
    user_version = '1.1'
    latest_version = '1.2'
    # push.push_mama_update_app(mama_id, user_version, latest_version, remarks, to_url)
    # saletrade = SaleTrade.objects.get(id=1)
    # push.push_trade_pay_notify(saletrade)
    # push.push_deliver_notify(saletrade)
    # salerefund = SaleRefund.objects.get(id=11)
    # push.push_refund_notify(salerefund)
    awardcarry = AwardCarry.objects.get(id=1)
    courage_remarks = 'remark'
    to_url = ''
    push.push_mama_award(awardcarry, courage_remarks, to_url)


def test_push_new_mama_task():
    from flashsale.xiaolumm.tasks import task_push_new_mama_task
    from flashsale.xiaolumm.models.models import XiaoluMama
    from flashsale.xiaolumm.models.new_mama_task import NewMamaTask

    xlmm = XiaoluMama.objects.get(id=1)
    task_push_new_mama_task(xlmm, NewMamaTask.TASK_FIRST_FANS)


def test_push_clickcarry():
    from flashsale.xiaolumm.models.models_fortune import ClickCarry

    push = WeixinPush()
    clickcarry = ClickCarry.objects.filter().order_by('-created').first()
    push.push_mama_clickcarry(clickcarry)


def test_push_pintuan():
    from flashsale.pay.models.teambuy import TeamBuy

    customer = Customer.objects.filter(mobile='15716692522').first()
    push = WeixinPush()
    teambuy = TeamBuy.objects.filter(id=1).first()
    push.push_pintuan_need_more_people(teambuy, customer)


def test_push_salerefund():
    from flashsale.pay.models import SaleRefund
    salerefund = SaleRefund.objects.get(id=54103)
    push = WeixinPush()
    push.push_refund_notify(salerefund, 9)


def test_push_mama_coupon_audit():
    from flashsale.coupon.models.transfer_coupon import CouponTransferRecord

    coupon_record = CouponTransferRecord.objects.first()
    print coupon_record.id
    push = WeixinPush()
    push.push_mama_coupon_audit(coupon_record)


def test_send_msg():
    from shopapp.weixin.weixin_apis import WeiXinAPI
    # openid = 'our5huD8xO6QY-lJc1DTrqRut3us'
    openid = 'our5huNlWVnegDDtQ5BHy7qaaBYM'  #　子飞

    params = {
        'touser': openid,
        'msgtype': 'news',
        'news': {
            'articles': [
             {
                 'title': '小鹿美美｜欢迎加入小鹿妈妈！',
                 'description': '小鹿美美｜欢迎加入小鹿妈妈！',
                 'url': 'http://m.xiaolumeimei.com/mama_shop/html/greetings_mama.html',
                 'picurl': 'http://7xogkj.com1.z0.glb.clouddn.com/xiaolumm/manager/yaya.jpg'
             },
             ]
        }
    }

    wxapi = WeiXinAPI()
    wxapi.send_custom_message(params)


if __name__ == '__main__':
    import django
    django.setup()

    # test_push_new_mama_task()
    # test_push_clickcarry()
    # test_push_pintuan()
    # test_send_msg()
    test_push_mama_coupon_audit()
