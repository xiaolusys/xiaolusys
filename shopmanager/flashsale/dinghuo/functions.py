# coding:utf-8
__author__ = 'yann'
import datetime
from django.forms.models import model_to_dict
from flashsale.dinghuo.models import orderdraft, OrderDetail


def parse_date(dt):
    return datetime.datetime.strptime(dt, '%Y-%m-%d')


def parse_datetime(dt):
    return datetime.datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')


def get_product_dict_from_product(product_result):
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
    flag_of_state = False
    sample_num = 0
    if memo.__contains__("样品补全:"):
        sample_num = memo.split(":")[1]
        if len(sample_num) > 0:
            sample_num = int(sample_num[0])
            flag_of_state = True
    return flag_of_state, sample_num


def get_ding_huo_status(num, ding_huo_num, sku_dict):
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
    all_details = OrderDetail.objects.filter(orderlist_id=order_list_id)
    for order_detail in all_details:
        buy_quantity = order_detail.inferior_quantity + order_detail.non_arrival_quantity
        draft_query = orderdraft.objects.filter(buyer_name=user, product_id=order_detail.product_id,
                                                chichu_id=order_detail.chichu_id)
        if draft_query.count() == 0:
            current_time = datetime.datetime.now()
            t_draft = orderdraft(buyer_name=user, product_id=order_detail.product_id, outer_id=order_detail.outer_id,
                                 buy_quantity=buy_quantity, product_name=order_detail.product_name,
                                 buy_unitprice=order_detail.buy_unitprice,
                                 chichu_id=order_detail.chichu_id, product_chicun=order_detail.product_chicun,
                                 created=current_time)
            t_draft.save()