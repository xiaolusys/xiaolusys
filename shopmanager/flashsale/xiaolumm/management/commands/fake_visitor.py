# coding=utf-8
import os
from datetime import datetime
from django.core.management.base import BaseCommand

from common.utils import update_model_fields
from flashsale.xiaolumm.models.models_fortune import UniqueVisitor


class Command(BaseCommand):
    def handle(self, *args, **options):
        """
        伪造妈妈访客
        """

        mama_id = 1
        unionid = 'fake_unionid%s' % os.urandom(6).encode('hex')
        nick = 'fake-nick'
        img = ''
        date_field = datetime.today().date()
        uni_key = 'fake-%s-%s' % (unionid, date_field.strftime('%Y-%m-%d'))

        visitor = UniqueVisitor(mama_id=mama_id, visitor_unionid=unionid, visitor_nick=nick,
                                visitor_img=img, uni_key=uni_key, date_field=date_field)
        visitor.save()
