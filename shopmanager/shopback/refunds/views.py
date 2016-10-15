# -*- encoding:utf8 -*-
import json
import datetime
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.conf import settings
from django.core.urlresolvers import reverse
from auth import staff_requried
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
# from djangorestframework.views import ModelView
from shopback.trades.models import MergeTrade, MergeOrder
from shopback.items.models import Product, ProductSku, Item
from shopback.refunds.models import RefundProduct, Refund, REFUND_STATUS, CS_STATUS_CHOICES
from common.utils import parse_datetime, parse_date, format_time, map_int2str
from shopback.refunds.tasks import updateAllUserRefundOrderTask
from shopback import paramconfig as pcfg
from core.options import log_action, User, ADDITION, CHANGE
from shopback.base.new_renders import new_BaseJSONRenderer
import logging
from rest_framework import authentication
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework.compat import OrderedDict
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer, BrowsableAPIRenderer
from rest_framework.views import APIView
from rest_framework import filters
from . import serializers
from rest_framework import status
from django.db import transaction

from renderers import *
from unrelate_product_handler import update_Unrelate_Prods_Product, update_Product_Collect_Num

logger = logging.getLogger('django.request')
__author__ = 'meixqhi'


@staff_requried(login_url=settings.LOGIN_URL)
def update_interval_refunds(request, dt_f, dt_t):
    dt_f = parse_date(dt_f)
    dt_t = parse_date(dt_t)

    logistics_task = updateAllUserRefundOrderTask.delay(update_from=dt_f, update_to=dt_t)

    ret_params = {'task_id': logistics_task.task_id}

    return HttpResponse(json.dumps(ret_params), content_type='application/json')


############################### 缺货订单商品列表 #################################       
class RefundManagerView(APIView):
    """ docstring for class RefundManagerView """
    serializer_class = serializers.RefundSerializer
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)
    renderer_classes = (RefundManagerRenderer, new_BaseJSONRenderer, BrowsableAPIRenderer)

    def get(self, request, *args, **kwargs):
        handling_refunds = Refund.objects.filter(has_good_return=True, is_reissue=False,
                                                 status__in=(pcfg.REFUND_WAIT_SELLER_AGREE,
                                                             pcfg.REFUND_WAIT_RETURN_GOODS,
                                                             pcfg.REFUND_CONFIRM_GOODS))
        handling_tids = set()
        refund_dict = {}
        for refund in handling_refunds:
            refund_tid = refund.tid.strip()
            if refund_dict.has_key(refund_tid):
                refund_dict[refund_tid]['order_num'] += 1
                refund_dict[refund_tid]['is_reissue'] &= refund.is_reissue
            else:
                handling_tids.add(refund_tid)
                try:
                    receiver_name = MergeTrade.objects.filter(tid=refund_tid).receiver_name
                except:
                    receiver_name = ''
                has_refund_prod = RefundProduct.objects.filter(trade_id=refund_tid).count() > 0
                refund_dict[refund_tid] = {'tid': refund_tid,
                                           'buyer_nick': refund.buyer_nick,
                                           'seller_id': refund.user.id,
                                           'seller_nick': refund.user.nick,
                                           'receiver_name': receiver_name,
                                           'mobile': refund.mobile,
                                           'phone': refund.phone,
                                           'order_num': 1,
                                           'created': refund.created.strftime('%Y.%m.%d'),
                                           'reason': refund.reason,
                                           'desc': refund.desc,
                                           'company_name': refund.company_name,
                                           'sid': refund.sid,
                                           'is_reissue': refund.is_reissue,
                                           'has_refund_prod': has_refund_prod,
                                           'cs_status': dict(CS_STATUS_CHOICES).get(refund.cs_status, u'状态不对'),
                                           'status': dict(REFUND_STATUS).get(refund.status, u'状态不对'),
                                           }

        refund_items = sorted(refund_dict.items(), key=lambda d: d[1]['created'], reverse=True)

        refund_list = [v for k, v in refund_items]
        unrelate_prods = []
        unfinish_prods = RefundProduct.objects.filter(is_finish=False)
        for prod in unfinish_prods:
            prod_trade_id = prod.trade_id
            if not prod_trade_id or (prod_trade_id not in handling_tids):
                unrelate_prods.append(prod)
        return Response({"object": {'refund_trades': refund_list,
                                    'unrelate_prods': serializers.RefundProductSerializer(unrelate_prods,
                                                                                          many=True).data}})
        # Response({"object":{'refund_trades':refund_list,'unrelate_prods':unrelate_prods}})

    def post(self, request, *args, **kwargs):
        content = request.REQUEST
        tid = content.get('tid')
        # print "tid",tid
        seller_id = content.get('seller_id')
        if not tid:
            return Response(u'请输入交易ID')

        trade = get_object_or_404(MergeTrade, tid=tid, user=seller_id)
        try:
            merge_trade = serializers.MergeTradeSerializer(trade).data
        except MergeTrade.DoesNotExist:
            return Response(u'订单未找到')

        refund_orders = serializers.RefundSerializer(Refund.objects.filter(tid=tid), many=True).data
        refund_products = serializers.RefundProductSerializer(RefundProduct.objects.filter(trade_id=tid),
                                                              many=True).data
        # print "55555",refund_orders
        op_str = render_to_string('refunds/refund_order_product.html',
                                  {'refund_orders': refund_orders,
                                   'refund_products': refund_products,
                                   'STATIC_URL': settings.STATIC_URL,
                                   'trade': merge_trade
                                   })

        return Response({'template_string': op_str, 'trade_id': tid,})
        # return { 'refund_orders': refund_orders,'refund_products': refund_products ,'STATIC_URL':settings.STATIC_URL}


############################### 退货商品订单 #################################
class RefundProductView(APIView):
    """ docstring for class RefundProductView """
    serializer_class = serializers.RefundProductSerializer
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)
    renderer_classes = (RefundProductRenderer, new_BaseJSONRenderer, BrowsableAPIRenderer,)

    def get(self, request, *args, **kwargs):

        return Response({})

    def post(self, request, *args, **kwargs):

        content = request.REQUEST
        outer_id = content.get('outer_id')
        outer_sku_id = content.get('outer_sku_id')
        prod_sku = None
        prod = None
        if outer_sku_id:
            try:
                prod_sku = ProductSku.objects.get(product__outer_id=outer_id, outer_id=outer_sku_id)
            except:
                pass
        else:
            try:
                prod = Product.objects.get(outer_id=outer_id)
            except:
                pass
        rf_prod = RefundProduct.objects.filter(outer_id='')
        if rf_prod.count() > 0:
            rf = rf_prod[0]
        else:
            rf = RefundProduct()

        for k, v in content.iteritems():
            hasattr(rf, k) and setattr(rf, k, v)
        rf.trade_id = rf.trade_id.isdigit() and rf.trade_id or ''
        rf.can_reuse = content.get('can_reuse') == 'true' and True or False
        rf.title = prod_sku.product.name if prod_sku else prod.name
        rf.property = prod_sku.properties_alias or prod_sku.properties_name if prod_sku else ''
        rf.save()

        return Response(serializers.RefundProductSerializer(rf).data)


############################### 退货单 #################################       
class RefundView(APIView):
    """ docstring for class RefundView """
    serializer_class = serializers.RefundSerializer
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)
    renderer_classes = (new_BaseJSONRenderer,)

    def get(self, request, *args, **kwargs):

        content = request.REQUEST
        q = content.get('q')
        # q="40270295378417"
        if not q:
            return Response(u'请输入查询内容')

        queryset = Refund.objects.filter(has_good_return=True)
        if q.isdigit():
            rf_prods = queryset.filter(Q(mobile=q) | Q(phone=q) | Q(sid=q) | Q(refund_id=q) | Q(tid=q))
        else:
            rf_prods = queryset.filter(Q(buyer_nick=q) | Q(mobile=q) | Q(phone=q) | Q(sid=q))

        prod_list = []
        for rp in rf_prods:

            tid = rp.tid
            oid = rp.oid

            try:
                order = MergeOrder.objects.get(tid=tid, oid=oid)
                # order = MergeOrder.objects.all()[0]
            except:
                return Response(u'订单未找到')

            outer_id = order.outer_id
            outer_sku_id = order.outer_sku_id

            prod_sku = None
            prod = None
            if outer_sku_id:
                try:
                    prod_sku = ProductSku.objects.get(product__outer_id=outer_id, outer_id=outer_sku_id)
                except:
                    pass
            else:
                try:
                    prod = Product.objects.get(outer_id=outer_id)
                except:
                    pass

            prod_dict = {}
            prod_dict['refund_id'] = rp.refund_id
            prod_dict['buyer_nick'] = rp.buyer_nick
            prod_dict['mobile'] = rp.mobile
            prod_dict['phone'] = rp.phone

            prod_dict['company_name'] = rp.company_name
            prod_dict['sid'] = rp.sid
            prod_dict['created'] = rp.created
            prod_dict['status'] = rp.status

            prod_dict['title'] = prod_sku.product.name if prod_sku else prod.name
            prod_dict['property'] = (prod_sku.properties_alias or prod_sku.properties_name) if prod_sku else ''

            prod_list.append(prod_dict)

        return Response(prod_list)

    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        content = request.REQUEST
        rf = RefundProduct()
        refundproduct = RefundProduct.objects.filter(trade_id=content['trade_id'],
                                                     outer_sku_id=content['outer_sku_id'],
                                                     buyer_phone=content['buyer_phone'],
                                                     title=content['title'],
                                                     outer_id=content['outer_id']).first()
        if refundproduct:
            return Response(serializers.RefundProductSerializer(refundproduct).data)
        for k, v in content.iteritems():
            if k == 'oid':
                if RefundProduct.objects.filter(oid=v).count() != 0:
                    return Response(serializers.RefundProductSerializer(rf).data)
            if k == 'can_reuse':
                v = v == "true" and True or False
            hasattr(rf, k) and setattr(rf, k, v)
        rf.save()
        # 创建一条退货款单记录
        log_action(request.user.id, rf, CHANGE, u'创建退货商品记录')
        update_Unrelate_Prods_Product(pro=rf, req=request)  # 关联退货

        # 创建时候发送消息
        refund_product = RefundProduct.objects.get(id=rf.id)  # 重新获取(避免缓存问题)
        refund_product.send_goods_backed_message()

        update_Product_Collect_Num(pro=rf, req=request)  # 更新产品库存
        if refund_product.check_salerefund_conformably():  # 退货和退款单信息一致
            sale_refund = refund_product.get_sale_refund()
            if not sale_refund:
                return
            is_finish = sale_refund.return_fee_by_refund_product()
            if is_finish:
                refund_product.is_finish = True
        refund_product.save(update_fields=['is_finish'])

        return Response(serializers.RefundProductSerializer(rf).data)


@csrf_exempt
@staff_member_required
def create_refund_exchange_trade(request, seller_id, tid):
    try:
        origin_trade = MergeTrade.objects.get(tid=tid.strip(), user=seller_id)
    except MergeTrade.DoesNotExist:
        return HttpResponseNotFound('<h1>订单未找到 404<h1>')

    refunds = Refund.objects.filter(tid=tid)
    rfprods = RefundProduct.objects.filter(trade_id=tid.strip())
    if rfprods.count() == 0:
        return HttpResponseNotFound('<h1>未找到退货商品 404<h1>')

    dt = datetime.datetime.now()
    merge_trade = MergeTrade.objects.create(
        user=origin_trade.user,
        buyer_nick=origin_trade.buyer_nick,
        type=pcfg.EXCHANGE_TYPE,
        shipping_type=origin_trade.shipping_type,
        logistics_company=origin_trade.logistics_company,
        receiver_name=origin_trade.receiver_name,
        receiver_state=origin_trade.receiver_state,
        receiver_city=origin_trade.receiver_city,
        receiver_district=origin_trade.receiver_district,
        receiver_address=origin_trade.receiver_address,
        receiver_zip=origin_trade.receiver_zip,
        receiver_mobile=origin_trade.receiver_mobile,
        receiver_phone=origin_trade.receiver_phone,
        sys_status=pcfg.WAIT_AUDIT_STATUS,
        status=pcfg.WAIT_SELLER_SEND_GOODS,
        created=dt,
        pay_time=dt,
        modified=dt)
    for prod in rfprods.filter(can_reuse=True):
        merge_order = MergeOrder()
        merge_order.merge_trade = merge_trade
        merge_order.title = prod.title
        merge_order.sku_properties_name = prod.property
        merge_order.outer_id = prod.outer_id
        merge_order.outer_sku_id = prod.outer_sku_id
        merge_order.num = prod.num
        merge_order.seller_nick = origin_trade.user.nick
        merge_order.buyer_nick = origin_trade.buyer_nick
        merge_order.gift_type = pcfg.RETURN_GOODS_GIT_TYPE
        merge_order.sys_status = pcfg.IN_EFFECT
        merge_order.status = pcfg.WAIT_SELLER_SEND_GOODS
        merge_order.created = dt
        merge_order.save()

    refunds.update(is_reissue=True)
    rfprods.update(is_finish=True)
    for refund in refunds:
        try:
            refund.confirm_refund()
        except Exception, exc:
            logger.error(exc.message, exc_info=True)

    log_action(request.user.id, merge_trade, ADDITION, u'创建退换货单')

    return HttpResponseRedirect('/admin/trades/mergetrade/?type__exact=exchange'
                                '&sys_status=WAIT_AUDIT&q=%s' % str(merge_trade.id))


from unrelate_product_handler import update_Product_Collect_Num_By_Delete


@csrf_exempt
@staff_member_required
def delete_trade_order(request, id):
    user_id = request.user.id
    print id
    try:
        refund_prod = RefundProduct.objects.get(id=id)
    except:
        return HttpResponse(json.dumps({'code': 1, 'response_error': u'订单不存在'}),
                            content_type="application/json")

    refund_prod.delete()
    # 删除的时候更新商品库存
    update_Product_Collect_Num_By_Delete(refund_prod, request)

    ret_params = {'code': 0, 'response_content': {'success': True}}

    return HttpResponse(json.dumps(ret_params), content_type="application/json")


@csrf_exempt
@staff_member_required
def relate_refund_product(request):
    content = request.REQUEST
    refund_tid = content.get('refund_tid')
    rpid = content.get('rpid')

    try:
        trade = MergeTrade.objects.get(tid=refund_tid)
    except:
        return HttpResponse(json.dumps({'code': 1, 'response_error': u'订单不存在'}),
                            content_type="application/json")

    try:
        refund_prod = RefundProduct.objects.get(id=rpid)
    except:
        return HttpResponse(json.dumps({'code': 1, 'response_error': u'退回商品不存在'}),
                            content_type="application/json")

    refund_prod.trade_id = trade.tid
    refund_prod.buyer_nick = trade.buyer_nick
    refund_prod.save()

    log_action(request.user.id, refund_prod, CHANGE, u'关联订单')

    ret_params = {'code': 0, 'response_content': {'success': True}}

    return HttpResponse(json.dumps(ret_params), content_type="application/json")
