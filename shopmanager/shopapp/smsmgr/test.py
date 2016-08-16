# encoding=utf8
import os
import sys
sys.path.append('.')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.settings")
from flashsale.xiaolumm.models.models_fortune import OrderCarry
from shopapp.smsmgr.sms_push import SMSPush


if __name__ == '__main__':
    import django
    django.setup()

    ordercarry = OrderCarry.objects.get(id=1)
    sms = SMSPush()
    sms.push_mama_ordercarry(ordercarry)
