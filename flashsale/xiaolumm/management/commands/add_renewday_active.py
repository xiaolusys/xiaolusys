# coding=utf-8
import datetime

from django.core.management.base import BaseCommand

from common.utils import update_model_fields
from flashsale.xiaolumm.models import XiaoluMama
from flashsale.xiaolumm.models.models_fortune import ActiveValue


class Command(BaseCommand):
    def handle(self, *args, **options):
        """
        从今年3月1日开始，当天有活跃就增加1天妈妈截止日期
        """
        start_date = datetime.date(2016, 3, 1)
        end_date = datetime.date(2016, 7, 10)
        activites = ActiveValue.objects.filter(date_field__gte=start_date,
                                               date_field__lte=end_date)

        mms = XiaoluMama.objects.filter(status=XiaoluMama.EFFECT,
                                        agencylevel__gte=XiaoluMama.VIP_LEVEL,
                                        charge_status=XiaoluMama.CHARGED)
        print "mama count is %s" % mms.count()
        data_0 = []
        data_1 = []
        for mm in mms:
            renewdays = len(activites.filter(mama_id=mm.id).values('date_field').distinct())  # 活跃天数
            dic = {"mm": mm.id, "days": renewdays}
            if mm.id % 100 == 0:
                print 'mm id %s , old renew date is %s , renew days is %s .' % (mm.id, mm.renew_time, renewdays)
            data_1.append(dic) if renewdays > 0 else data_0.append(dic)
            if isinstance(mm.renew_time, datetime.datetime) and renewdays > 0:
                mm.renew_time = mm.renew_time + datetime.timedelta(days=renewdays)
                update_model_fields(mm, update_fields=['renew_time'])
        print "0 days mm count %s" % len(data_0)
        print "n days mm count %s" % len(data_1)

