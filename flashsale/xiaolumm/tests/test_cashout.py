# encoding=utf8
import os
import sys
import time
sys.path.append('.')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.local_settings")
import datetime
from flashsale.xiaolumm.models.models_fortune import MamaFortune
from flashsale.xiaolumm.models.models import CashOut
from django.db import transaction
from django.db.models import F, Sum


CASHOUT_HISTORY_LAST_DAY_TIME = datetime.datetime(2016, 3, 30, 23, 59, 59)


def main(s, money, mama_id):
    # mama_id = 1

    # cashout_sum = CashOut.objects.filter(xlmm=mama_id, approve_time__gt=CASHOUT_HISTORY_LAST_DAY_TIME).values(
    #     'status').annotate(total=Sum('value'))
    # print cashout_sum

    # mf = MamaFortune.objects.filter(mama_id=mama_id).first()
    # MamaFortune.objects.filter(mama_id=mama_id).update(carry_cashout=mf.carry_cashout - money)

    # MamaFortune.objects.filter(mama_id=mama_id).update(carry_cashout=F('carry_cashout')-money)

    with transaction.atomic():
        mf = MamaFortune.objects.select_for_update().filter(mama_id=mama_id).first()
        time.sleep(s)
        MamaFortune.objects.filter(mama_id=mama_id).update(carry_cashout=mf.carry_cashout-money)


if __name__ == '__main__':
    s = int(sys.argv[1])
    money = int(sys.argv[2])
    mama_id = int(sys.argv[3])
    main(s, money, mama_id)
