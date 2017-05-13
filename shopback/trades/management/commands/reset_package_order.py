# coding=utf-8

from django.core.management.base import BaseCommand
import json
from shopback.trades.models import PackageSkuItem,PackageOrder
from shopback.logistics.models import LogisticsCompany

## 重新设置我们仓库韵达快递发货
##起因是有一些单子第三方发货改成仓库发货的时候,PackageSkuItem,PackageOrder莫名有了不是韵达的运单号,所以必须要清空物流数据,仓库才好发货

##用法 python manage.py reset_package_order -id 202753,32131,321321
class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '-id', '--package_sku_item_id', action='store', dest='package_sku_item_id',
            type=str,
        )

    def handle(self, *args, **options):
        ids = options.get("package_sku_item_id")
        ids = ids.split(',')
        print ids
        lc=LogisticsCompany.objects.get(kd100_express_key='yunda',status=True)
        for i in ids:
            PackageSkuItem.objects.filter(id=i).update(assign_status=PackageSkuItem.ASSIGNED,out_sid='',logistics_company_name='',ware_by=1)#psi设置已备货,清空物流数据,仓库设置为上海仓
            psi = PackageSkuItem.objects.get(id=i)
            sale_order=PackageSkuItem.objects.get(id=i).get_relate_order()
            sale_order.status=2
            sale_order.save()  #相应的saleorder设置会已付款状态
            PackageOrder.objects.filter(pid=psi.package_order_pid).update(status='WAIT_PREPARE_SEND_STATUS',out_sid='',logistics_company_id=lc.id,ware_by=1) # 包裹清空物流数据,设置上海仓,设置物流为韵达

