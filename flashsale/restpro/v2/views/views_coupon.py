# coding=utf-8
import datetime
import logging

from rest_framework import viewsets
from rest_framework import authentication
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.decorators import list_route, detail_route

from flashsale.xiaolumm.models import ReferalRelationship, XiaoluMama

from flashsale.restpro import permissions as perms

from flashsale.coupon.models import CouponTransferRecord, UserCoupon
from flashsale.pay.models import Customer
from flashsale.restpro.v2.serializers import CouponTransferRecordSerializer

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
    coupons = UserCoupon.objects.filter(customer_id=customer_id,coupon_type=UserCoupon.TYPE_TRANSFER,status=UserCoupon.UNUSED, template_id=record.template_id)
    if coupons.count() < record.coupon_num:
        info = u"您的券库存不足，请立即购买!"
        return {"code":3, "info":info}
        
    now = datetime.datetime.now()
    CouponTransferRecord.objects.filter(order_no=record.order_no).update(transfer_status=CouponTransferRecord.DELIVERED,modified=now)
    coupons = coupons[0:record.coupon_num]
    for coupon in coupons:
        coupon.customer_id = init_from_customer_id
        coupon.extras.update({"transfer_coupon_pk":record.id})
        coupon.save()
    from flashsale.xiaolumm.tasks.tasks_mama_dailystats import task_calc_xlmm_elite_score
    task_calc_xlmm_elite_score.delay(record.coupon_to_mama_id)  # 计算妈妈积分
    return {"code": 0, "info": u"发放成功"}

    
class CouponTransferRecordViewSet(viewsets.ModelViewSet):
    paginate_by = 10
    page_query_param = 'page'
    paginate_by_param = 'page_size'
    max_paginate_by = 100

    queryset = CouponTransferRecord.objects.all()
    serializer_class = CouponTransferRecordSerializer

    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)

    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    @list_route(methods=['POST'])
    def start_transfer(self, request, *args, **kwargs):
        content = request.data
        
        coupon_num = content.get("coupon_num") or None
        product_id = content.get("product_id")
        if not (coupon_num and coupon_num.isdigit() and product_id and product_id.isdigit()):
            res = Response({"code": 1, "info": u"coupon_num或product_id错误！"})
            #res["Access-Control-Allow-Origin"] = "*"
            return res

        from shopback.items.models import Product
        from flashsale.pay.models import ModelProduct
        
        product = Product.objects.filter(id=product_id).first()
        model_product = ModelProduct.objects.filter(id=product.model_id).first()
        
        template_id = model_product.extras.get("template_id")
        if not template_id:
            res = Response({"code": 2, "info": u"template_id错误！"})
            #res["Access-Control-Allow-Origin"] = "*"
            return res
            
        res = CouponTransferRecord.init_transfer_record(request.user, coupon_num, template_id, product_id)
        res = Response(res)
        #res["Access-Control-Allow-Origin"] = "*"
        
        return res

    
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
        direct_buy = mama.can_buy_transfer_coupon() #可否直接购买精品券
        direct_buy_link = "http://m.xiaolumeimei.com/mall/buycoupon"
        upgrade_score = mama.get_upgrade_score()
        elite_level = mama.elite_level
        
        res = Response({"mama_id": mama_id, "stock_num": stock_num, "waiting_in_num": waiting_in_num,
                        "waiting_out_num": waiting_out_num, "bought_num": in_num,"is_elite_mama":is_elite_mama,
                        "direct_buy": direct_buy, "direct_buy_link": direct_buy_link, "elite_score": mama.elite_score,
                        "elite_level": elite_level, "upgrade_score": upgrade_score})
        #res["Access-Control-Allow-Origin"] = "*"

        return res

    @detail_route(methods=['POST'])
    def process_coupon(self, request, pk=None, *args, **kwargs):
        if not (pk and pk.isdigit()):
            res = {"code":1, "info": u"请求错误"}
        
        mama = get_charged_mama(request.user)
        mama_id = mama.id

        record = CouponTransferRecord.objects.filter(id=pk).first()
        res = {"code": 1, "info": u"无记录审核或不能审核"}
        
        if record and record.can_process(mama_id):
            stock_num = CouponTransferRecord.get_coupon_stock_num(mama_id, record.template_id)
            if stock_num >= record.coupon_num:
                customer = Customer.objects.filter(unionid=mama.unionid).first()
                init_from_mama = XiaoluMama.objects.filter(id=record.init_from_mama_id).first()
                init_from_customer = Customer.objects.filter(unionid=init_from_mama.unionid,status=Customer.NORMAL).first()
                res = process_transfer_coupon(customer.id, init_from_customer.id, record)
            else:
                record.transfer_status=CouponTransferRecord.PROCESSED
                record.save(update_fields=['transfer_status'])
                res = CouponTransferRecord.gen_transfer_record(request.user, record)
        
        res = Response(res)
        return res

    @detail_route(methods=['POST'])
    def cancel_coupon(self, request, pk=None, *args, **kwargs):
        if not (pk and pk.isdigit()):
            res = {"code":1, "info": u"请求错误"}
            
        mama = get_charged_mama(request.user)
        mama_id = mama.id
        
        record = CouponTransferRecord.objects.filter(id=pk).first()
        info = u"无取消记录或不能取消"
        if record and record.can_cancel(mama_id):
            record.transfer_status=CouponTransferRecord.CANCELED
            record.save(update_fields=['transfer_status'])
            info = u"取消成功"
        res = Response({"code": 0, "info": info})
        #res["Access-Control-Allow-Origin"] = "*"
        return res

    
    @detail_route(methods=['POST'])
    def transfer_coupon(self, request, pk=None, *args, **kwargs):
        if not (pk and pk.isdigit()):
            res = {"code":1, "info": u"请求错误"}

        customer = Customer.objects.normal_customer.filter(user=request.user).first()
        mama = customer.get_charged_mama()
        mama_id = mama.id

        info = u"无取消记录或不能取消"
        record = CouponTransferRecord.objects.filter(id=pk).first()
        init_from_mama = XiaoluMama.objects.filter(id=record.init_from_mama_id).first()
        init_from_customer = Customer.objects.filter(unionid=init_from_mama.unionid,status=Customer.NORMAL).first()
        stock_num = CouponTransferRecord.get_coupon_stock_num(mama_id, record.template_id)
        if stock_num < record.coupon_num:
            info = u"您的精品券库存不足，请立即购买!"
            return Response({"code":2, "info":info})

        if record and record.can_process(mama_id) and mama.can_buy_transfer_coupon():
            coupons = UserCoupon.objects.filter(customer_id=customer.id,coupon_type=UserCoupon.TYPE_TRANSFER,status=UserCoupon.UNUSED, template_id=record.template_id)
            if coupons.count() < record.coupon_num:
                info = u"您的券库存不足，请立即购买!"
                return Response({"code":3, "info":info})
            now = datetime.datetime.now()
            CouponTransferRecord.objects.filter(order_no=record.order_no).update(transfer_status=CouponTransferRecord.DELIVERED,modified=now)
            coupons = coupons[0:record.coupon_num]
            for coupon in coupons:
                coupon.customer_id = init_from_customer.id
                coupon.extras.update({"transfer_coupon_pk":pk})
                coupon.save()
            info = u"发放成功"

            from flashsale.xiaolumm.tasks.tasks_mama_dailystats import task_calc_xlmm_elite_score
            task_calc_xlmm_elite_score.delay(record.coupon_to_mama_id)  # 计算妈妈积分
        res = Response({"code": 0, "info": info})
        #res["Access-Control-Allow-Origin"] = "*"
        return res
    
    @list_route(methods=['GET'])
    def list_out_coupons(self, request, *args, **kwargs):
        content = request.GET
        transfer_status = content.get("transfer_status") or None
        status = CouponTransferRecord.EFFECT
        
        mama = get_charged_mama(request.user)
        mama_id = mama.id
        coupons = self.queryset.filter(coupon_from_mama_id=mama_id,status=status).order_by('-created')
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
        #res["Access-Control-Allow-Origin"] = "*"
        return res

    @list_route(methods=['GET'])
    def list_in_coupons(self, request, *args, **kwargs):
        content = request.GET
        transfer_status = content.get("transfer_status") or None
        status = CouponTransferRecord.EFFECT
        
        mama = get_charged_mama(request.user)
        mama_id = mama.id
        coupons = self.queryset.filter(coupon_to_mama_id=mama_id,status=status).order_by('-created')
        if transfer_status:
            coupons = coupons.filter(transfer_status=transfer_status.strip())

        coupons = self.paginate_queryset(coupons)
        serializer = CouponTransferRecordSerializer(coupons, many=True)
        res = self.get_paginated_response(serializer.data)
        #res["Access-Control-Allow-Origin"] = "*"
        return res

    @list_route(methods=['GET'])
    def list_mama_left_coupons(self, request, *args, **kwargs):
        content = request.GET

        mama = get_charged_mama(request.user)
        mama_id = mama.id

        from django.db.models import Q
        coupons = CouponTransferRecord.objects.filter(Q(transfer_type=CouponTransferRecord.OUT_TRANSFER) | Q(transfer_type=CouponTransferRecord.IN_BUY_COUPON),
                                       coupon_to_mama_id=mama_id, transfer_status=CouponTransferRecord.DELIVERED).order_by('-created')

        left_coupons = {"code": 0, "info": "成功", "results": []}
        from django.db.models import Sum
        for one_coupon in coupons:
            has_calc = False
            for one_left_coupon in left_coupons.results:
                if one_left_coupon["template_id"] == one_coupon.template_id:
                    has_calc = True
                    break
            if has_calc:
                break

            res = CouponTransferRecord.objects.filter(template_id=one_coupon.template_id, coupon_from_mama_id=mama_id, transfer_status=CouponTransferRecord.DELIVERED).aggregate(
                n=Sum('coupon_num'))
            out_num = res['n'] or 0

            res = CouponTransferRecord.objects.filter(template_id=one_coupon.template_id, coupon_to_mama_id=mama_id, transfer_status=CouponTransferRecord.DELIVERED).aggregate(
                n=Sum('coupon_num'))
            in_num = res['n'] or 0

            stock_num = in_num - out_num
            #one_coupon.coupon_num = stock_num
            if stock_num > 0:
                left_coupons["results"].append({"product_img": one_coupon.product_img, "coupon_num": stock_num, "template_id": one_coupon.template_id,})
        res = Response(left_coupons)
        return res
