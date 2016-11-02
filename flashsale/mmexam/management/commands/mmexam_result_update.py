# coding=utf-8
from django.core.management.base import BaseCommand
from flashsale.mmexam.models import Result
from flashsale.xiaolumm.models import XiaoluMama


class Command(BaseCommand):
    def handle(self, *args, **options):
        print "mmexam command is running !"
        rs = Result.objects.filter(customer_id=0)
        print "in flush data programing count is %s:" % rs.count()
        for r in rs:
            try:
                xlmm = XiaoluMama.objects.get(openid=r.daili_user)
                cu = xlmm.get_mama_customer()
                r.customer_id = cu.id
                r.xlmm_id = xlmm.id
                r.save(update_fields=['xlmm_id', 'customer_id'])
            except:
                print "rs %d has no customer ,that will be delete" % r.id
                r.delete()
                continue
