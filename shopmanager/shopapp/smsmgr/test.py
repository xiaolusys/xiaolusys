# encoding=utf8
import os
import sys
sys.path.append('.')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.local_settings")
from flashsale.xiaolumm.models.models_fortune import OrderCarry
from shopapp.smsmgr.sms_push import SMSPush
from flashsale.xiaolumm.models.models import XiaoluMama


if __name__ == '__main__':
    import django
    django.setup()

    # ordercarry = OrderCarry.objects.get(id=1)
    xlmm = XiaoluMama.objects.get(id=1)
    customer = xlmm.get_customer()
    sms = SMSPush()
    sms.push_mama_subscribe_weixin(customer)
    # sms.push_mama_ordercarry(ordercarry)


def deposit_msg():
    from flashsale.pay.models import Customer
    from flashsale.coupon.models import UserCoupon
    from shopapp.smsmgr.sms_push import SMSPush
    coupons = UserCoupon.objects.filter(template_id=121, status=UserCoupon.UNUSED, is_pushed=False)
    print "count : ", coupons.count()
    push = SMSPush()
    content = u'您的200元已经到账，快打开App查看。小鹿美美送钱，加入就送230元！随意购物，无门槛，无期限！快告诉好友闺蜜吧！【小鹿美美】'
    for coupon in coupons:
        customer = Customer.objects.get(id=coupon.customer_id)
        xlmm = customer.get_xiaolumm()
        mobile = xlmm.mobile
        if len(mobile) != 11:
            mobile = customer.mobile
        if len(mobile) != 11:
            continue
        push.push(mobile, content=content, sms_notify_type='tocity')
        coupon.is_pushed = True
        coupon.save(update_fields=['is_pushed'])
