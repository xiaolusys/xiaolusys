# coding=utf-8
__author__ = 'meron'
import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

PASS_CHARS = list('1234567890abcdefghijklmnopqrstuvwxyz')

genPassword=lambda:random.sample(list(PASS_CHARS),8)

class Command(BaseCommand):
    def handle(self, *args, **options):
        staffs = User.objects.filter(is_staff=True)
        print 'reset staff password start ...'
        print ','.join(['username', 'password', 'last_logintime'])
        for staff in staffs:
            pwd = genPassword()
            staff.set_password(pwd)
            staff.save()

            print ','.join([staff.username, pwd, staff.last_login])
        print 'reset staff password success ...'