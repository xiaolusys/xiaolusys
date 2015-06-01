# coding:utf-8
__author__ = 'yann'
import datetime
from django.forms.models import model_to_dict
from flashsale.dinghuo.models import orderdraft


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

