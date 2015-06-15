# coding:utf-8
__author__ = 'yann'
import datetime
from django.forms.models import model_to_dict
from shopback.trades.models import MergeOrder
from flashsale.dinghuo import paramconfig as pcfg
from django.db.models import Q
from shopback.items.models import Product
from flashsale.dinghuo.models import orderdraft, OrderDetail
from flashsale.dinghuo.models_user import MyUser, MyGroup


def parse_date(dt):
    return datetime.datetime.strptime(dt, '%Y-%m-%d')


def parse_datetime(dt):
    return datetime.datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')


def get_product_dict_from_product(product_result):
    """ 从商品queryset中得到关于这个商品的所有信息加上尺寸的所有信息，并且返回dict"""
    product_list = []
    for product in product_result:
        product_dict = model_to_dict(product)
        product_dict['prod_skus'] = []

        all_sku = product.prod_skus.all()
        for gui_ge in all_sku:
            sku_dict = model_to_dict(gui_ge)
            sku_dict['sku_name'] = sku_dict['properties_alias'] if len(
                sku_dict['properties_alias']) > 0 else sku_dict['properties_name']
            product_dict['prod_skus'].append(sku_dict)

        product_list.append(product_dict)
    return product_list


def cal_amount(u, express_cost):
    amount = 0
    drafts = orderdraft.objects.all().filter(buyer_name=u)
    for draft in drafts:
        amount += draft.buy_unitprice * draft.buy_quantity
    amount = amount + express_cost
    return amount


def get_num_by_memo(memo):
    """根据备注来获取样品的数量"""
    flag_of_state = False
    sample_num = 0
    if memo.__contains__("样品补全:"):
        sample_num = memo.split(":")[1]
        if len(sample_num) > 0:
            sample_num = int(sample_num[0])
            flag_of_state = True
    return flag_of_state, sample_num


def get_ding_huo_status(num, ding_huo_num, sku_dict):
    """根据销售数量，订货数量，样品数量得到订货的状态"""
    flag_of_more = False
    flag_of_less = False
    result_str = ""
    flag_of_memo, sample_num = get_num_by_memo(sku_dict['memo'])
    if ding_huo_num + sample_num > num:
        flag_of_more = True
        result_str = '多订' + str(ding_huo_num + sample_num - num) + '件'
    if ding_huo_num + sample_num < num:
        flag_of_less = True
        result_str = '缺少' + str(num - ding_huo_num - sample_num) + '件'

    return result_str, flag_of_memo, flag_of_more, flag_of_less


def save_draft_from_detail_id(order_list_id, user):
    """根据这个订货单的id获取未完成的订货信息"""
    all_details = OrderDetail.objects.filter(orderlist_id=order_list_id)
    for order_detail in all_details:
        buy_quantity = order_detail.inferior_quantity + order_detail.non_arrival_quantity
        draft_query = orderdraft.objects.filter(buyer_name=user, product_id=order_detail.product_id,
                                                chichu_id=order_detail.chichu_id)
        if draft_query.count() == 0 and buy_quantity > 0:
            current_time = datetime.datetime.now()
            t_draft = orderdraft(buyer_name=user, product_id=order_detail.product_id, outer_id=order_detail.outer_id,
                                 buy_quantity=buy_quantity, product_name=order_detail.product_name,
                                 buy_unitprice=order_detail.buy_unitprice,
                                 chichu_id=order_detail.chichu_id, product_chicun=order_detail.product_chicun,
                                 created=current_time)
            t_draft.save()


def get_source_orders(start_dt=None, end_dt=None):
    """获取某个时间段里面的原始订单的信息"""
    order_qs = MergeOrder.objects.filter(sys_status=pcfg.IN_EFFECT) \
        .exclude(merge_trade__type=pcfg.REISSUE_TYPE) \
        .exclude(merge_trade__type=pcfg.EXCHANGE_TYPE) \
        .exclude(gift_type=pcfg.RETURN_GOODS_GIT_TYPE)
    order_qs = order_qs.filter(pay_time__gte=start_dt, pay_time__lte=end_dt)
    order_qs = order_qs.filter(merge_trade__status__in=pcfg.ORDER_SUCCESS_STATUS) \
        .exclude(merge_trade__sys_status__in=(pcfg.INVALID_STATUS, pcfg.ON_THE_FLY_STATUS)) \
        .exclude(merge_trade__sys_status=pcfg.FINISHED_STATUS, merge_trade__is_express_print=False)

    order_qs = order_qs.values("outer_id", "num", "outer_sku_id", "pay_time").extra(where=["CHAR_LENGTH(outer_id)>=9"]) \
        .filter(Q(outer_id__startswith="9") | Q(outer_id__startswith="1") | Q(outer_id__startswith="8"))
    return order_qs


def get_source_orders_consign(start_dt=None, end_dt=None):
    """获取发货时间段里面的原始订单的信息"""
    order_qs = MergeOrder.objects.filter(sys_status=pcfg.IN_EFFECT) \
        .exclude(merge_trade__type=pcfg.REISSUE_TYPE) \
        .exclude(merge_trade__type=pcfg.EXCHANGE_TYPE) \
        .exclude(gift_type=pcfg.RETURN_GOODS_GIT_TYPE)
    order_qs = order_qs.filter(merge_trade__weight_time__gte=start_dt, merge_trade__weight_time__lte=end_dt)
    order_qs = order_qs.filter(merge_trade__status__in=pcfg.ORDER_SUCCESS_STATUS) \
        .exclude(merge_trade__sys_status__in=(pcfg.INVALID_STATUS, pcfg.ON_THE_FLY_STATUS)) \
        .exclude(merge_trade__sys_status=pcfg.FINISHED_STATUS, merge_trade__is_express_print=False)

    order_qs = order_qs.values("outer_id", "num", "outer_sku_id", "merge_trade__weight_time").extra(where=["CHAR_LENGTH(outer_id)>=9"]) \
        .filter(Q(outer_id__startswith="9") | Q(outer_id__startswith="1") | Q(outer_id__startswith="8"))
    return order_qs

def get_product_by_date(shelve_date, group_name="0"):
    """根据上架时间和组名获取对应的商品信息"""
    group_members = []
    if group_name == '0':
        product_qs = Product.objects.values('id', 'name', 'outer_id', 'pic_path').filter(
            sale_time=shelve_date).exclude(status="delete")
    else:
        all_user = MyUser.objects.filter(group__name=group_name)
        for user in all_user:
            group_members.append(user.user.username)
        product_qs = Product.objects.values('id', 'name', 'outer_id', 'pic_path').filter(sale_time=shelve_date,
                                                                                         sale_charger__in=group_members).exclude(status="delete")
    return product_qs


def get_product_from_order(order_qs):
    """从订单里面得到所有的商品、尺寸销售数"""
    result_str = {}
    for order in order_qs:
        if order["outer_id"] in result_str:
            if order["outer_sku_id"] in result_str[order["outer_id"]]:
                result_str[order["outer_id"]][order["outer_sku_id"]]["num"] += order["num"]
            else:
                result_str[order["outer_id"]][order["outer_sku_id"]] = {"num": order["num"]}
        else:
            result_str[order["outer_id"]] = {order["outer_sku_id"]: {"num": order["num"]}}
    return result_str


def get_sale_num_by_sku(pro_outer_id, sku_outer_id, order_dict):
    """通过商品外部编码和sku外部编码、销售集合得到销售数量"""
    # sale_num1 = orderqs.filter(outer_sku_id=sku_outer_id).aggregate(total_sale_num=Sum('num')).get(
    # 'total_sale_num') or 0
    sale_num = 0
    if pro_outer_id in order_dict and sku_outer_id in order_dict[pro_outer_id]:
        sale_num = order_dict[pro_outer_id][sku_outer_id]['num']
    return sale_num