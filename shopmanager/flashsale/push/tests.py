# coding: utf-8
import os
import sys
sys.path.append('.')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.settings")
from flashsale.xiaolumm.models.models_fortune import OrderCarry
from flashsale.push.app_push import AppPush


if __name__ == '__main__':
    import django
    django.setup()
    ordercarry = OrderCarry.objects.get(id=1)
    # AppPush.push_mama_ordercarry(ordercarry)
    AppPush.push_pass_through(913405)
