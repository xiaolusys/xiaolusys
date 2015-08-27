# coding=utf-8
from .models import ClickCount
from shopmanager.flashsale.xiaolumm.models import Clicks, XiaoluMama
import datetime
from django.db.models.signals import post_save
from celery.task import task


def Create_Or_Change_Clickcount(sender, instance, created, **kwargs):
    task_Count_ClickCount_Info(instance, created)


post_save.connect(Create_Or_Change_Clickcount, sender=Clicks)


@task()
def task_Count_ClickCount_Info(instance=None, created=None):
    if created:
        today = datetime.datetime.today()
        # 这里只是补货创建记录　当有创建的时候　才会去获取或者修改该　点击统计的记录
        click_count, state = ClickCount.objects.get_or_create(date=today, linkid=instance.linkid)
        xlmm = XiaoluMama.objects.get(id=instance.linkid)
        if xlmm.agencylevel not in (2, 3):  # 未接管的不去统计
            return
        if state:  # 表示创建统计记录
            click_count.user_num = 1
            click_count.valid_num = 1
            click_count.click_num = 1
            click_count.date = today
            click_count.save()
        else:  # 表示获取到了　修改该统计记录
            time_from = datetime.datetime(today.year, today.month, today.day)
            time_to = datetime.datetime(today.year, today.month, today.day, 23, 59, 59)
            clicks = Clicks.objects.filter(click_time__range=(time_from, time_to), linkid=xlmm.id)
            click_count.click_num += 1  # 累加１
            if instance.isvalid:
                click_count.valid_num = clicks.filter(isvalid=True).values('openid').distinct().count()  # 有效点击数量
                click_count.user_num = clicks.values('openid').distinct().count()  # 点击人数
                click_count.save()
