# encoding:utf-8
from .models import ProductDaySale, Product


def updateProductDaySaleOuterid():
    pss = ProductDaySale.objects.all()
    product_ids = [p['product_id'] for p in pss.values('product_id').distinct()]
    cnt = 0
    print 'debug total:', len(product_ids)
    for pid in product_ids:
        try:
            product = Product.objects.get(id=pid)
        except:
            continue
        pss.filter(product_id=pid).update(outer_id=product.outer_id)

        cnt += 1
        if cnt % 1000 == 0:
            print cnt


import datetime


def updateProductDayStatSaletime():
    """ 更新每日订单商品统计上架时间 """
    pss = ProductDaySale.objects.filter(user_id__in=(7, 12),
                                        day_date__gte=datetime.datetime(2015, 1, 1)) \
        .order_by('day_date').values_list('day_date', 'product_id').distinct()
    cnt = 0
    total_count = pss.count()
    print 'debug: total=', total_count
    for p in pss:
        day_date, product_id = p
        pre_date = day_date - datetime.timedelta(days=1)
        ps_sale_time = day_date
        pre_p = ProductDaySale.objects.filter(product_id=product_id, day_date=pre_date)
        if pre_p.count() > 0 and pre_p[0].sale_time:
            ps_sale_time = pre_p[0].sale_time

        pds_qs = ProductDaySale.objects.filter(product_id=product_id, day_date=day_date)
        pds_qs.update(sale_time=ps_sale_time)

        cnt += 1
        if cnt % 100 == 0:
            print cnt
