# coding:utf-8
__author__ = 'yann'
import datetime
from django.forms.models import model_to_dict
from shopback.trades.models import MergeOrder
from flashsale.dinghuo import paramconfig as pcfg
from django.db.models import Q
from shopback.items.models import Product
from flashsale.dinghuo.models import OrderDraft, OrderDetail
from flashsale.dinghuo.models_user import MyUser, MyGroup
import simplejson
import urllib2
from django.db import connection


def parse_date(dt):
    return datetime.datetime.strptime(dt, '%Y-%m-%d')


def parse_datetime(dt):
    return datetime.datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')


def get_product_dict_from_product(product_result):
    """ 从商品queryset中得到关于这个商品的所有信息加上尺寸的所有信息，并且返回dict"""
    product_list = []
    for product in product_result:
        try:
            detail2pro = product.details
        except:
            detail2pro = False

        product_dict = model_to_dict(product)
        if detail2pro:
            detail_d = model_to_dict(detail2pro)
        else:
            detail_d = {"head_imgs": "", "content_imgs": ""}
        product_dict['details'] = detail_d
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
    drafts = OrderDraft.objects.all().filter(buyer_name=u)
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


def get_ding_huo_status(num, ding_huo_num, ku_cun_num=0, sample_num=0, arrival_num=0):
    """根据销售数量，订货数量，库存数量得到订货的状态"""
    flag_of_more = False
    flag_of_less = False
    result_str = ""
    if ding_huo_num + ku_cun_num + sample_num + arrival_num > num:
        flag_of_more = True
        result_str = '多' + str(ding_huo_num + ku_cun_num + sample_num + arrival_num - num) + '件'
    if ding_huo_num + ku_cun_num + sample_num + arrival_num < num:
        flag_of_less = True
        result_str = '缺少' + str(num - ding_huo_num - ku_cun_num - sample_num - arrival_num) + '件'

    return result_str, flag_of_more, flag_of_less


def save_draft_from_detail_id(order_list_id, user):
    """根据这个订货单的id获取未完成的订货信息"""
    all_details = OrderDetail.objects.filter(orderlist_id=order_list_id)
    for order_detail in all_details:
        buy_quantity = order_detail.non_arrival_quantity
        draft_query = OrderDraft.objects.filter(buyer_name=user, product_id=order_detail.product_id,
                                                chichu_id=order_detail.chichu_id)
        if draft_query.count() == 0 and buy_quantity > 0:
            current_time = datetime.datetime.now()
            t_draft = OrderDraft(buyer_name=user, product_id=order_detail.product_id, outer_id=order_detail.outer_id,
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

    order_qs = order_qs.values("outer_id", "num", "outer_sku_id", "merge_trade__weight_time").extra(
        where=["CHAR_LENGTH(outer_id)>=9"]) \
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
                                                                                         sale_charger__in=group_members).exclude(
            status="delete")
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


def send_txt_msg(token, content, to_user="@all", to_party="", to_tag="", application_id=0, safe=0):
    try:
        data = {
            "touser": to_user,
            "toparty": to_party,
            "totag": to_tag,
            "msgtype": "text",
            "agentid": application_id,
            "text": {"content": content},
            "safe": safe
        }

        data = simplejson.dumps(data, ensure_ascii=False)
        print data, type(data)
        req = urllib2.Request('https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=%s' % (token,))
        resp = urllib2.urlopen(req, data)
        msg = u'返回值:' + resp.read()
    except Exception, ex:
        msg = u'异常:' + str(ex)
    finally:
        print msg


def get_token_in_time(corp_id, secret):
    res = urllib2.urlopen('https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=%s&corpsecret=%s' % (corp_id, secret))
    res_dict = simplejson.loads(res.read())
    token = res_dict.get('access_token', False)

    return token


def get_result_daily():
    today = datetime.date.today()
    dhstatus = '1'
    target_date = today - datetime.timedelta(days=1)
    shelve_from = datetime.datetime(target_date.year, target_date.month, target_date.day)
    query_time = datetime.datetime.now()
    time_to = datetime.datetime.now()
    groups = (1, 2, 3)
    group_name = ("A:", "B:", "C:")
    result_str = ""
    for groupname in groups:
        order_sql = "select id,outer_id,sum(num) as sale_num,outer_sku_id,pay_time from " \
                    "shop_trades_mergeorder where sys_status='IN_EFFECT' " \
                    "and merge_trade_id in (select id from shop_trades_mergetrade where type not in ('reissue','exchange') " \
                    "and status in ('WAIT_SELLER_SEND_GOODS','WAIT_BUYER_CONFIRM_GOODS','TRADE_BUYER_SIGNED','TRADE_FINISHED') " \
                    "and sys_status not in('INVALID','ON_THE_FLY') " \
                    "and id not in (select id from shop_trades_mergetrade where sys_status='FINISHED' and is_express_print=False))" \
                    "and gift_type !=4 " \
                    "and (pay_time BETWEEN '{0}' and '{1}') " \
                    "and CHAR_LENGTH(outer_id)>=9 " \
                    "and (left(outer_id,1)='9' or left(outer_id,1)='8' or left(outer_id,1)='1') " \
                    "group by outer_id,outer_sku_id".format(shelve_from, time_to)
        if groupname == 0:
            group_sql = ""
        else:
            group_sql = " where group_id = " + str(groupname)

        product_sql = "select A.id,A.product_name,A.outer_id,A.pic_path,B.outer_id as outer_sku_id,B.quantity,B.properties_alias,B.id as sku_id,C.exist_stock_num from " \
                      "(select id,name as product_name,outer_id,pic_path from " \
                      "shop_items_product where  sale_time='{0}' " \
                      "and status!='delete' " \
                      "and sale_charger in (select username from auth_user where id in (select user_id from suplychain_flashsale_myuser {1}))) as A " \
                      "left join (select id,product_id,outer_id,properties_alias,quantity from shop_items_productsku) as B " \
                      "on A.id=B.product_id left join flash_sale_product_sku_detail as C on B.id=C.product_sku".format(
            target_date, group_sql)
        ding_huo_sql = "select B.outer_id,B.chichu_id,sum(if(A.status='草稿' OR A.status='审核',B.buy_quantity,0)) as buy_quantity,sum(if(A.status='7',B.buy_quantity,0)) as sample_quantity," \
                       "sum(if(status='5' OR  status='6' OR status='有问题' OR status='验货完成' OR status='已处理',B.arrival_quantity,0)) as arrival_quantity,B.effect_quantity,A.status" \
                       " from (select id,status from suplychain_flashsale_orderlist where status not in ('作废') and created BETWEEN '{0}' AND '{1}') as A " \
                       "left join (select orderlist_id,outer_id,chichu_id,buy_quantity,arrival_quantity,(buy_quantity-non_arrival_quantity) as effect_quantity " \
                       "from suplychain_flashsale_orderdetail) as B on A.id=B.orderlist_id group by outer_id,chichu_id".format(
            shelve_from, query_time)
        sql = "select product.outer_id,product.product_name,product.outer_sku_id,product.pic_path,product.properties_alias," \
              "order_info.sale_num,ding_huo_info.buy_quantity,ding_huo_info.effect_quantity,product.sku_id,product.exist_stock_num," \
              "product.id,ding_huo_info.arrival_quantity,ding_huo_info.sample_quantity " \
              "from (" + product_sql + ") as product left join (" + order_sql + ") as order_info on product.outer_id=order_info.outer_id and product.outer_sku_id=order_info.outer_sku_id left join (" + ding_huo_sql + ") as ding_huo_info on product.outer_id=ding_huo_info.outer_id and product.sku_id=ding_huo_info.chichu_id"
        cursor = connection.cursor()
        cursor.execute(sql)
        raw = cursor.fetchall()
        trade_dict = {}
        total_more_num = 0
        total_less_num = 0
        for product in raw:
            sale_num = int(product[5] or 0)
            ding_huo_num = int(product[6] or 0)
            arrival_num = int(product[11] or 0)
            sample_num = int(product[12] or 0)
            ding_huo_status, flag_of_more, flag_of_less = get_ding_huo_status(
                sale_num, ding_huo_num, int(product[9] or 0), sample_num, arrival_num)
            if flag_of_more:
                total_more_num += (sample_num + int(product[9] or 0) + ding_huo_num + arrival_num - sale_num)
            if flag_of_less:
                total_less_num += (sale_num - sample_num - int(product[9] or 0) - arrival_num - ding_huo_num)
            temp_dict = {"product_id": product[10], "sku_id": product[2], "product_name": product[1],
                         "pic_path": product[3], "sale_num": sale_num or 0, "sku_name": product[4],
                         "ding_huo_num": ding_huo_num, "effect_num": product[7] or 0,
                         "ding_huo_status": ding_huo_status, "sample_num": sample_num,
                         "flag_of_more": flag_of_more, "flag_of_less": flag_of_less,
                         "sku_id": product[8], "ku_cun_num": int(product[9] or 0),
                         "arrival_num": arrival_num}
            if dhstatus == u'0' or ((flag_of_more or flag_of_less) and dhstatus == u'1') or (
                        flag_of_less and dhstatus == u'2') or (flag_of_more and dhstatus == u'3'):
                if product[0] not in trade_dict:
                    trade_dict[product[0]] = [temp_dict]
                else:
                    trade_dict[product[0]].append(temp_dict)
        result_str += str(group_name[groupname - 1]) + "缺:" + str(total_less_num) + " 多" + str(total_more_num) + "\n"
    return result_str
