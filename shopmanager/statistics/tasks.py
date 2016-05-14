# coding=utf-8
__author__ = 'jie.lin'
import logging
import datetime
from celery.task import task
from django.db.models import Sum
from shopback.items.models import Product
from flashsale.pay.models import SaleOrder

logger = logging.getLogger(__name__)


@task()
def task_statistics_product_sale_num(sale_time_left, sale_time_right, category):
    start_time = datetime.datetime.now()
    # 指定上架时间的产品
    products = Product.objects.filter(status='normal')
    if category == 'female':
        female = [18, 19, 20, 21, 22, 24, 8]
        products = Product.objects.filter(status='normal', category_id__in=female)
    elif category == 'child':
        child = [12, 13, 14, 15, 16, 17, 23, 25, 26, 5]
        products = Product.objects.filter(status='normal', category_id__in=child)

    products_info = products.filter(
        sale_time__gte=sale_time_left,
        sale_time__lte=sale_time_right).order_by('-sale_time').only(
        "id",
        "outer_id",
        "name",
        "category_id",
        "pic_path",
        "cost",
        "agent_price",
        "collect_num",
        "model_id",
    )

    data = {}
    item_id_annotate = SaleOrder.objects.filter(status__gte=2,
                                                status__lte=5,
                                                refund_status=0).filter(
        created__gte=sale_time_left,
        created__lte=sale_time_right).values('item_id').annotate(pro_sale_num=Sum('num'))  # 没有退款的订单 按照产品id分组

    for product in products_info:
        order_sales = item_id_annotate.filter(item_id=product.id)
        pro_sale_num = order_sales[0]['pro_sale_num'] if order_sales else 0

        if data.has_key(product.model_id):
            data[product.model_id]['collect_num'] += product.collect_num  # 库存累加
            data[product.model_id]['pro_sale_num'] += pro_sale_num  # 销量累加
        else:
            data[product.model_id] = {
                "model_id": product.model_id,
                "outer_id": product.outer_id,
                "name": product.name,
                "category_id": product.category_id,
                "pic_path": product.pic_path,
                "cost": product.cost,
                "agent_price": product.agent_price,
                "collect_num": product.collect_num,
                "pro_sale_num": pro_sale_num,
            }
    end_time = datetime.datetime.now()
    return {"data": data, "time_consuming": str(end_time - start_time)}
