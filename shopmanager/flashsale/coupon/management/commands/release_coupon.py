# coding=utf-8
import datetime
from django.core.management.base import BaseCommand
from flashsale.coupon.models import UserCoupon
from shopback.trades.models import PackageSkuItem
from flashsale.pay.models import SaleOrder


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('template', nargs='+', type=int,
                            help='assign a template id to release coupon')
        parser.add_argument('date_from', nargs='+', type=str,
                            help='assign a date_from to filter that date sal trade.')
        parser.add_argument('date_to', nargs='+', type=str,
                            help='assign a date_to to filter that date sal trade.')

    def date_split(self, date):
        year = int(date.split('-')[0])
        month = int(date.split('-')[1])
        day = int(date.split('-')[2])
        return year, month, day

    def handle(self, *args, **options):
        templateids = options.get('template')
        date_froms = options.get('date_from')
        date_tos = options.get('date_to')
        if templateids and date_froms and date_tos:
            template = templateids[0]
            date_from = date_froms[0]
            date_to = date_tos[0]
            try:
                year_f, month_f, day_f = self.date_split(date_from)
                year_t, month_t, day_t = self.date_split(date_to)
                date_from = datetime.date(year=year_f, month=month_f, day=day_f)
                date_to = datetime.date(year=year_t, month=month_t, day=day_t)
            except:
                print "date format is like this : '2016-04-05'"
                return
            print "release coupon template id is %s, " \
                  "the sale trade pay date is %s - %s." % (template, date_from, date_to)

            if isinstance(date_from, datetime.date) and isinstance(date_to, datetime.date):
                packages = PackageSkuItem.objects.filter(assign_time__range=(date_from, date_to),
                                                         assign_status=PackageSkuItem.FINISHED)
                print "sku 包裹数量为%s" % packages.count()
                count = 0
                for package in packages:
                    order = SaleOrder.objects.filter(id=package.sale_order_id).first()
                    try:
                        if order:
                            trade = order.sale_trade
                            print "release for customer %s ." % trade.buyer_id
                            UserCoupon.objects.create_normal_coupon(buyer_id=trade.buyer_id, template_id=template)
                            count += 1
                    except:
                        continue
                print "共发放优惠券 %s 张" % count
