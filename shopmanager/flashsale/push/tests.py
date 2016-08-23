# coding: utf-8
import os
import sys
sys.path.append('.')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.local_settings")
from flashsale.xiaolumm.models.models_fortune import OrderCarry
from flashsale.push.app_push import AppPush


if __name__ == '__main__':
    import django
    django.setup()
    ordercarry = OrderCarry.objects.get(id=10)

    customer_id = 913405
    target_url = 'http://baidu.com'
    msg = 'hello, this is app push test!'
    # resp = AppPush.push(customer_id, target_url, msg)
    # AppPush.push_mama_ordercarry(ordercarry)
    # for i in range(100):
    # AppPush.push_pass_through('CESHI')
    AppPush.push_mama_ordercarry_to_all(ordercarry)
