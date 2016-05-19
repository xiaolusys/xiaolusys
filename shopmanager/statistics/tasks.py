# coding=utf-8
import logging
import datetime
from celery.task import task
from django.db.models import Sum
from django.contrib.auth.models import User
from shopback.items.models import Product
from flashsale.pay.models_custom import ModelProduct
from supplychain.supplier.models import SupplierCharge, SaleSupplier
from flashsale.pay.models import SaleOrder

from statistics.models import SaleStats

logger = logging.getLogger(__name__)


@task()
def task_statistics_product_sale_num(sale_time_left, sale_time_right, category):
    """ 实时统计页面任务 """
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


@task()
def task_update_sale_order_stats_record(sale_order):
    """
    更新统计模块的 SaleOrderStatsRecord 记录
    """
    from statistics.models import SaleOrderStatsRecord

    date_field = sale_order.pay_time.date() if sale_order.pay_time else sale_order.created.date()

    if sale_order.stats_not_pay():
        status = SaleOrderStatsRecord.NOT_PAY
    elif sale_order.stats_paid():
        status = SaleOrderStatsRecord.PAID
    elif sale_order.stats_cancel():
        status = SaleOrderStatsRecord.CANCEL
    elif sale_order.stats_out_stock():
        status = SaleOrderStatsRecord.OUT_STOCK
    elif sale_order.stats_return_goods():
        status = SaleOrderStatsRecord.RETURN_GOODS
    else:
        return
    record = SaleOrderStatsRecord.objects.filter(oid=sale_order.oid).first()
    if not record:
        record = SaleOrderStatsRecord(
            oid=sale_order.oid,
            outer_id=sale_order.outer_id,
            sku_id=sale_order.outer_id + '/' + sale_order.outer_sku_id,
            name=sale_order.title + '/' + sale_order.sku_name,
            pic_path=sale_order.pic_path,
            num=sale_order.num,
            payment=sale_order.payment,
            pay_time=sale_order.pay_time,
            date_field=date_field,
            status=status
        )
        if status == SaleOrderStatsRecord.RETURN_GOODS:
            record.return_goods = SaleOrderStatsRecord.HAS_RETURN
        record.save()
    else:
        if record.status != status:
            record.status = status
            update_fields = ['status']
            if record.date_field != date_field:
                record.date_field = date_field
                update_fields.append('date_field')
            if status == SaleOrderStatsRecord.RETURN_GOODS:
                record.return_goods = SaleOrderStatsRecord.HAS_RETURN
                update_fields.append('return_goods')
            record.save(update_fields=update_fields)


def calculate_sku_sale_stats(sku_id=None, date_field=None):
    """ 计算sku的数量 信息 """
    from statistics.models import SaleOrderStatsRecord
    records = SaleOrderStatsRecord.objects.filter(sku_id=sku_id,
                                                  date_field=date_field)
    return records.values('status').annotate(total_num=Sum('num'),
                                             total_payment=Sum('payment'))


def make_sale_stat_uni_key(date_field, current_id, record_type, status):
    """ make the sale stat unique key """
    return '/'.join([str(date_field), str(current_id), str(record_type), str(status)])


def gen_status_data_map(stats):
    data = {}
    for k in SaleStats.STATUS:
        key = k[0]
        data[key] = {"total_num": 0, "total_payment": 0}
    for s in stats:
        key = s['status']
        data[key]['total_num'] = s['total_num']
        data[key]['total_payment'] = s['total_payment']
    return data


def find_parent_record_type(stats):
    current_type = stats.record_type
    for stats_type in SaleStats.RECORD_TYPES:
        if stats_type[0] > current_type:
            return stats_type[0]
    return None


@task()
def task_statsrecord_update_salestats(stats_record):
    """
    :type stats_record: SaleOrderStatsRecord instance
    """
    current_id = stats_record.sku_id

    date_field = stats_record.date_field
    stats = calculate_sku_sale_stats(current_id, date_field)

    data = gen_status_data_map(stats)
    for status, v in data.items():
        total_num = v['total_num']
        total_payment = v['total_payment']
        uni_key = make_sale_stat_uni_key(date_field, current_id, SaleStats.TYPE_SKU, status)
        old_stat = SaleStats.objects.filter(uni_key=uni_key).first()
        if not old_stat:
            if total_num > 0:
                st = SaleStats(
                    parent_id=stats_record.outer_id,
                    current_id=current_id,
                    date_field=date_field,
                    name=stats_record.name,
                    pic_path=stats_record.pic_path,
                    uni_key=uni_key,
                    record_type=SaleStats.TYPE_SKU,
                    status=status,
                    num=total_num,
                    payment=total_payment
                )
                st.save()
        else:
            update_fields = []
            if old_stat.num != total_num:
                old_stat.num = total_num
                update_fields.append('num')
            if old_stat.payment != total_payment:
                old_stat.payment = total_payment
                update_fields.append('payment')
            if update_fields:
                old_stat.save(update_fields=update_fields)


def get_product_name_pic_path(outer_id):
    product = Product.objects.filter(outer_id=outer_id).first()
    if product:
        return product.name, product.pic_path
    return None, None


def get_model_id(product_outer_id):
    product = Product.objects.filter(outer_id=product_outer_id).first()
    if product:
        return product.model_id
    return None


def get_supplier_id(model_id):
    product = Product.objects.filter(model_id=model_id).first()
    if product:
        sal_p, supplier = product.pro_sale_supplier()
        if supplier:
            return supplier.id
    return None


def get_supplier_name_and_pic_path(supplier_id):
    supplier = SaleSupplier.objects.filter(id=supplier_id).first()
    if supplier:
        return supplier.supplier_name, supplier.main_page
    return None, None


def get_model_name_and_picpath(model_id):
    model = ModelProduct.objects.filter(id=model_id).first()
    if model:
        return model.name, model.head_imgs
    return None, None


def get_bd_id(supplier_id):
    charger = SupplierCharge.objects.filter(supplier_id=supplier_id).first()
    if charger:
        return charger.employee.id  # User ID
    return None


def get_bd_name_and_pic_path(bd_id):
    user = User.objects.filter(id=bd_id).first()
    if user:
        return user.username, ''
    return None, None


def get_parent_id_name_and_pic_path(record_type, target_id, date_field=None):
    if record_type == SaleStats.TYPE_COLOR:
        model_id = get_model_id(target_id)
        name, pic_path = get_product_name_pic_path(target_id)
        return model_id, name, pic_path

    if record_type == SaleStats.TYPE_MODEL:
        supplier_id = get_supplier_id(target_id)
        name, pic_path = get_model_name_and_picpath(target_id)
        return supplier_id, name, pic_path

    if record_type == SaleStats.TYPE_SUPPLIER:
        bd_id = get_bd_id(target_id)
        name, pic_path = get_supplier_name_and_pic_path(target_id)
        return bd_id, name, pic_path
    if record_type == SaleStats.TYPE_BD:
        name, pic_path = get_bd_name_and_pic_path(target_id)
        return date_field, name, pic_path
    return None, None, None


@task()
def task_update_parent_sale_stats(sale_stats):
    parent_id = sale_stats.parent_id
    if not parent_id and sale_stats.record_type != SaleStats.TYPE_TOTAL:
        logger.error('task_update_parent_sale_stats: current id  is %s' % sale_stats.current_id)
        print "current_id :", sale_stats.current_id, sale_stats.get_record_type_display()
        return

    stats = SaleStats.objects.filter(
        parent_id=parent_id, date_field=sale_stats.date_field,
    ).values('status').annotate(total_num=Sum('num'), total_payment=Sum('payment'))  # 同等级的数据计算

    data = gen_status_data_map(stats)

    date_field = sale_stats.date_field
    record_type = find_parent_record_type(sale_stats)
    if not record_type:
        return
    for status, v in data.iteritems():
        total_num = v['total_num']
        total_payment = v['total_payment']
        uni_key = make_sale_stat_uni_key(date_field, parent_id, record_type, status)

        old_stat = SaleStats.objects.filter(uni_key=uni_key).first()
        if not old_stat:
            if total_num > 0:
                # print "total num :", total_num, sale_stats.get_record_type_display()
                grand_parent_id, name, pic_path = get_parent_id_name_and_pic_path(record_type, parent_id, date_field)
                st = SaleStats(
                    parent_id=grand_parent_id,
                    current_id=parent_id,
                    date_field=date_field,
                    name=name,
                    pic_path=pic_path,
                    uni_key=uni_key,
                    record_type=record_type,
                    status=status,
                    num=total_num,
                    payment=total_payment
                )
                st.save()
        else:
            update_fields = []
            if old_stat.num != total_num:
                # print "total num :", total_num, sale_stats.get_record_type_display()
                old_stat.num = total_num
                update_fields.append('num')
            if old_stat.payment != total_payment:
                old_stat.payment = total_payment
                update_fields.append('payment')
            if update_fields:
                old_stat.save(update_fields=update_fields)
