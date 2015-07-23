import sys
from datetime import datetime

from django.core.management import setup_environ
import settings

setup_environ(settings)


from flashsale.clickrebeta.models import StatisticsShopping
from django.conf import settings
from shopapp.weixin.models import get_Unionid
from flashsale.xiaolumm.models import XiaoluMama




def cal_month_xlmm(month_start_date, month_end_date):
    result_list = []
    all_purchase = StatisticsShopping.objects.filter(shoptime__gte=month_start_date,
                                                     shoptime__lt=month_end_date).values("openid").distinct()
    all_purchase_num = all_purchase.count()
    history_purchase = StatisticsShopping.objects.filter(shoptime__lt=month_start_date).values("openid").distinct()
    history_purchase_detail = set([val['openid'] for val in history_purchase])

    all_purchase_detail = set([val['openid'] for val in all_purchase])
    all_purchase_detail_unionid = set(
        [get_Unionid(val['openid'], settings.WEIXIN_APPID) for val in all_purchase])

    repeat_user = all_purchase_detail & history_purchase_detail
    repeat_user_unionid = set([get_Unionid(val, settings.WEIXIN_APPID) for val in repeat_user])

    all_xlmm = XiaoluMama.objects.filter(charge_status=u'charged', agencylevel=2).values("openid").distinct()
    all_xlmm_detail = set([val['openid'] for val in all_xlmm])

    repeat_xlmm = repeat_user_unionid & all_xlmm_detail
    xlmm_num = all_purchase_detail_unionid & all_xlmm_detail
    result_list.append(
        {"month": month_start_date, "all_purchase_num": all_purchase_num, "repeat_user_num": len(repeat_user),
         "repeat_xlmm_num": len(repeat_xlmm), "xlmm_num": len(xlmm_num)}
    )
    print result_list


if __name__ == "__main__":

    if len(sys.argv) != 3:
        print >> sys.stderr, "usage: python *.py  <datefrom> <dateto>"
        sys.exit(1)

    df = datetime.strptime(sys.argv[1], "%Y-%m-%d")
    dt = datetime.strptime(sys.argv[2], "%Y-%m-%d")

    cal_month_xlmm(df, dt)

