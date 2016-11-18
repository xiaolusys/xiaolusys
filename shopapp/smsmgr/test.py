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

