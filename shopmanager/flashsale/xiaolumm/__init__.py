from flashsale.xiaolumm.models import CarryLog
import datetime

carry_logs = CarryLog.objects.all()
for cl in carry_logs:
    if cl.log_type in (CarryLog.ORDER_REBETA,CarryLog.CLICK_REBETA):
        on = '20'+str(cl.order_num)
        cl.carry_date = datetime.datetime.strptime(on,'%Y%m%d')
    else:
        cl.carry_date = cl.created.date()
    cl.save()