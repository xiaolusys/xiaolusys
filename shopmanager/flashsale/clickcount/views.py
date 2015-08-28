# coding=utf-8
from flashsale.clickcount.models import ClickCount
from shopmanager.flashsale.xiaolumm.models import Clicks, XiaoluMama
import datetime
from django.db.models.signals import post_save
from flashsale.clickcount.tasks import task_Count_ClickCount_Info


def Create_Or_Change_Clickcount(sender, instance, created, **kwargs):
    task_Count_ClickCount_Info.s(instance, created)()


post_save.connect(Create_Or_Change_Clickcount, sender=Clicks)

