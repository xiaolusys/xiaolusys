# coding=utf-8
import os
import random
from datetime import datetime
from django.core.management.base import BaseCommand

from flashsale.xiaolumm.models.models_fortune import UniqueVisitor


class Command(BaseCommand):
    def handle(self, *args, **options):
        """
        伪造妈妈访客
        """

        filepath = '/home/aladdin/code/xiaolusys-houtai/shopmanager/mama_id_A.txt'
        with open(filepath) as f:
            mamas = f.readlines()
            mamas = map(lambda x: int(x.strip()), mamas)

        visitors = UniqueVisitor.objects.exclude(visitor_nick='', visitor_img='') \
            .values('visitor_nick', 'visitor_img')[:1000]

        for i, mama_id in enumerate(mamas):
            fake_visitor = random.choice(visitors)
            unionid = 'fake_%s' % os.urandom(10).encode('hex')
            nick = fake_visitor['visitor_nick']
            img = fake_visitor['visitor_img']
            date_field = datetime.today().date()
            uni_key = 'fake-%s-%s' % (unionid, date_field.strftime('%Y-%m-%d'))

            visitor = UniqueVisitor(mama_id=mama_id, visitor_unionid=unionid, visitor_nick=nick,
                                    visitor_img=img, uni_key=uni_key, date_field=date_field)
            visitor.save()
            print i, mama_id
