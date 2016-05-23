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
    charger = SupplierCharge.objects.filter(
        supplier_id=supplier_id,
        status=SupplierCharge.EFFECT
    ).order_by("-id").first()  # 有效状态的最新的接管人
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
    if not parent_id and sale_stats.record_type > SaleStats.TYPE_TOTAL:  # # 没有父级别id 并且 大于 日期 总计 级别的报错
        logger.error(u'task_update_parent_sale_stats: record_type not cover, current id  is %s' % sale_stats.current_id)
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
                # 供应商级别更新bd级别的 bd没有找到 则return
                if sale_stats.record_type == SaleStats.TYPE_SUPPLIER and grand_parent_id is None:
                    logger.error(u'task_update_parent_sale_stats: '
                                 u' bd user not found , the supplier is %s' % sale_stats.current_id)
                    return
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


@task()
def task_create_snapshot_record(sale_stats):
    """
    :type sale_stats: SaleStats record_type is TYPE_TOTAL  instance
    为日期级别的记录 创建 快照记录
    """
    if sale_stats.record_type != SaleStats.TYPE_TOTAL:
        return
    current_id = sale_stats.current_id  # 应该是日期类型 的字符串
    yesterday_date_field = sale_stats.date_field - datetime.timedelta(days=1)  # 昨天的时间
    if str(sale_stats.date_field) != current_id:
        logger.error(u'task_create_snapshot_record: sale stats id is %s' % sale_stats.id)
        return
    # 昨天的 snapshot 标记
    snapshot_tag = 'snapshot'
    for s in SaleStats.STATUS:
        status = s[0]
        uni_key = make_sale_stat_uni_key(yesterday_date_field,
                                         snapshot_tag,
                                         SaleStats.TYPE_SNAPSHOT,
                                         status)
        # 查找昨天的快照是否存在
        yesterday_snapshot = SaleStats.objects.filter(uni_key=uni_key).first()
        if yesterday_snapshot:  # 已经做过快照 返回
            continue
        stats = SaleStats.objects.filter(date_field=yesterday_date_field,
                                         record_type=SaleStats.TYPE_TOTAL,
                                         status=status).first()
        if not stats:  # 昨天的记录没有找到 无法为 昨天的记录做 快照 返回
            continue
        yesterday_snapshot = SaleStats(
            current_id=snapshot_tag,
            date_field=yesterday_date_field,
            num=stats.num,
            payment=stats.payment,
            uni_key=uni_key,
            record_type=SaleStats.TYPE_SNAPSHOT,
            status=status
        )
        yesterday_snapshot.save()  # 保存快照信息


@task()
def task_update_week_stats_record(date_stats):
    """
    :type date_stats: SaleStats instance witch record_type is TYPE_TOTAL
    日期 级别 数据 统计的 变化 更新 周报记录更新
    """
    if date_stats.record_type != SaleStats.TYPE_TOTAL:
        return
    # 查询周报记录是否存在
    # 有 则 判断是否有数字变化 有变化则更新  记录不存在 则创建记录 写入数据
    current_tag = 'week'
    date_field = date_stats.date_field
    time_left = (date_field - datetime.timedelta(days=date_field.weekday()))
    time_end = time_left + datetime.timedelta(days=7)  # 该 周的 截止时间
    date_field_uni = date_field.strftime('%Y%W')  # 年周

    for s in SaleStats.STATUS:
        status = s[0]
        uni_key = make_sale_stat_uni_key(date_field=date_field_uni, current_id=current_tag,
                                         record_type=SaleStats.TYPE_WEEK, status=status)
        # 计算该 周 的 每天 的 日期级别 统计  该状态 总和
        date_stats = SaleStats.objects.filter(record_type=SaleStats.TYPE_TOTAL,
                                              date_field__gte=time_left,
                                              date_field__lte=time_end,
                                              status=status)
        sum_dic = date_stats.values('num', 'payment').aggregate(t_num=Sum('num'), t_payment=Sum('payment'))
        num = sum_dic.get('t_num') or 0
        payment = sum_dic.get('t_payment') or 0
        if num == 0 and payment == 0:  # 都为0 则不更新
            continue
        stats = SaleStats.objects.filter(uni_key=uni_key).first()
        if stats:  # 有 周报记录
            update_fields = []
            if num != stats.num:
                stats.num = num
                update_fields.append('num')
            if payment != stats.payment:
                stats.payment = payment
                update_fields.append('payment')
            if update_fields:
                stats.save(update_fields=update_fields)
            continue
        else:
            stats = SaleStats(
                current_id=current_tag,
                date_field=time_left,
                num=num,
                payment=payment,
                uni_key=uni_key,
                record_type=SaleStats.TYPE_WEEK,
                status=status
            )
            stats.save()
            continue


def update_month_stats_record(year, month):
    """
    :type month: int month
    :type year: int year
    """
    current_tag = 'month'
    date_field_uni = str(year) + str(month)  # 年月
    time_left = datetime.date(year, month, 1)
    month_days = calendar.monthrange(time_left.year, time_left.month)[1]  # 该 月份 天数
    time_right = datetime.date(year, month, month_days)
    for s in SaleStats.STATUS:
        status = s[0]
        uni_key = make_sale_stat_uni_key(date_field=date_field_uni, current_id=current_tag,
                                         record_type=SaleStats.TYPE_MONTH, status=status)
        # 计算该 月 的 每天 的 统计 总和
        date_stats = SaleStats.objects.filter(record_type=SaleStats.TYPE_TOTAL,
                                              date_field__gte=time_left,
                                              date_field__lte=time_right,
                                              status=status)
        sum_dic = date_stats.values('num', 'payment').aggregate(t_num=Sum('num'), t_payment=Sum('payment'))
        num = sum_dic.get('t_num') or 0
        payment = sum_dic.get('t_payment') or 0
        if num == 0 and payment == 0:
            continue
        stats = SaleStats.objects.filter(uni_key=uni_key).first()
        if stats:  # 有 周报记录
            update_fields = []
            if num != stats.num:
                stats.num = num
                update_fields.append('num')
            if payment != stats.payment:
                stats.payment = payment
                update_fields.append('payment')
            if update_fields:
                stats.save(update_fields=update_fields)
            continue
        else:
            stats = SaleStats(
                current_id=current_tag,
                date_field=time_left,
                num=num,
                payment=payment,
                uni_key=uni_key,
                record_type=SaleStats.TYPE_MONTH,
                status=status
            )
            stats.save()
            continue


@task()
def task_update_month_stats_record(week_stats):
    """
    :type week_stats: SaleStats instance witch record_type is TYPE_WEEK
    """
    if week_stats.record_type != SaleStats.TYPE_WEEK:
        return

    # 查询月报记录是否存在
    # 有 则 判断是否有数字变化 有变化则更新  记录不存在 则创建记录 写入数据
    date_field = week_stats.date_field  # 该 周报记录的日期数值  注意这里并不是 第一天
    # 一个日期 判断是 一个月的最后一周
    sixed_date_field = date_field + datetime.timedelta(days=6)

    if sixed_date_field.year == date_field.year and sixed_date_field.month == date_field.month:  # 同年 同月 仅需要更新一次
        update_month_stats_record(date_field.year, date_field.month)
    if sixed_date_field.year == date_field.year and sixed_date_field.month > date_field.month:  # 夸月度 两个月度都更新
        update_month_stats_record(date_field.year, date_field.month)
        update_month_stats_record(date_field.year, sixed_date_field.month)
    if sixed_date_field.year > date_field.year:  # 夸年
        update_month_stats_record(date_field.year, sixed_date_field.month)
        update_month_stats_record(sixed_date_field.year, 1)  # 更新1月份的


@task()
def task_update_quarter_stats_record(month_stats):
    """
    :type month_stats: SaleStats instance witch record_type is TYPE_MONTH
    """
    if month_stats.record_type != SaleStats.TYPE_MONTH:
        return

    # 查询季度报告记录是否存在
    # 有 则 判断是否有数字变化 有变化则更新  记录不存在 则创建记录 写入数据
    current_tag = 'quarter'  # 季度 tag
    date_field = month_stats.date_field  # 该 阅读报告 记录的日期数值 该月的第一天
    current_month = date_field.month
    if current_month in [1, 2, 3]:
        quarter_num = 1
        time_left = datetime.date(date_field.year, 1, 1)  # 该日期的季度的第一天
        time_right = datetime.date(time_left.year, 3, 31)  # 截止日期
    elif current_month in [4, 5, 6]:
        quarter_num = 2
        time_left = datetime.date(date_field.year, 4, 1)  # 该日期的季度的第一天
        time_right = datetime.date(time_left.year, 6, 30)  # 截止日期
    elif current_month in [7, 8, 9]:
        quarter_num = 3
        time_left = datetime.date(date_field.year, 7, 1)  # 该日期的季度的第一天
        time_right = datetime.date(time_left.year, 9, 30)  # 截止日期
    elif current_month in [10, 11, 12]:
        quarter_num = 4
        time_left = datetime.date(date_field.year, 10, 1)  # 该日期的季度的第一天
        time_right = datetime.date(time_left.year, 12, 31)  # 截止日期
    else:
        logger.error(u'task_update_quarter_stats_record: month out of range')
        return
    date_field_uni = month_stats.date_field.strftime('%Y') + str(quarter_num)  # 年季度
    for s in SaleStats.STATUS:
        status = s[0]
        uni_key = make_sale_stat_uni_key(date_field=date_field_uni, current_id=current_tag,
                                         record_type=SaleStats.TYPE_QUARTER, status=status)
        # 计算该 月 的 每天 的 统计 总和
        date_stats = SaleStats.objects.filter(record_type=SaleStats.TYPE_TOTAL,
                                              date_field__gte=time_left,
                                              date_field__lte=time_right,
                                              status=status)
        sum_dic = date_stats.values('num', 'payment').aggregate(t_num=Sum('num'), t_payment=Sum('payment'))
        num = sum_dic.get('t_num') or 0
        payment = sum_dic.get('t_payment') or 0
        if num == 0 and payment == 0:
            continue

        stats = SaleStats.objects.filter(uni_key=uni_key).first()
        if stats:  # 有 周报记录
            update_fields = []
            if num != stats.num:
                stats.num = num
                update_fields.append('num')
            if payment != stats.payment:
                stats.payment = payment
                update_fields.append('payment')
            if update_fields:
                stats.save(update_fields=update_fields)
            continue
        else:
            stats = SaleStats(
                current_id=current_tag,
                date_field=time_left,
                num=num,
                payment=payment,
                uni_key=uni_key,
                record_type=SaleStats.TYPE_QUARTER,
                status=status
            )
            stats.save()
            continue
