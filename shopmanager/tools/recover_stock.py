from shopback.items.models import Product,ProductSku,ItemNumTaskLog
import datetime

def recover():

    two_days_ago = datetime.datetime(2014,4,5)
    one_days_ago = datetime.datetime(2014,4,10)
    num_logs = ItemNumTaskLog.objects.filter(start_at__gte=two_days_ago,end_at__lte=one_days_ago)
    for log in num_logs:
        sku = ProductSku.objects.get(product__outer_id=log.outer_id,outer_id=log.sku_outer_id)
        if sku.quantity == 0 and log.num > 0:
            print log.outer_id,log.sku_outer_id,sku.name,log.num
