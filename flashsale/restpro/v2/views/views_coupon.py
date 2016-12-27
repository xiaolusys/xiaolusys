# coding=utf-8
import datetime
import logging

from django.db import transaction
from django.db.models import Q, Sum
from rest_framework import viewsets
from rest_framework import authentication
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.decorators import list_route, detail_route
from rest_framework import exceptions
from rest_framework import filters

from flashsale.restpro import permissions as perms
from flashsale.restpro.v2.serializers import CouponTransferRecordSerializer

from flashsale.coupon.models import CouponTransferRecord, UserCoupon
from flashsale.pay.models import Customer, SaleOrder
from flashsale.pay.models.product import ModelProduct
from flashsale.pay.apis.v1.customer import get_customer_by_django_user, get_customer_by_id

from flashsale.coupon.apis.v1.transfer import agree_apply_transfer_record, reject_apply_transfer_record, \
    get_freeze_boutique_coupons_by_transfer, cancel_return_2_sys_transfer
from flashsale.coupon.apis.v1.usercoupon import return_transfer_coupon, transfer_coupons
from flashsale.coupon.apis.v1.transfer import coupon_exchange_saleorder

from flashsale.xiaolumm.tasks.tasks_mama_dailystats import task_calc_xlmm_elite_score
from flashsale.xiaolumm.models import ReferalRelationship, XiaoluMama, OrderCarry
from flashsale.xiaolumm.apis.v1.xiaolumama import get_mama_by_openid

logger = logging.getLogger(__name__)


def get_charged_mama(user):
    customer = Customer.objects.normal_customer.filter(user=user).first()
    if customer:
        xlmm = customer.get_charged_mama()
        if xlmm:
            return xlmm
    return None


def get_referal_from_mama_id(to_mama_id):
    rr = ReferalRelationship.objects.filter(referal_to_mama_id=to_mama_id).first()
    if rr:
        return rr.referal_from_mama_id
    return None


def process_transfer_coupon(customer_id, init_from_customer_id, record):
    coupons = UserCoupon.objects.filter(customer_id=customer_id, coupon_type=UserCoupon.TYPE_TRANSFER,
                                        status=UserCoupon.UNUSED, template_id=record.template_id)
    if coupons.count() < record.coupon_num:
        info = u"您的券库存不足，请立即购买!"
        return {"code": 3, "info": info}

    now = datetime.datetime.now()
    with transaction.atomic():
        trs = CouponTransferRecord.objects.filter(order_no=record.order_no)
        trs.update(transfer_status=CouponTransferRecord.DELIVERED, modified=now)  # 更新为已经完成

        coupon_from_mama_id = record.coupon_from_mama_id
        init_customer = get_customer_by_id(init_from_customer_id)
        init_mama = init_customer.get_xiaolumm()
        mama_id = init_mama.id
        chain = ReferalRelationship.get_ship_chain(mama_id, coupon_from_mama_id)  # 获取推荐关系链

        transfer_coupons(coupons[0:record.coupon_num], init_from_customer_id, record.id, chain)  # 转券

    update_coupons = CouponTransferRecord.objects.filter(order_no=record.order_no)
    for update_coupon in update_coupons:
        task_calc_xlmm_elite_score(update_coupon.coupon_to_mama_id)  # 计算妈妈积分
    return {"code": 0, "info": u"发放成功"}


class CouponTransferRecordFilter(filters.FilterSet):
    class Meta:
        model = CouponTransferRecord
        fields = ['transfer_type', 'transfer_status']


class CouponTransferRecordViewSet(viewsets.ModelViewSet):
    paginate_by = 10
    page_query_param = 'page'
    paginate_by_param = 'page_size'
    max_paginate_by = 100

    queryset = CouponTransferRecord.objects.all()
    serializer_class = CouponTransferRecordSerializer

    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)
    filter_class = CouponTransferRecordFilter

    def list(self, request, *args, **kwargs):
        return exceptions.APIException('METHOD NOT ALLOW')

    def create(self, request, *args, **kwargs):
        return exceptions.APIException('METHOD NOT ALLOW')

    def update(self, request, *args, **kwargs):
        return exceptions.APIException('METHOD NOT ALLOW')

    def destroy(self, request, *args, **kwargs):
        return exceptions.APIException('METHOD NOT ALLOW')

    @list_route(methods=['POST'])
    def start_transfer(self, request, *args, **kwargs):
        content = request.data
        coupon_num = content.get("coupon_num") or None
        product_id = content.get("product_id")
        if not (coupon_num and coupon_num.isdigit() and product_id and product_id.isdigit()):
            return Response({"code": 1, "info": u"coupon_num或product_id错误！"})

        from shopback.items.models import Product
        from flashsale.pay.models import ModelProduct

        product = Product.objects.filter(id=product_id).first()
        model_product = ModelProduct.objects.filter(id=product.model_id).first()

        template_id = model_product.extras.get("template_id")
        if not template_id:
            return Response({"code": 2, "info": u"template_id错误！"})
        res = CouponTransferRecord.init_transfer_record(request.user, coupon_num, template_id, product_id)
        return Response(res)

    def start_return_coupon(self, request, *args, **kwargs):
        pass

    def update_coupon(self, request, *args, **kwargs):
        pass

    @list_route(methods=['GET'])
    def profile(self, request, *args, **kwargs):
        mama = get_charged_mama(request.user)
        if not mama:
            return Response({"code": 1, "info": u"你还没加入精英妈妈！"})
        mama_id = mama.id
        stock_num, in_num, out_num = CouponTransferRecord.get_stock_num(mama_id)
        waiting_in_num = CouponTransferRecord.get_waiting_in_num(mama_id)
        waiting_out_num = CouponTransferRecord.get_waiting_out_num(mama_id)
        is_elite_mama = mama.is_elite_mama
        direct_buy = mama.can_buy_transfer_coupon()  # 可否直接购买精品券
        direct_buy_link = "http://m.xiaolumeimei.com/mall/buycoupon"
        upgrade_score = mama.get_upgrade_score()
        elite_level = mama.elite_level

        return Response({"mama_id": mama_id, "stock_num": stock_num, "waiting_in_num": waiting_in_num,
                         "waiting_out_num": waiting_out_num, "bought_num": in_num, "is_elite_mama": is_elite_mama,
                         "direct_buy": direct_buy, "direct_buy_link": direct_buy_link, "elite_score": mama.elite_score,
                         "elite_level": elite_level, "upgrade_score": upgrade_score})

    @detail_route(methods=['POST'])
    def process_coupon(self, request, pk=None, *args, **kwargs):
        if not (pk and pk.isdigit()):
            return Response({"code": 1, "info": u"请求错误"})

        mama = get_charged_mama(request.user)
        mama_id = mama.id
        record = CouponTransferRecord.objects.filter(id=pk).first()
        res = {"code": 1, "info": u"无记录审核或不能审核"}

        if record and record.can_process(mama_id):
            stock_num = CouponTransferRecord.get_coupon_stock_num(mama_id, record.template_id)
            if stock_num >= record.coupon_num:
                customer = Customer.objects.filter(unionid=mama.unionid).first()
                init_from_mama = XiaoluMama.objects.filter(id=record.init_from_mama_id).first()
                init_from_customer = Customer.objects.filter(unionid=init_from_mama.unionid,
                                                             status=Customer.NORMAL).first()
                res = process_transfer_coupon(customer.id, init_from_customer.id, record)
            else:
                # record.transfer_status = CouponTransferRecord.PROCESSED
                # record.save(update_fields=['transfer_status'])
                # res = CouponTransferRecord.gen_transfer_record(request.user, record)
                # 2016-12-21 中间的妈妈券不够的话，进行提示，自己找上级申请，不自动跟她们申请，以免她们混乱
                info = u"您的券库存不足，请立即购买!"
                res = {"code": 3, "info": info}

        return Response(res)

    @detail_route(methods=['POST'])
    def cancel_coupon(self, request, pk=None, *args, **kwargs):
        if not (pk and pk.isdigit()):
            return Response({"code": 1, "info": u"请求错误"})

        mama = get_charged_mama(request.user)
        mama_id = mama.id

        record = CouponTransferRecord.objects.filter(id=pk).first()
        info = u"无取消记录或不能取消"
        if record and record.can_cancel(mama_id):
            record.transfer_status = CouponTransferRecord.CANCELED
            record.save(update_fields=['transfer_status'])
            info = u"取消成功"
        return Response({"code": 0, "info": info})

    @detail_route(methods=['POST'])
    def transfer_coupon(self, request, pk=None, *args, **kwargs):
        if not (pk and pk.isdigit()):
            return Response({"code": 1, "info": u"请求错误"})
        customer = get_customer_by_django_user(user=request.user)
        mama = customer.get_charged_mama()
        mama_id = mama.id
        info = u"无取消记录或不能取消"

        record = CouponTransferRecord.objects.filter(id=pk).first()
        init_from_mama = XiaoluMama.objects.filter(id=record.init_from_mama_id).first()
        init_from_customer = Customer.objects.filter(unionid=init_from_mama.unionid, status=Customer.NORMAL).first()
        stock_num = CouponTransferRecord.get_coupon_stock_num(mama_id, record.template_id)
        if stock_num < record.coupon_num:
            return Response({"code": 2, "info": u"您的精品券库存不足，请立即购买!"})

        coupon_from_mama_id = record.coupon_from_mama_id
        tmama_id = init_from_mama.id
        chain = ReferalRelationship.get_ship_chain(tmama_id, coupon_from_mama_id)

        if record and record.can_process(mama_id) and mama.can_buy_transfer_coupon():
            coupons = UserCoupon.objects.filter(customer_id=customer.id, coupon_type=UserCoupon.TYPE_TRANSFER,
                                                status=UserCoupon.UNUSED, template_id=record.template_id)
            if coupons.count() < record.coupon_num:
                return Response({"code": 3, "info": u"您的券库存不足，请立即购买!"})
            now = datetime.datetime.now()
            trds = CouponTransferRecord.objects.filter(order_no=record.order_no)
            with transaction.atomic():
                trds.update(transfer_status=CouponTransferRecord.DELIVERED, modified=now)
                transfer_coupons(coupons[0:record.coupon_num], init_from_customer.id, int(pk), chain)  # 转券
            info = u"发放成功"
            for tr in trds:
                task_calc_xlmm_elite_score(tr.coupon_to_mama_id)  # 计算妈妈积分
        return Response({"code": 0, "info": info})

    @list_route(methods=['GET'])
    def list_out_coupons(self, request, *args, **kwargs):
        content = request.GET
        transfer_status = content.get("transfer_status") or None
        status = CouponTransferRecord.EFFECT

        mama = get_charged_mama(request.user)
        mama_id = mama.id
        coupons = self.queryset.filter(coupon_from_mama_id=mama_id, status=status).exclude(transfer_type__in=[
            CouponTransferRecord.OUT_CASHOUT,
            CouponTransferRecord.IN_RETURN_COUPON]).order_by('-created')
        if transfer_status:
            coupons = coupons.filter(transfer_status=transfer_status.strip())

        coupons = self.paginate_queryset(coupons)
        serializer = CouponTransferRecordSerializer(coupons, many=True)
        data = serializer.data

        for entry in data:
            if mama.can_buy_transfer_coupon() and entry["transfer_status"] == CouponTransferRecord.PENDING:
                entry.update({"is_buyable": True})
            else:
                entry.update({"is_buyable": False})

        res = self.get_paginated_response(data)
        return res

    @list_route(methods=['GET'])
    def list_in_coupons(self, request, *args, **kwargs):
        content = request.GET
        transfer_status = content.get("transfer_status") or None
        status = CouponTransferRecord.EFFECT

        mama = get_charged_mama(request.user)
        mama_id = mama.id
        coupons = self.queryset.filter(coupon_to_mama_id=mama_id, status=status).exclude(transfer_type__in=[
            CouponTransferRecord.OUT_CASHOUT,
            CouponTransferRecord.IN_RETURN_COUPON]).order_by('-created')
        if transfer_status:
            coupons = coupons.filter(transfer_status=transfer_status.strip())

        coupons = self.paginate_queryset(coupons)
        serializer = CouponTransferRecordSerializer(coupons, many=True)
        res = self.get_paginated_response(serializer.data)
        return res

    @list_route(methods=['GET'])
    def list_mama_left_coupons(self, request, *args, **kwargs):
        mama = get_charged_mama(request.user)
        mama_id = mama.id

        coupons = CouponTransferRecord.objects.filter(
            Q(transfer_type=CouponTransferRecord.OUT_TRANSFER) | Q(transfer_type=CouponTransferRecord.IN_BUY_COUPON),
            coupon_to_mama_id=mama_id, transfer_status=CouponTransferRecord.DELIVERED).order_by('-created')

        left_coupons = {"code": 0, "info": "成功", "results": []}

        for one_coupon in coupons:
            has_calc = False
            for one_left_coupon in left_coupons["results"]:
                if one_left_coupon["template_id"] == one_coupon.template_id:
                    has_calc = True
                    break
            if has_calc:
                break
            res = CouponTransferRecord.objects.filter(template_id=one_coupon.template_id, coupon_from_mama_id=mama_id,
                                                      transfer_status=CouponTransferRecord.DELIVERED).aggregate(
                n=Sum('coupon_num'))
            out_num = res['n'] or 0

            res = CouponTransferRecord.objects.filter(template_id=one_coupon.template_id, coupon_to_mama_id=mama_id,
                                                      transfer_status=CouponTransferRecord.DELIVERED).aggregate(
                n=Sum('coupon_num'))
            in_num = res['n'] or 0

            stock_num = in_num - out_num
            if stock_num > 0:
                left_coupons["results"].append({"product_img": one_coupon.product_img, "coupon_num": stock_num,
                                                "template_id": one_coupon.template_id, })
        return Response(left_coupons)

    @list_route(methods=['POST'])
    def verify_return_transfer_record(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        """上级妈妈审核流通记录　并冻结该流通记录优惠券
        """
        transfer_record_id = request.POST.get('transfer_record_id')
        verify_func = request.POST.get('verify_func')
        if not transfer_record_id or not verify_func:
            return Response({'code': 1, 'info': '参数错误'})
        transfer_record_id = int(str(transfer_record_id).strip())
        try:
            if verify_func == 'agree':  # 同意
                state = agree_apply_transfer_record(request.user, transfer_record_id)
            elif verify_func == 'reject':  # 拒绝
                state = reject_apply_transfer_record(request.user, transfer_record_id)
            else:
                return Response({'code': 1, 'info': '参数错误'})
        except Exception as e:
            return Response({'code': 3, 'info': '审核异常:%s' % e.message})
        if state:
            return Response({'code': 0, 'info': '审核成功'})
        return Response({'code': 2, 'info': '审核出错'})

    @list_route(methods=['post'])
    def return_transfer_coupon_2_upper(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        """下级妈妈　通过　流通记录　将冻结的流通记录优惠券　解冻退还给上级妈妈
        """
        transfer_record_id = request.POST.get('transfer_record_id')
        if not transfer_record_id:
            return Response({'code': 1, 'info': '参数错误'})
        customer = get_customer_by_django_user(request.user)  # 下属用户返还自己的　券　给上级
        transfer_record_id = int(str(transfer_record_id).strip())
        coupons = get_freeze_boutique_coupons_by_transfer(transfer_record_id, customer.id)
        if not coupons:
            return Response({'code': 3, 'info': '优惠券没有找到'})
        state = return_transfer_coupon(coupons)  # 返还券
        if not state:
            return Response({'code': 2, 'info': '操作失败'})
        return Response({'code': 0, 'info': '操作成功'})

    @list_route(methods=['post'])
    def cancel_return_2_sys_transfer_coupon(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        """取消　退券　给　系统
        """
        transfer_record_id = request.POST.get('transfer_record_id')
        if not transfer_record_id:
            return Response({'code': 1, 'info': '参数错误'})
        customer = get_customer_by_django_user(request.user)  # 下属用户返还自己的　券　给上级
        transfer_record_id = int(str(transfer_record_id).strip())
        try:
            cancel_return_2_sys_transfer(transfer_record_id, customer=customer)
        except Exception as e:
            return Response({'code': 3, 'info': '取消出错:%s' % e.message})
        return Response({'code': 0, 'info': '已经取消'})

    @list_route(methods=['get'])
    def list_return_transfer_record(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        """下属退回自己的　优惠券　流通记录　列表
        """
        customer = get_customer_by_django_user(request.user)
        if not customer.unionid:
            return Response({'code': 1, 'info': '用户错误'})
        mama = get_mama_by_openid(customer.unionid)
        if not mama:
            return Response({'code': 2, 'info': '妈妈记录没找到'})
        queryset = CouponTransferRecord.objects.get_return_transfer_coupons().filter(
            coupon_to_mama_id=mama.id).order_by('-created')
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @list_route(methods=['get'])
    def list_from_my_records(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        """向上级申请退券的　优惠券　流通记录　列表
        """
        customer = get_customer_by_django_user(request.user)
        if not customer.unionid:
            return Response({'code': 1, 'info': '用户错误'})
        mama = get_mama_by_openid(customer.unionid)
        if not mama:
            return Response({'code': 2, 'info': '妈妈记录没找到'})
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(coupon_from_mama_id=mama.id,
                                   transfer_type__in=[CouponTransferRecord.OUT_CASHOUT,
                                                      CouponTransferRecord.IN_RETURN_COUPON]).order_by('-created')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class CouponExchgOrderViewSet(viewsets.ModelViewSet):
    queryset = CouponTransferRecord.objects.all()
    serializer_class = CouponTransferRecordSerializer

    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)

    def list(self, request, *args, **kwargs):
        return exceptions.APIException('METHOD NOT ALLOW')

    def create(self, request, *args, **kwargs):
        return exceptions.APIException('METHOD NOT ALLOW')

    def update(self, request, *args, **kwargs):
        return exceptions.APIException('METHOD NOT ALLOW')

    def partial_update(self, request, *args, **kwargs):
        return exceptions.APIException('METHOD NOT ALLOW')

    def retrieve(self, request, *args, **kwargs):
        return exceptions.APIException('METHOD NOT ALLOW')

    def destroy(self, request, *args, **kwargs):
        return exceptions.APIException('METHOD NOT ALLOW')

    @list_route(methods=['GET'])
    def list_can_exchg_orders(self, request, *args, **kwargs):
        content = request.GET
        exchg_orders = None
        customer = Customer.objects.normal_customer.filter(user=request.user).first()
        if customer:
            mama = get_charged_mama(request.user)
            mama_id = mama.id
            exchg_orders = OrderCarry.objects.filter(mama_id=mama_id,
                                                     carry_type__in=[OrderCarry.WAP_ORDER, OrderCarry.APP_ORDER],
                                                     status__in=[OrderCarry.ESTIMATE, OrderCarry.CONFIRM],
                                                     date_field__gt='2016-11-30')
        results = []
        if exchg_orders:
            for entry in exchg_orders:
                # find sale trade use coupons
                sale_order = SaleOrder.objects.filter(oid=entry.order_id).first()
                if not sale_order:
                    continue
                if sale_order and sale_order.extras.has_key('exchange'):
                    continue

                user_coupon = UserCoupon.objects.filter(trade_tid=sale_order.sale_trade.tid).first()
                if user_coupon:
                    use_template_id = user_coupon.template_id
                else:
                    use_template_id = None

                # find modelproduct

                model_product = ModelProduct.objects.filter(id=sale_order.item_product.model_id, is_boutique=True).first()
                if model_product and model_product.extras.has_key('payinfo') \
                        and model_product.extras['payinfo'].has_key('coupon_template_ids'):

                    if model_product.extras['payinfo']['coupon_template_ids'] and len(
                            model_product.extras['payinfo']['coupon_template_ids']) > 0:

                        template_ids = model_product.extras['payinfo']['coupon_template_ids']
                        template_id = model_product.extras['payinfo']['coupon_template_ids'][0]
                        # 用的券全部是精品券那就无法兑换，部分用券部分现金还是能兑换的
                        if template_ids and template_id:
                            # if use_template_id and use_template_id in template_ids:
                            #     continue
                            if round(sale_order.payment / sale_order.price) > 0:
                                results.append({'exchg_template_id': template_id,
                                                'num': round(sale_order.payment / sale_order.price),
                                                'order_id': entry.order_id, 'sku_img': entry.sku_img,
                                                'contributor_nick': entry.contributor_nick, 'status': entry.status,
                                                'status_display': OrderCarry.STATUS_TYPES[entry.status][1],
                                                'order_value': entry.order_value, 'date_field': entry.date_field})

        #从relationship推荐人中找出购买rmb338的新精英妈妈订单
        from flashsale.xiaolumm.models.models_fortune import ReferalRelationship
        ships = ReferalRelationship.objects.filter(referal_from_mama_id=mama.id, referal_type=XiaoluMama.ELITE, status=ReferalRelationship.VALID)
        for ship in ships:
            if ship.order_id and len(ship.order_id) > 0:
                rmb338_order = SaleOrder.objects.filter(oid=ship.order_id).first()
                if rmb338_order and (not rmb338_order.extras.has_key('exchange')) \
                        and rmb338_order.is_new_elite_deposit():
                    buyer_customer = Customer.objects.normal_customer.filter(id=rmb338_order.buyer_id).first()
                    results.append({'exchg_template_id': 156,
                                    'num': 5,
                                    'order_id': ship.order_id, 'sku_img': rmb338_order.pic_path,
                                    'contributor_nick': buyer_customer.nick, 'status': 2,
                                    'status_display': u'确定收益',
                                    'order_value': round(rmb338_order.payment * 100), 'date_field': rmb338_order.pay_time})
        logger.info({
            'message': u'list can exchange order:result len=%s ' % (len(results)),
            'data': '%s' % content
        })
        return Response(results)

    @list_route(methods=['POST'])
    def start_exchange(self, request, *args, **kwargs):
        content = request.POST
        customer = get_customer_by_django_user(request.user)
        if not customer:
            return Response({"code": 5, "info": u"没有找到用户！"})

        coupon_num = content.get("coupon_num") or None
        order_id = content.get("order_id")
        exchg_template_id = content.get("exchg_template_id")
        if not (coupon_num and coupon_num.isdigit() and exchg_template_id and exchg_template_id.isdigit()):
            logger.warn({
                'message': u'exchange order:coupon_num=%s order_id=%s templateid=%s' % (
                    coupon_num, order_id, exchg_template_id),
                'data': '%s' % content
            })
            return Response({"code": 1, "info": u"coupon_num或exchg_template_id错误！"})

        if int(coupon_num) == 0:
            return Response({"code": 4, "info": u'兑换精品券数量不能为0!'})

        mama = get_charged_mama(request.user)
        mama_id = mama.id

        stock_num = CouponTransferRecord.get_coupon_stock_num(mama_id, exchg_template_id)
        if stock_num < int(coupon_num):
            logger.warn({
                'message': u'exchange order:stock_num=%s < exchg coupon_num=%s ,order_id=%s templateid=%s' % (
                    stock_num, coupon_num, order_id, exchg_template_id),
            })
            return Response({"code": 2, "info": u'您的精品券库存不足，请立即购买!'})

        user_coupons = UserCoupon.objects.filter(customer_id=customer.id, template_id=int(exchg_template_id),
                                                 status=UserCoupon.UNUSED)
        if len(user_coupons) < int(coupon_num):
            logger.warn({
                'message': u'exchange order:user_coupon=%s < exchg coupon_num=%s ,order_id=%s templateid=%s' % (
                    len(user_coupons), coupon_num, order_id, exchg_template_id),
            })
            return Response({"code": 3, "info": u'您的精品券数量不足，请联系微信客服!'})

        coupon_exchange_saleorder(customer, order_id, mama_id, exchg_template_id, coupon_num)
        return Response({'code': 0, 'info': '兑换成功'})
