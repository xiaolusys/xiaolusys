# coding: utf-8
"""
统计一段时期内特卖商品的退货数量，及库存数量，并可创建退货单，退回给供应商
库存：shopback items models Product collect_num: 库存数
退货：flashsale dinghuo models_stats SupplyChainStatsOrder refund_num :退货数量 ,该产品的昨天的退货数量
"""
from cStringIO import StringIO
import decimal
import io
import urllib
import xlsxwriter

from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework import permissions
import logging
import json
import datetime
import common.utils
from core.options import log_action, ADDITION, CHANGE
from ..tasks import calcu_refund_info_by_pro_v2
from shopback.logistics.models import LogisticsCompany
from flashsale.dinghuo.models import InBound,OrderList,OrderDetail
from rest_framework import  authentication

logger = logging.getLogger('django.request')

from common.decorators import jsonapi
from flashsale.dinghuo.models import RGDetail, ReturnGoods, UnReturnSku
from flashsale.finance.models import BillRelation, Bill
from rest_framework import generics, permissions, renderers, viewsets
from supplychain.supplier.models import SaleProduct, SaleSupplier
from rest_framework.decorators import list_route, detail_route
from shopback.warehouse import WARE_NONE, WARE_GZ, WARE_SH, WARE_CHOICES
from shopback.trades.models import PackageSkuItem,PackageOrder
from shopback.items.models import SkuStock,Product,ProductSku
from .. import forms


def get_sale_product(sale_product):
    """　找到库存商品对应的选品信息　"""
    try:
        sal_p = SaleProduct.objects.get(id=sale_product)
        return sal_p.sale_supplier.supplier_name, sal_p.sale_supplier.pk, \
               sal_p.sale_supplier.contact, sal_p.sale_supplier.mobile
    except SaleProduct.DoesNotExist:
        return "", 0, "", ""


def modify_sku_quantity(sku_id=None):
    pass


class StatisRefundSupView(APIView):
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer)
    template_name = "tuihuo/tuihuo_statistic_page.html"
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, format=None):
        content = request.GET
        date_from = (
            content.get('date_from',
                        datetime.datetime.today() - datetime.timedelta(days=7)))
        date_to = (content.get('date_to', datetime.datetime.today()))
        task_id = calcu_refund_info_by_pro_v2.delay(date_from, date_to)
        return Response({"task_id": task_id,
                         "date_from": date_from,
                         "date_to": date_to})

    def post(self, request, format=None):
        content = request.POST
        arr = content.get("arr", None)
        data = eval(arr)  # json字符串转化
        supplier_set = set()
        pro_id_set = set()
        for i in data:
            supplier_set.add(i['supplier'])
        if supplier_set.__len__() != 1:
            return Response({"res": "multi_supplier"})
        supplier = supplier_set.pop()  # 唯一供应商

        for i in data:
            pro_id_set.add(i['pro_id'])

        for pro_id in pro_id_set:
            return_num = 0
            sum_amount = 0.0
            rg = ReturnGoods()
            rg.product_id = pro_id
            rg.supplier_id = supplier
            rg.save()
            for da in data:
                if da['pro_id'] == pro_id:  # 是当前的商品
                    sku_return_num = int(da['return_num'])
                    price = float(da['price'])
                    sku_id = int(da['sku_id'])
                    inferior_num = int(da['sku_inferior_num'])
                    return_num = return_num + sku_return_num  # 累计产品的退货数量
                    sum_amount = sum_amount + price * sku_return_num
                    rg_d = RGDetail.objects.create(skuid=sku_id,
                                                   return_goods_id=rg.id,
                                                   num=sku_return_num,
                                                   inferior_num=inferior_num,
                                                   price=price)
                    log_action(request.user.id, rg_d, ADDITION, u'创建退货单')
            rg.return_num = return_num
            rg.sum_amount = sum_amount
            rg.noter = request.user.username
            rg.save()
            log_action(request.user.id, rg, ADDITION, u'创建退货单')
        return Response({"res": True})


from django.http import HttpResponse

from shopback.items.models import Product, ProductSku
from django.db.models import F
from common.modelutils import update_model_fields


def change_duihuo_status(request):
    content = request.POST
    act_str = content.get("act_str", None)
    id = content.get("id", None)
    if not (act_str and id):
        return HttpResponse(False)
    id = int(id)
    user_id = request.user.id
    rg = ReturnGoods.objects.get(id=id)
    change_status_des = u"仓库退货单状态变更为_{0}"
    if act_str == "ok":  # 审核通过
        rg.status = ReturnGoods.VERIFY_RG
        rg.save()
        change_product_inventory(rg, request.user.username, request.user.id)
        log_action(user_id, rg, CHANGE,
                   change_status_des.format(rg.get_status_display()))
        # 减少库存
    elif act_str == "no":  # 作废
        rg.status = ReturnGoods.OBSOLETE_RG
        rg.save()
        log_action(user_id, rg, CHANGE,
                   change_status_des.format(rg.get_status_display()))
    elif act_str == "send":  # 已经发货
        rg.status = ReturnGoods.DELIVER_RG
        rg.save()
        log_action(user_id, rg, CHANGE,
                   change_status_des.format(rg.get_status_display()))
    elif act_str == "send_ok":  # 已经发货
        rg.status = ReturnGoods.SUCCEED_RG
        rg.save()
        log_action(user_id, rg, CHANGE,
                   change_status_des.format(rg.get_status_display()))
    return HttpResponse(True)
    # elif act_str == "send_fail":  # 已经发货
    #     return
    # rg.status = ReturnGoods.FAILED_RG
    # rd = rg.rg_details.all()
    # try:
    #     for item in rd:
    #         skuid = item.skuid
    #         num = item.num
    #         inferior_num = item.inferior_num
    #         ProductSku.objects.filter(id=skuid).update(quantity = F('quantity')+num, sku_inferior_num=F('sku_inferior_num')+inferior_num)
    #         rg.save()
    #     # log_action(user_id, rg, CHANGE,
    #     #            change_status_des.format(rg.get_status_display()))
    #     return HttpResponse(True)
    # except Exception,msg:
    #     return HttpResponse(False)


def change_return_goods_memo(request):
    content = request.POST
    id = content.get("id", None)
    memo = content.get("memo", '')
    return_goods = get_object_or_404(ReturnGoods, id=id)
    return_goods.memo = memo
    return_goods.save()
    return HttpResponse(True)


def modify_return_goods_sku(request):
    content = request.POST
    id = int(content.get("id", None))
    sku_id = content.get("sku_id", None)
    num = int(content.get("num", 0))
    price = float(content.get("price", 0))
    return_goods = get_object_or_404(ReturnGoods, id=id)
    rg_detail = return_goods.rg_details.get(skuid=sku_id)
    rg_detail.num = num
    rg_detail.price = price
    rg_detail.save()
    return HttpResponse(True)

def create_pksi_by_rgdetail(request):
    content = request.POST
    returngoods_id = content.get("returngoods_id",None)
    return_good = ReturnGoods.objects.get(id=returngoods_id)
    supplier_addr = return_good.get_supplier_addr()
    if not supplier_addr:
        return HttpResponse(json.dumps({"status": False, "reason": "供应商信息不存在,请填写供应商地址信息"}), content_type="application/json",
                            status=200)
    elif not supplier_addr.is_complete():
        return HttpResponse(json.dumps({"status": False, "reason": "供应商信息不完整,请完善供应商地址信息"}), content_type="application/json",
                            status=200)
    rgdetail_ids = content.get("RGdetail_ids")
    type = content.get("type")
    rgdetail_ids = json.loads(rgdetail_ids)
    RGdetail = RGDetail.objects.filter(id__in=rgdetail_ids)
    pksi_id = []
    print content.get("RGdetail_ids")
    print content.get("supplier_id")
    for i in RGdetail:
        sku_id = i.skuid
        sale_order_id = i.id
        sale_trade_id = i.return_goods.id
        type = type
        num = i.num
        title = SkuStock.objects.get(sku_id=i.skuid).product.name
        pic_path = SkuStock.objects.get(sku_id=i.skuid).product.pic_path
        sku_properties_name = i.product_sku.properties_name
        rg_detail_info = {"sku_id":sku_id,"sale_order_id":sale_order_id,"sale_trade_id":sale_trade_id,"type":type,"pay_time":return_good.created,"num":num,
                          "title":title,"pic_path":pic_path,"sku_properties_name":sku_properties_name}
        print rg_detail_info
        if PackageSkuItem.objects.filter(sale_order_id = i.id):
            pksi = PackageSkuItem.objects.filter(sale_order_id=i.id).first()
            if type!=2:
                pksi_id.append(pksi.id)
                continue
            PackageSkuItem.objects.filter(sale_order_id = i.id).update(**rg_detail_info)
            pksi_id.append(pksi.id)
            if pksi.package_order_pid:
                PackageOrder.objects.filter(pid=pksi.package_order_pid).update(redo_sign=True,is_picking_print=False)

        else:
            pksi = PackageSkuItem.objects.create(**rg_detail_info)
            pksi.return_merge()
            pksi_id.append(pksi.id)
    return HttpResponse(json.dumps({"status":True,"pksi_id":pksi_id}),content_type="application/json", status=200)



def replace_become_refund(request):
    content = request.POST
    id = content.get("returngoods_id",None)
    RGdetail_ids = content.get("RGdetail_ids",None)
    RGdetail_ids = json.loads(RGdetail_ids)
    new_returngoods_id = get_new_ctr(id,RGdetail_ids)
    return HttpResponse(json.dumps({"new_returngoods_id":new_returngoods_id}))

def get_new_ctr(returngoods_id,RGdetail_ids):
    supplier = ReturnGoods.objects.get(id=returngoods_id).supplier
    bei = " 换货变退货回款，需要这个新的退货单作为财务收款凭证，仓库如果没货，就不要发，此单作为收款凭据，不要作废"
    return_goods = ReturnGoods.objects.create(supplier=supplier, type=ReturnGoods.TYPE_COMMON,
                                              memo="由退货单中" + returngoods_id + "中的数据生成的新退货单,"+bei)  #先生成新的退货单 by供应商

    # orderlist_id = InBound.objects.filter(return_goods_id=returngoods_id).first().ori_orderlist_id          #根据老的退货单,找到入仓单,找到订货单,找到里面所有的货的id和价格
    # order_detail_all = OrderList.objects.filter(id=orderlist_id).first().order_list.all()
    # order_detail_all = {i.chichu_id:i.buy_unitprice for i in order_detail_all}
    sum_num = 0
    sum_money = 0
    str_rgdetail_ids = ''
    for i in RGdetail_ids:                                                     #对于每一个我们期望变成退款的货,我们找到并修改价格,退货类型,以及它的退货单外键
        str_rgdetail_ids = str_rgdetail_ids + str(i)+' '
        rg_detail = RGDetail.objects.filter(skuid=i,return_goods_id=returngoods_id).first()
        order_detail = OrderDetail.objects.filter(chichu_id=i).order_by("-created")
        if not order_detail:
            buy_unitprice = 0                          #订货单中没有,说明是多货,那么回款为0
        else:
            buy_unitprice = order_detail.first().buy_unitprice
        rg_detail.price = buy_unitprice
        rg_detail.type = RGDetail.TYPE_REFUND
        rg_detail.return_goods = return_goods
        sum_num = sum_num + rg_detail.num + rg_detail.inferior_num
        sum_money = sum_money + rg_detail.price * (rg_detail.num + rg_detail.inferior_num)
        rg_detail.save()

    return_goods.return_num = sum_num                            #就算新产生退货单的退货数和计划退货金额
    return_goods.plan_amount = sum_money
    return_goods.sum_amount = sum_money
    return_goods.save()

    o_bei = "    由于无货可换,供应商只能退款给我司,所以"+"此单中的sku:"+str_rgdetail_ids+"已移除到新的退货单:"+return_goods.id+"中"
    origin_memo = ReturnGoods.objects.get(id=returngoods_id).memo
    ReturnGoods.objects.filter(id=returngoods_id).update(return_num=F("return_num")-sum_num,memo = origin_memo+o_bei) #修改原先退货单的退货数量

    return return_goods.id

def delete_return_goods_sku(request):
    content = request.POST
    id = int(content.get("id", None))
    sku_id = content.get("sku_id", None)
    return_goods = get_object_or_404(ReturnGoods, id=id)
    rg_details = return_goods.rg_details.filter(skuid=sku_id)
    for rg_detail in rg_details:
        rg_detail.delete()
    return_goods.set_stat()
    return HttpResponse(True)


@jsonapi
def set_return_goods_sku_send(request):
    from flashsale.finance.models import Bill

    content = request.POST
    id = int(content.get("id", None))
    logistic_company_name = content.get("logistic_company", None)
    logistic_company = get_object_or_404(LogisticsCompany,
                                         name=logistic_company_name)
    logistic_no = content.get("logistic_no", None)
    consigner = request.user.username
    return_goods = get_object_or_404(ReturnGoods, id=id)
    if not return_goods.transactor_id:
        return {'code': 1, 'msg': '请选择负责人'}
    if return_goods.status == ReturnGoods.VERIFY_RG:
        # return_goods.supply_notify_refund(Bill.TRANSFER_PAY, return_goods.sum_amount)
        return_goods.delivery_by(logistic_no, logistic_company.id, consigner)
        return {}
    else:
        return {'code': 1, 'msg': '只有已审核的退货可以执行发货'}


def set_transactor(request):
    content = request.POST
    id = int(content.get("id", None))
    transactor = content.get("transactor", None)
    return_goods = get_object_or_404(ReturnGoods, id=id)
    return_goods.set_transactor(transactor)
    return HttpResponse(True)


def set_return_goods_failed(request):
    content = request.POST
    id = int(content.get("id", None))
    return_goods = get_object_or_404(ReturnGoods, id=id)
    if return_goods.status == ReturnGoods.DELIVER_RG:
        return_goods.set_failed()
        return HttpResponse(True)
    else:
        res = {"success": False, 'desc': u'只有发货了才能退货失败加库存'}
        return HttpResponse(json.dump(res))


def change_sum_price(request):
    content = request.POST
    id = content.get("id", None)
    sum_amount = content.get("sum_amount", None)
    if id is None or sum_amount is None:
        return HttpResponse(False)
    id = int(id)
    sum_price = float(sum_amount)
    user_id = request.user.id
    rg = ReturnGoods.objects.get(id=id)
    rg.sum_amount = sum_price
    rg.save()
    # update_model_fields(rg, update_fields=['sum_amount'])
    change_sum_price_des = u"仓库退货单总金额改为_{0}"
    log_action(user_id, rg, CHANGE, change_sum_price_des.format(sum_price))
    rgdts = rg.rg_details.all()
    price = sum_price / rg.return_num if rg.return_num != 0 else 0
    rgdts.update(price=price)
    return HttpResponse(True)


def change_product_inventory(rg, actioner, actor_id):
    """
        仓库审核通过退货单的时候减少对应商品的库存
    """
    rg.consigner = actioner
    update_model_fields(rg, update_fields=['consigner'])
    rg_details = rg.rg_details.all()
    try:
        product = Product.objects.get(id=rg.product_id)
    except Product.DoesNotExist:
        return
    for rd in rg_details:
        try:
            psk = ProductSku.objects.get(id=rd.skuid)
            acrion_invenctory_num(product, psk, rd, actor_id)
        except ProductSku.DoesNotExist:
            return


def acrion_invenctory_num(product, psk, rd, actor_id):
    # 减少库存sku的数量
    psk_quantity = psk.quantity
    if psk_quantity >= rd.num:
        psk.quantity = F("quantity") - rd.num
        update_model_fields(psk, update_fields=['quantity'])  # 更新字段方法
    else:
        psk.quantity = 0
        update_model_fields(psk, update_fields=['quantity'])  # 更新字段方法
    action_desc = u"仓库审核退货单通过->将原来库存{0}更新为{1}".format(psk_quantity,
                                                      psk.quantity)
    log_action(actor_id, psk, CHANGE, action_desc)

    # 减少库存商品的数量
    product_af = Product.objects.get(id=product.id)
    pro_collect_num = product_af.collect_num  # 原来的库存数量
    if pro_collect_num >= rd.num:
        product_af.collect_num = F("collect_num") - rd.num
        update_model_fields(product_af, update_fields=['collect_num'])  # 更新字段方法
    else:
        product_af.collect_num = 0
        update_model_fields(product_af, update_fields=['collect_num'])  # 更新字段方法
    pro_action_desc = u"仓库审核退货单通过->将原来库存{0}更新为{1}".format(
        pro_collect_num, product_af.collect_num)
    log_action(actor_id, product_af, CHANGE, pro_action_desc)

    # 减少库存 减去次品数
    sku_inferior_num = psk.sku_inferior_num
    if sku_inferior_num >= rd.inferior_num:
        psk.sku_inferior_num = F("sku_inferior_num") - rd.inferior_num
        update_model_fields(psk, update_fields=['sku_inferior_num'])  # 更新字段方法
    else:
        psk.sku_inferior_num = 0
        update_model_fields(psk, update_fields=['sku_inferior_num'])  # 更新字段方法
    action_desc = u"仓库审核退货单通过->将原来次品数量{0}更新为{1}".format(sku_inferior_num,
                                                        psk.sku_inferior_num)
    log_action(actor_id, psk, CHANGE, action_desc)


from shopback.refunds.models import RefundProduct


def acrion_product_num(outer_id, sku_out_id, num, can_reuse):
    try:
        actioner = 19  # 操作用户的id systemoa 641
        pro = Product.objects.get(outer_id=outer_id)
        psk = ProductSku.objects.get(product=pro.id, outer_id=sku_out_id)
        if can_reuse:  # 可以二次销售　正品　更新 quantity
            before_num = psk.quantity
            psk.quantity = F('quantity') + num  # 增加历史库存数
            update_model_fields(psk, update_fields=['quantity'])  # 更新字段方法
            log_action(actioner, psk, CHANGE,
                       u"更新历史{0}+{1}退货商品到产品库存中".format(before_num,
                                                       psk.quantity))
            before_pro_num = pro.collect_num
            pro.collect_num = F('collect_num') + num
            update_model_fields(pro, update_fields=['collect_num'])  # 更新字段方法
            log_action(actioner, pro, CHANGE,
                       u"更新历史{0}+{1}退货商品到产品库存中".format(before_pro_num,
                                                       psk.quantity))
        else:
            before_num = psk.sku_inferior_num
            psk.sku_inferior_num = F('sku_inferior_num') + num  # 增加历史库存数
            update_model_fields(psk,
                                update_fields=['sku_inferior_num'])  # 更新字段方法
            log_action(actioner, psk, CHANGE,
                       u"更新历史{0}+{1}退货次品到产品库存次品中".format(before_num,
                                                         psk.sku_inferior_num))
        print "usual :", outer_id, sku_out_id, num
    except ProductSku.DoesNotExist:
        print "exption :ProductSku mutil", outer_id, sku_out_id, num
    except Product.DoesNotExist:
        print "exption :ProductSku mutil", outer_id, sku_out_id, num
    except Product.MultipleObjectsReturned:
        print "exption :ProductSku mutil", outer_id, sku_out_id, num
    except ProductSku.MultipleObjectsReturned:
        print "exption :ProductSku mutil", outer_id, sku_out_id, num
    except:
        print "未知异常", outer_id, sku_out_id, num


def update_refundpro_to_product(can_reuse=False):
    endtime = datetime.datetime(2015, 10, 8, 17, 20, 0)
    actioner = 19  # 操作用户的id systemoa 641
    rep_dic = {}
    # can_reuse=False　不可以二次销售的　次品       #　can_reuse=True 可以二次销售的　正品
    re_prods = RefundProduct.objects.filter(is_finish=False,
                                            can_reuse=can_reuse,
                                            created__lte=endtime)

    for rp in re_prods:
        if rep_dic.has_key(rp.outer_id):
            if rep_dic[rp.outer_id].has_key(rp.outer_sku_id):
                rep_dic[rp.outer_id][rp.outer_sku_id] += rp.num
            else:
                rep_dic[rp.outer_id][rp.outer_sku_id] = rp.num
        else:
            rep_dic[rp.outer_id] = {rp.outer_sku_id: rp.num}
        rp.is_finish = True
        update_model_fields(rp, update_fields=['is_finish'])  # 更新字段方法
        log_action(actioner, rp, CHANGE,
                   u"更新历史退货商品到产品库存时　修改成处理完成")  # systemoa 添加log action

    for pr in rep_dic.items():
        outer_id = pr[0]
        for sku in pr[1].items():
            sku_out_id = sku[0]
            num = sku[1]
            # 修改该商品的该sku库存
            acrion_product_num(outer_id, sku_out_id, num, can_reuse)


def export_return_goods(request):
    def _parse_name(product_name):
        name, color = ('-',) * 2
        parts = product_name.rsplit('/', 1)
        if len(parts) > 1:
            name, color = parts[:2]
        elif len(parts) == 1:
            name = parts[0]
        return name, color

    rg_id = int(request.GET['rg_id'])
    rg = ReturnGoods.objects.get(id=rg_id)

    image_width = 25
    image_height = 125
    buff = StringIO()
    workbook = xlsxwriter.Workbook(buff)
    worksheet = workbook.add_worksheet()

    merge_format = workbook.add_format({
        'border': 1,
        'align': 'center',
        'valign': 'vcenter'
    })
    bold_format = workbook.add_format({'bold': True})
    money_format = workbook.add_format({'num_format': '0.00'})

    worksheet.set_column('A:A', 18)
    worksheet.set_column('B:B', 30)
    worksheet.set_column('C:C', 30)
    worksheet.set_column('E:E', image_width)

    worksheet.write('A1', '供应商名称:', bold_format)
    supplier_name = ''
    if rg.supplier:
        supplier_name = rg.supplier.supplier_name
    worksheet.merge_range('B1:E1', supplier_name)
    worksheet.write('A2', '收件人:', bold_format)
    worksheet.merge_range('B2:E2', '')
    worksheet.write('A3', '手机/电话:', bold_format)
    worksheet.merge_range('B3:E3', '')
    worksheet.write('A4', '收件地址:', bold_format)
    worksheet.merge_range('B4:E4', '')

    worksheet.write('A6', '商品名称', bold_format)
    worksheet.write('B6', '产品货号', bold_format)
    worksheet.write('C6', '颜色', bold_format)
    worksheet.write('D6', '规格', bold_format)
    worksheet.write('E6', '图片', bold_format)
    worksheet.write('F6', '数量', bold_format)
    worksheet.write('G6', '单项价格', bold_format)
    worksheet.write('H6', '总价', bold_format)

    row = 6
    all_price = decimal.Decimal('0')
    all_quantity = 0

    saleproduct_ids = set()
    for product in rg.products:
        saleproduct_ids.add(product.sale_product)

    saleproducts_dict = {}
    for saleproduct in SaleProduct.objects.filter(id__in=list(saleproduct_ids)):
        saleproducts_dict[saleproduct.id] = {
            'supplier_sku': saleproduct.supplier_sku,
            'product_link': saleproduct.product_link
        }

    warehouse_stats = dict.fromkeys([WARE_SH, WARE_GZ], 0)
    for product in rg.products_item_sku():
        for detail_item in product.detail_items:
            num = detail_item.num
            if num <= 0:
                continue

            sku = detail_item.product_sku
            name, color = _parse_name(product.name)
            properties_name = sku.properties_name or sku.properties_alias
            pic_path = product.pic_path.strip()
            if pic_path:
                pic_path = common.utils.url_utf8_quote(pic_path.encode('utf-8'))
                pic_path = '%s?imageMogr2/thumbnail/560/crop/560x480/format/jpg' % pic_path
            cost = detail_item.price
            saleproduct_dict = saleproducts_dict.get(product.sale_product) or {}
            supplier_sku = saleproduct_dict.get('supplier_sku') or ''
            product_link = saleproduct_dict.get('product_link') or ''

            if product.ware_by in [WARE_SH, WARE_GZ]:
                warehouse_stats[product.ware_by] += 1

            all_quantity += num
            all_price += decimal.Decimal(str(num * cost))

            worksheet.write(row, 0, name)
            worksheet.write(row, 1, supplier_sku)
            worksheet.write(row, 2, color)
            worksheet.write(row, 3, properties_name)
            if pic_path:
                opt = {'image_data':
                           io.BytesIO(urllib.urlopen(pic_path).read()),
                       'x_scale': 0.25,
                       'y_scale': 0.25}
                if product_link:
                    opt['url'] = product_link
                worksheet.set_row(row, image_height)
                worksheet.insert_image(row, 4, pic_path, opt)
            worksheet.write(row, 5, num)
            worksheet.write(row, 6, round(cost, 2))
            worksheet.write(row, 7, round(cost * num, 2))
            row += 1

    worksheet.write(row, 4, '总数:', bold_format)
    worksheet.write(row, 5, all_quantity)
    worksheet.write(row, 6, '总计:', bold_format)
    worksheet.write(row, 7, all_price, money_format)

    row += 1
    worksheet.write(row, 0, '寄件地址:', bold_format)
    ware = max(warehouse_stats.items(), key=lambda x: x[1])[0]
    if ware == WARE_SH:
        warehouse = '上海市佘山镇吉业路245号5号楼'
    else:
        warehouse = '广州市白云区太和镇永兴村龙归路口悦博大酒店对面龙门公寓3楼'
    worksheet.merge_range(row, 1, row, 5, warehouse)
    worksheet.write(row + 1, 0, '支付宝账号:', bold_format)
    worksheet.merge_range(row + 1, 1, row + 1, 5,
                          'xiaoxiaoshijie@unilittles.com')

    workbook.close()
    filename = '%s-%d.xlsx' % (rg.created.strftime('%Y%m%d'), rg.id)
    response = HttpResponse(
        buff.getvalue(),
        content_type=
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment;filename=%s' % filename
    return response


def mark_unreturn(request):
    id_ = int(request.POST['id'])
    sku_id = int(request.POST['sku_id'])
    rg = get_object_or_404(ReturnGoods, id=id_)
    rg_detail = rg.rg_details.get(skuid=sku_id)
    rg_detail.delete()
    rg.set_stat()

    rows = UnReturnSku.objects.filter(sku_id=sku_id)
    if rows:
        row = rows[0]
        row.status = UnReturnSku.EFFECT
        row.save()
        for row in rows:
            row.delete()
    else:
        sku = ProductSku.objects.get(id=sku_id)
        saleproduct_id = sku.product.sale_product
        saleproduct = SaleProduct.objects.get(id=saleproduct_id)
        supplier = saleproduct.sale_supplier

        unreturn_sku = UnReturnSku(supplier=supplier,
                                   sale_product=saleproduct,
                                   product=sku.product,
                                   sku=sku,
                                   creater=request.user,
                                   status=UnReturnSku.EFFECT)
        unreturn_sku.save()
    return HttpResponse(True)


@jsonapi
def returngoods_add_sku(request):
    form = forms.ReturnGoodsAddSkuForm(request.POST)
    if not form.is_valid():
        raise Exception(form.error_message)
    rg_id = form.cleaned_data['rg_id']
    sku_id = form.cleaned_data['sku_id']
    sku = get_object_or_404(ProductSku, id=sku_id)
    num = form.cleaned_data['num']
    inferior = form.cleaned_data['inferior']
    inferior = bool(inferior)
    rg = get_object_or_404(ReturnGoods, id=rg_id)
    supplier = sku.product.get_supplier()
    # if supplier.id != rg.supplier_id:
    #     raise Exception(u'只能添加此供应商的SKU')
    rg = ReturnGoods.objects.get(id=rg_id)
    rg.add_sku(sku_id, num, inferior=inferior)
    return {'code': 0}


@jsonapi
def returngoods_deal(request):
    form = forms.DealForm(request.POST)
    if not form.is_valid():
        return {'code': 1, 'msg': '参数错误'}

    rg = ReturnGoods.objects.get(id=form.cleaned_data['rg_id'])
    returngoods_type = ContentType.objects.get(app_label='dinghuo',
                                               model='returngoods')
    bill_relation = BillRelation.objects.filter(content_type=returngoods_type,
                                                object_id=rg.id).exclude(
        bill__type=Bill.DELETE).order_by('-id').first()
    if not bill_relation:
        return {'code': 1, 'msg': '找不到账单'}
    bill = bill_relation.bill
    for bill_relation in bill.billrelation_set.all():
        relation_object = bill_relation.get_based_object()
        if hasattr(relation_object, 'deal'):
            relation_object.deal(form.cleaned_data['attachment'])

    bill.receive_method = form.cleaned_data['receive_method']
    bill.plan_amount = form.cleaned_data['amount']
    bill.note = '\r\n'.join([x for x in [bill.note, form.cleaned_data['note']]])
    bill.attachment = form.cleaned_data['attachment']
    bill.status = Bill.STATUS_DEALED
    bill.transcation_no = form.cleaned_data['transaction_no']
    bill.save()
    return {'bill_id': bill.id}


class ReturnGoodsViewSet(viewsets.GenericViewSet):
    renderer_classes = (renderers.JSONRenderer,)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = ReturnGoods.objects.all()

    @list_route(methods=['post'])
    def gen_by_supplier(self, request):
        supplier_id = int(request.POST.get('supplier_id') or 0)
        supplier = get_object_or_404(SaleSupplier, pk=supplier_id)
        returngoods = ReturnGoods.generate_by_supplier(supplier.id, request.user.username)
        return Response('OK')

    @detail_route(methods=['get'])
    def create_psi_by_rgdetail(self, request, pk):
        return Response(pk)


    @detail_route(methods=['post'])
    def psi_has_pid(self,request, pk):
        content = request.POST
        returngoods_id = content.get("returngoods_id", None)
        return_good = ReturnGoods.objects.get(id=returngoods_id)
        rg_detail = return_good.rg_details.all()
        pid_count = 0
        for i in rg_detail:
            if PackageSkuItem.objects.filter(sale_order_id=i.id):
                pksi = PackageSkuItem.objects.filter(sale_order_id=i.id).first()
                if pksi.package_order_pid:
                    pid_count = pid_count + 1
        if pid_count == len(rg_detail):
            info = {"status": True, "info": "全部都已生成了packageOrder"}
        elif pid_count == 0:
            info = {"status": False, "info": "这个退货单里面的记录并没有生成任何一个packageorder"}
        else:
            info = {"status": True, "info": "这个退货单里面的记录有些有packageorder有些没有"}

        return HttpResponse(json.dumps(info), content_type="application/json", status=200)


    @detail_route(methods=['post'])
    def create_psi_by_rgdetail(self, request, pk):
        content = request.POST
        returngoods_id = pk
        return_good = ReturnGoods.objects.get(id=returngoods_id)
        supplier_addr = return_good.get_supplier_addr()
        if not supplier_addr:
            return HttpResponse(json.dumps({"status": False, "reason": "供应商信息不存在,请填写供应商地址信息"}),
                                content_type="application/json",
                                status=200)
        elif not supplier_addr.is_complete():
            return HttpResponse(json.dumps({"status": False, "reason": "供应商信息不完整,请完善供应商地址信息"}),
                                content_type="application/json",
                                status=200)

        rgdetail_ids = content.get("RGdetail_ids")
        type = ''
        if return_good.type == ReturnGoods.TYPE_COMMON:
            type = 2
        # rgdetail_ids = json.loads(rgdetail_ids)
        # RGdetail = RGDetail.objects.filter(id__in=rgdetail_ids)
        rgdetail = return_good.rg_details.all()
        psi_id = []
        print content.get("RGdetail_ids")
        print content.get("supplier_id")
        for i in rgdetail:
            sku_id = i.skuid
            sale_order_id = i.id
            sale_trade_id = i.return_goods.id
            if all([not type,i.type,i.num]):
                print [not type,i.type,i.num]
                type = 3
            if all([not type,i.type,i.inferior_num]):
                print [not type, i.type, i.inferior_num]
                type = 4
            num = i.num
            title = SkuStock.objects.get(sku_id=i.skuid).product.name
            pic_path = SkuStock.objects.get(sku_id=i.skuid).product.pic_path
            sku_properties_name = i.product_sku.properties_name
            rg_detail_info = {"sku_id": sku_id, "sale_order_id": sale_order_id, "sale_trade_id": sale_trade_id,
                              "type": type, "pay_time": return_good.created, "num": num,
                              "title": title, "pic_path": pic_path, "sku_properties_name": sku_properties_name,
                              "status":'assigned'}
            print rg_detail_info
            if PackageSkuItem.objects.filter(sale_order_id=i.id):
                psi = PackageSkuItem.objects.filter(sale_order_id=i.id).first()
                if type != 2:
                    psi_id.append(psi.id)
                    continue
                PackageSkuItem.objects.filter(sale_order_id=i.id).update(**rg_detail_info)
                psi_id.append(psi.id)
                if psi.package_order_pid:
                    PackageOrder.objects.filter(pid=psi.package_order_pid).update(redo_sign=True,
                                                                                   is_picking_print=False)

            else:
                psi = PackageSkuItem.objects.create(**rg_detail_info)
                psi.return_merge()
                psi_id.append(psi.id)
        return HttpResponse(json.dumps({"status": True, "psi_id": psi_id}), content_type="application/json",
                            status=200)

