# coding=utf-8
import logging
import datetime
import calendar
from celery.task import task
from django.db.models import Sum
from django.contrib.auth.models import User
from shopback.items.models import Product
from flashsale.pay.models_custom import ModelProduct
from supplychain.supplier.models import SupplierCharge, SaleSupplier
from flashsale.pay.models import SaleOrder
from statistics import constants

from statistics.models import SaleStats, ProductStockStat

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

    order_time_right = datetime.datetime.strptime(sale_time_right, '%Y-%m-%d') + datetime.timedelta(days=3)

    item_id_annotate = SaleOrder.objects.filter(status__gte=2,
                                                status__lte=5,
                                                refund_status=0).filter(
        created__gte=sale_time_left,
        created__lte=order_time_right).values('item_id').annotate(pro_sale_num=Sum('num'))  # 没有退款的订单 按照产品id分组

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
        status = constants.NOT_PAY
    elif sale_order.stats_paid():
        status = constants.PAID
    elif sale_order.stats_cancel():
        status = constants.CANCEL
    elif sale_order.stats_out_stock():
        status = constants.OUT_STOCK
    elif sale_order.stats_return_goods():
        status = constants.RETURN_GOODS
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
        if status == constants.RETURN_GOODS:
            record.return_goods = constants.HAS_RETURN
        record.save()
    else:
        if record.status != status:
            record.status = status
            update_fields = ['status']
            if record.date_field != date_field:
                record.date_field = date_field
                update_fields.append('date_field')
            if status == constants.RETURN_GOODS:
                record.return_goods = constants.HAS_RETURN
                update_fields.append('return_goods')
            record.save(update_fields=update_fields)


def calculate_sku_sale_stats(sku_id=None, date_field=None):
    """ 计算sku的数量 信息 """
    from statistics.models import SaleOrderStatsRecord

    records = SaleOrderStatsRecord.objects.filter(sku_id=sku_id,
                                                  date_field=date_field)
    return records.values('status').annotate(total_num=Sum('num'),
                                             total_payment=Sum('payment'))


def make_sale_stat_uni_key(date_field, current_id, record_type, timely_type, status):
    """ make the sale stat unique key """
    return '/'.join([str(date_field), str(current_id), str(record_type), str(timely_type), str(status)])


def gen_status_data_map(stats):
    data = {}
    for k in constants.STATUS:
        key = k[0]
        data[key] = {"total_num": 0, "total_payment": 0}
    for s in stats:
        key = s['status']
        data[key]['total_num'] = s['total_num']
        data[key]['total_payment'] = s['total_payment']
    return data


def find_parent_record_type(stats):
    current_type = stats.record_type
    for stats_type in constants.RECORD_TYPES:
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
    # 统计sku类型的数据 销量 和 销售额内容
    stats = calculate_sku_sale_stats(current_id, date_field)

    data = gen_status_data_map(stats)
    for status, v in data.iteritems():
        total_num = v['total_num']
        total_payment = v['total_payment']
        uni_key = make_sale_stat_uni_key(date_field, current_id,
                                         constants.TYPE_SKU,
                                         constants.TIMELY_TYPE_DATE,
                                         status)
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
                    record_type=constants.TYPE_SKU,
                    timely_type=constants.TIMELY_TYPE_DATE,
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
    logger.warn(u'get_model_id not found the product_outer_id is %s' % product_outer_id)
    return None


def get_supplier_id(model_id):
    product = Product.objects.filter(model_id=model_id).first()
    if product:
        sal_p, supplier = product.pro_sale_supplier()
        if supplier:
            return supplier.id
    logger.warn(u'get_supplier_id not found the supplier, the model_id is %s' % model_id)
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
    charger = SupplierCharge.objects.filter(
        supplier_id=supplier_id,
        status=SupplierCharge.EFFECT
    ).order_by("-id").first()  # 有效状态的最新的接管人
    if charger:
        return charger.employee.id  # User ID
    logger.warn(u'get_bd_id not found the bd, the supplier_id is %s' % supplier_id)
    return None


def get_bd_name_and_pic_path(bd_id):
    user = User.objects.filter(id=bd_id).first()
    if user:
        return user.username, ''
    return None, None


def get_parent_id_name_and_pic_path(record_type, target_id, date_field=None):
    if record_type == constants.TYPE_COLOR:
        model_id = get_model_id(target_id)
        name, pic_path = get_product_name_pic_path(target_id)
        return model_id, name, pic_path

    if record_type == constants.TYPE_MODEL:
        supplier_id = get_supplier_id(target_id)
        name, pic_path = get_model_name_and_picpath(target_id)
        return supplier_id, name, pic_path

    if record_type == constants.TYPE_SUPPLIER:
        bd_id = get_bd_id(target_id)
        name, pic_path = get_supplier_name_and_pic_path(target_id)
        return bd_id, name, pic_path
    if record_type == constants.TYPE_BD:
        name, pic_path = get_bd_name_and_pic_path(target_id)
        return date_field, name, pic_path
    return None, None, None


def create_snapshot_record(sale_stats):
    """
    :type sale_stats: SaleStats record_type is TYPE_TOTAL  instance
    为日期级别的记录 创建 快照记录
    """
    yesterday_date_field = sale_stats.date_field - datetime.timedelta(days=1)  # 昨天的时间
    snapshot_tag = 'snapshot-%s' % str(yesterday_date_field)  # 昨天的 snapshot 标记
    for s in constants.STATUS:
        status = s[0]
        uni_key = make_sale_stat_uni_key(yesterday_date_field,
                                         snapshot_tag,
                                         constants.TYPE_SNAPSHOT,
                                         constants.TYPE_AGG,
                                         status)
        # 查找昨天的快照是否存在
        yesterday_snapshot = SaleStats.objects.filter(uni_key=uni_key).first()
        if yesterday_snapshot:  # 已经做过快照 返回
            continue
        stats = SaleStats.objects.filter(date_field=yesterday_date_field,
                                         record_type=constants.TYPE_AGG,
                                         timely_type=constants.TIMELY_TYPE_DATE,
                                         status=status).first()
        if not stats:  # 昨天的记录(聚合类型 日期维度)没有找到 无法为 昨天的记录做 快照 返回
            continue
        yesterday_snapshot = SaleStats(
            current_id=snapshot_tag,
            date_field=yesterday_date_field,
            num=stats.num,
            payment=stats.payment,
            uni_key=uni_key,
            record_type=constants.TYPE_SNAPSHOT,
            timely_type=constants.TIMELY_TYPE_DATE,
            status=status
        )
        yesterday_snapshot.save()  # 保存快照信息


def gen_date_ftt_info(date, timely_type):
    """
    1. 根据 timely_type
    2. 根据日期 计算该日期对应的周数 和起止日期
    """
    time_from, time_to, tag = None, None, None
    if timely_type == constants.TIMELY_TYPE_WEEK:
        time_from = (date - datetime.timedelta(days=date.weekday()))
        time_to = time_from + datetime.timedelta(days=6)  # 该 周的 截止时间
        tag = 'week-%s' % date.strftime('%W')  # 周数
    if timely_type == constants.TIMELY_TYPE_MONTH:
        tag = 'month-%s' % date.strftime('%m')
        time_from = datetime.date(date.year, date.month, 1)
        month_days = calendar.monthrange(time_from.year, time_from.month)[1]  # 该 月份 天数
        time_to = datetime.date(date.year, date.month, month_days)

    if timely_type == constants.TIMELY_TYPE_QUARTER:
        current_month = date.month
        if current_month in [1, 2, 3]:
            quarter_num = 1
            time_from = datetime.date(date.year, 1, 1)  # 该日期的季度的第一天
            time_to = datetime.date(time_from.year, 3, 31)  # 截止日期
        elif current_month in [4, 5, 6]:
            quarter_num = 2
            time_from = datetime.date(date.year, 4, 1)  # 该日期的季度的第一天
            time_to = datetime.date(time_from.year, 6, 30)  # 截止日期
        elif current_month in [7, 8, 9]:
            quarter_num = 3
            time_from = datetime.date(date.year, 7, 1)  # 该日期的季度的第一天
            time_to = datetime.date(time_from.year, 9, 30)  # 截止日期
        else:
            quarter_num = 4
            time_from = datetime.date(date.year, 10, 1)  # 该日期的季度的第一天
            time_to = datetime.date(time_from.year, 12, 31)  # 截止日期
        tag = 'quarter-%s' % quarter_num  # 季度 tag
    if timely_type == constants.TIMELY_TYPE_YEAR:
        time_from = datetime.date(date.year, 1, 1)
        time_to = datetime.date(date.year, 12, 31)
        tag = date.strftime('%Y')
    return time_from, time_to, tag


def agg_num_payment_sale_stats(sale_stats):
    sum_dic = sale_stats.values('num', 'payment').aggregate(t_num=Sum('num'), t_payment=Sum('payment'))
    num = sum_dic.get('t_num') or 0
    payment = sum_dic.get('t_payment') or 0
    return num, payment


def find_upper_timely_type(timely_type):
    for upper_timely_type in constants.TIMELY_AGG_TYPE:
        if upper_timely_type[0] > timely_type:
            return upper_timely_type[0]
    return None


@task()
def task_update_parent_sale_stats(sale_stats):
    """
    更新 时间维度 的 统计记录
    """
    parent_id = sale_stats.parent_id
    if sale_stats.record_type >= constants.TYPE_AGG:  # 买手上级别不从本task 更新
        return
    if not parent_id:  # # 没有父级别id
        logger.error(u'task_update_parent_sale_stats: parent_id is None, current id  is %s' % sale_stats.current_id)
        return
    if sale_stats.timely_type != constants.TIMELY_TYPE_DATE:
        return
    stats = SaleStats.objects.filter(parent_id=parent_id,
                                     date_field=sale_stats.date_field,
                                     record_type=sale_stats.record_type,
                                     timely_type=constants.TIMELY_TYPE_DATE
                                     ).values('status').annotate(total_num=Sum('num'),
                                                                 total_payment=Sum('payment'))  # 同等级的数据计算

    data = gen_status_data_map(stats)

    date_field = sale_stats.date_field
    record_type = find_parent_record_type(sale_stats)
    if not record_type:
        return
    for status, v in data.iteritems():
        total_num = v['total_num']
        total_payment = v['total_payment']
        uni_key = make_sale_stat_uni_key(date_field, parent_id, record_type, constants.TIMELY_TYPE_DATE, status)

        old_stat = SaleStats.objects.filter(uni_key=uni_key).first()
        if not old_stat:
            if total_num > 0:
                grand_parent_id, name, pic_path = get_parent_id_name_and_pic_path(record_type, parent_id, date_field)
                # 供应商级别更新bd级别的 bd没有找到 则return
                if sale_stats.record_type == constants.TYPE_SUPPLIER and grand_parent_id is None:
                    logger.error(u'task_update_parent_sale_stats: '
                                 u' bd user not found , the supplier is %s' % sale_stats.current_id)
                    return
                # 更新款式级别的父级别 即 供应商级别 供应商为空的时候返回
                if sale_stats.record_type == constants.TYPE_MODEL and parent_id is None:
                    logger.error(u'task_update_parent_sale_stats: '
                                 u' model supplier not found, the model is %s' % sale_stats.current_id)
                    return
                st = SaleStats(
                    parent_id=grand_parent_id,
                    current_id=parent_id,
                    date_field=date_field,
                    name=name,
                    pic_path=pic_path,
                    uni_key=uni_key,
                    record_type=record_type,
                    timely_type=constants.TIMELY_TYPE_DATE,
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
    if sale_stats.record_type == constants.TYPE_BD:
        # 买手级别的统计更新才去触发 快照更新
        create_snapshot_record(sale_stats)


@task()
def task_update_agg_sale_stats(sale_stats, time_from, time_to, upper_timely_type, tag):
    """
    timely_type 类型为TIMELY_TYPE_DATE_DETAIL record_type <= TYPE_BD 的记录 更新到周 月 季度 年
    :type sale_stats: SaleStats date detail sale stats
    """
    record_type = sale_stats.record_type
    if sale_stats.record_type > constants.TYPE_AGG:  # 买手上级别不从本task 更新
        return
    if sale_stats.timely_type >= constants.TIMELY_TYPE_YEAR:
        return

    # 日期细分类型 record_type 等于 instance.record_type 的 分组聚合
    status = sale_stats.status
    current_id = sale_stats.current_id
    salestats = SaleStats.objects.filter(date_field__gte=time_from,
                                         date_field__lte=time_to,
                                         record_type=record_type,
                                         timely_type=constants.TIMELY_TYPE_DATE,
                                         status=status)
    if record_type == constants.TYPE_AGG:  # 如果是总计类型
        current_id = tag
        sum_dic = salestats.values('num', 'payment').aggregate(t_num=Sum('num'), t_payment=Sum('payment'))
    else:
        sum_dic = salestats.filter(current_id=current_id).values('num', 'payment').aggregate(t_num=Sum('num'),
                                                                                             t_payment=Sum('payment'))
    # 同等级的数据计算
    num = sum_dic.get('t_num') or 0
    payment = sum_dic.get('t_payment') or 0
    uni_key = make_sale_stat_uni_key(time_from, current_id,
                                     record_type, upper_timely_type, status)  # 生成时间上一个维度的uni_key
    old_stat = SaleStats.objects.filter(uni_key=uni_key).first()
    if not old_stat:
        if num == 0:
            return
        st = SaleStats(
            parent_id=sale_stats.parent_id,
            current_id=current_id,
            date_field=time_from,
            name=sale_stats.name,
            pic_path=sale_stats.pic_path,
            uni_key=uni_key,
            record_type=record_type,
            timely_type=upper_timely_type,
            status=status,
            num=num,
            payment=payment
        )
        st.save()
    else:
        update_fields = []
        if old_stat.num != num:
            old_stat.num = num
            update_fields.append('num')
        if old_stat.payment != payment:
            old_stat.payment = payment
            update_fields.append('payment')
        if update_fields:
            old_stat.save(update_fields=update_fields)


@task()
def task_update_product_sku_stats(product_sku_stats):
    """
    :param product_sku_stats: ProductSkuStats instance
    when the instance attr change save to stats .
    """
    if not (product_sku_stats.product and product_sku_stats.sku):
        logger.error(u'task_update_product_sku_stats %s product product or sku is None' % product_sku_stats.id)
        return
    sku = product_sku_stats.sku
    sku_outer_id = product_sku_stats.sku.outer_id
    product = product_sku_stats.product
    product_id = product.outer_id
    date_field = product_sku_stats.product.sale_time
    if not date_field:
        logger.error(u'task_update_product_sku_stats %s product sale time is None' % product_sku_stats.id)
        return
    quantity = product_sku_stats.realtime_quantity  # ProductSkuStats realtime_quantity
    inferior_num = product_sku_stats.inferior_num
    amount = product_sku_stats.sku.cost * quantity
    name = product.name + sku.properties_name
    uni_key = make_sale_stat_uni_key(date_field,
                                     sku_outer_id,
                                     constants.TYPE_SKU,
                                     constants.TIMELY_TYPE_DATE, '')

    psk_stat = ProductStockStat.objects.filter(uni_key=uni_key).first()
    if psk_stat:
        update_fields = []
        params = {
            "quantity": quantity,
            "inferior_num": inferior_num,
            "amount": amount
        }
        for k, v in params.iteritems():
            if hasattr(psk_stat, k) and getattr(psk_stat, k) != v:
                psk_stat.__setattr__(k, v)
                update_fields.append(k)
        if update_fields:
            psk_stat.save(update_fields=update_fields)
    else:
        psk_stat = ProductStockStat(
            parent_id=product_id,
            current_id=sku_outer_id,
            date_field=date_field,
            name=name,
            pic_path=product.pic_path,
            quantity=quantity,
            inferior_num=inferior_num,
            amount=amount,
            uni_key=uni_key,
            record_type=constants.TYPE_SKU,
            timely_type=constants.TIMELY_TYPE_DATE
        )
        psk_stat.save()


def create_stock_snapshot_record(stock_stats):
    """
    :type stock_stats: ProductStockStat record_type is TYPE_TOTAL  instance
    为日期级别的记录 创建 快照记录
    """
    yesterday_date_field = stock_stats.date_field - datetime.timedelta(days=1)  # 昨天的时间
    snapshot_tag = 'snapshot-%s' % str(yesterday_date_field)  # 昨天的 snapshot 标记
    uni_key = make_sale_stat_uni_key(yesterday_date_field,
                                     snapshot_tag,
                                     constants.TYPE_SNAPSHOT,
                                     constants.TYPE_AGG,
                                     '')
    # 查找昨天的快照是否存在
    yesterday_snapshot = ProductStockStat.objects.filter(uni_key=uni_key).first()
    if yesterday_snapshot:  # 已经做过快照 返回
        return
    stock_stats = ProductStockStat.objects.filter(date_field=yesterday_date_field,
                                                  record_type=constants.TYPE_AGG,
                                                  timely_type=constants.TIMELY_TYPE_DATE).first()
    if not stock_stats:  # 昨天的记录(聚合类型 日期维度)没有找到 无法为 昨天的记录做 快照 返回
        return
    yesterday_snapshot = ProductStockStat(
        inferior_num=stock_stats.inferior_num,
        current_id=snapshot_tag,
        date_field=yesterday_date_field,
        quantity=stock_stats.quantity,
        amount=stock_stats.amount,
        uni_key=uni_key,
        record_type=constants.TYPE_SNAPSHOT,
        timely_type=constants.TIMELY_TYPE_DATE
    )
    yesterday_snapshot.save()  # 保存快照信息


@task()
def task_update_parent_stock_stats(stock_stats):
    parent_id = stock_stats.parent_id
    if stock_stats.record_type >= constants.TYPE_AGG:  # 买手上级别不从本task 更新
        return
    if not parent_id:  # # 没有父级别id
        logger.error(u'task_update_parent_sale_stats: parent_id is None, current id  is %s' % stock_stats.current_id)
        return
    if stock_stats.timely_type != constants.TIMELY_TYPE_DATE:
        return

    same_stock_statss = ProductStockStat.objects.filter(parent_id=parent_id,
                                                        date_field=stock_stats.date_field,
                                                        record_type=stock_stats.record_type,
                                                        timely_type=constants.TIMELY_TYPE_DATE)  # 同等级的数据计算
    sum_dic = same_stock_statss.values(
        'quantity',
        'inferior_num',
        'amount'
    ).aggregate(
        t_quantity=Sum('quantity'),
        t_inferior_num=Sum('inferior_num'),
        t_amount=Sum('amount')
    )

    quantity = sum_dic.get('t_quantity') or 0
    inferior_num = sum_dic.get('t_inferior_num') or 0
    amount = sum_dic.get('t_amount') or 0
    record_type = find_parent_record_type(stock_stats)
    date_field = stock_stats.date_field

    uni_key = make_sale_stat_uni_key(date_field, parent_id, record_type, constants.TIMELY_TYPE_DATE, '')
    psk_stat = ProductStockStat.objects.filter(uni_key=uni_key).first()
    if psk_stat:
        params = {
            "quantity": quantity,
            "inferior_num": inferior_num,
            "amount": amount
        }
        update_fields = []
        for k, v in params.iteritems():
            if hasattr(psk_stat, k) and getattr(psk_stat, k) != v:
                psk_stat.__setattr__(k, v)
                update_fields.append(k)
        if update_fields:
            psk_stat.save(update_fields=update_fields)
    else:
        grand_parent_id, name, pic_path = get_parent_id_name_and_pic_path(record_type, parent_id, date_field)
        # 供应商级别更新bd级别的 bd没有找到 则return
        if stock_stats.record_type == constants.TYPE_SUPPLIER and grand_parent_id is None:
            return
        # 更新款式级别的父级别 即 供应商级别 供应商为空的时候返回
        if stock_stats.record_type == constants.TYPE_MODEL and parent_id is None:
            return
        psk_stat = ProductStockStat(
            parent_id=grand_parent_id,
            current_id=parent_id,
            date_field=date_field,
            name=name,
            pic_path=pic_path,
            quantity=quantity,
            inferior_num=inferior_num,
            amount=amount,
            uni_key=uni_key,
            record_type=record_type,
            timely_type=constants.TIMELY_TYPE_DATE
        )
        psk_stat.save()
    if stock_stats.record_type == constants.TYPE_BD:
        # 买手级别的统计更新才去触发 快照更新
        create_stock_snapshot_record(stock_stats)


@task()
def task_update_agg_stock_stats(stock_stats, time_from, time_to, upper_timely_type, tag):
    record_type = stock_stats.record_type
    if stock_stats.record_type > constants.TYPE_AGG:  # 总计上级别不从本task 更新
        return
    if stock_stats.timely_type >= constants.TIMELY_TYPE_YEAR:
        return
    # 日期细分类型 record_type 等于 instance.record_type 的 分组聚合
    current_id = stock_stats.current_id
    same_stock_statss = ProductStockStat.objects.filter(date_field__gte=time_from,
                                                        date_field__lte=time_to,
                                                        record_type=record_type,
                                                        timely_type=constants.TIMELY_TYPE_DATE)
    if record_type == constants.TYPE_AGG:  # 如果是总计类型
        current_id = tag
        sum_dic = same_stock_statss.values('quantity', 'inferior_num', 'amount').aggregate(
            t_quantity=Sum('quantity'),
            t_inferior_num=Sum('inferior_num'),
            t_amount=Sum('amount'))
    else:  # 指定对象的周　月　季度　年报
        sum_dic = same_stock_statss.filter(current_id=current_id).values('quantity',
                                                                         'inferior_num',
                                                                         'amount').aggregate(
            t_quantity=Sum('quantity'),
            t_inferior_num=Sum('inferior_num'),
            t_amount=Sum('amount'))

    quantity = sum_dic.get('t_quantity') or 0
    inferior_num = sum_dic.get('t_inferior_num') or 0
    amount = sum_dic.get('t_amount') or 0

    # 生成时间上一个维度的uni_key
    uni_key = make_sale_stat_uni_key(time_from, current_id, record_type, upper_timely_type, '')
    psk_stat = ProductStockStat.objects.filter(uni_key=uni_key).first()
    if psk_stat:
        params = {
            "quantity": quantity,
            "inferior_num": inferior_num,
            "amount": amount
        }
        update_fields = []
        for k, v in params.iteritems():
            if hasattr(psk_stat, k) and getattr(psk_stat, k) != v:
                psk_stat.__setattr__(k, v)
                update_fields.append(k)
        if update_fields:
            psk_stat.save(update_fields=update_fields)
    else:
        psk_stat = ProductStockStat(
            parent_id=stock_stats.parent_id,
            current_id=current_id,
            date_field=time_from,
            name=stock_stats.name,
            pic_path=stock_stats.pic_path,
            quantity=quantity,
            inferior_num=inferior_num,
            amount=amount,
            uni_key=uni_key,
            record_type=record_type,
            timely_type=upper_timely_type
        )
        psk_stat.save()

