# coding: utf-8

from django.core.management.base import BaseCommand

from flashsale.push import mipush


REGID = 'd//igwEhgBGCI2TG6lWqlO82fL14QglJcMxBww66Gtj6RM139iKJcfjhoinOtBuDIjLafAkDpOrD8mDI5zAx+7S5iW8EBb0xHiiEG2GhC8o='
class Command(BaseCommand):
    def handle(self, *args, **options):
        print mipush.mipush_of_ios.push_to_regid(REGID, {'target_url': 'v1'}, description='测试python脚本推送')
