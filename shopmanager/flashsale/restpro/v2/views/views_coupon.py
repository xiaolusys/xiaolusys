# coding=utf-8
import datetime

from rest_framework import viewsets
from rest_framework import authentication
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.decorators import list_route, detail_route

from flashsale.xiaolumm.models import ReferalRelationship, XiaoluMama

from flashsale.restpro import permissions as perms

from flashsale.coupon.models import CouponTransferRecord
from flashsale.pay.models import Customer
from flashsale.restpro.v2.serializers import CouponTransferRecordSerializer

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


class CouponTransferRecordViewSet(viewsets.ModelViewSet):
    queryset = CouponTransferRecord.objects.all()
    serializer_class = CouponTransferRecordSerializer
    #authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    #permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)

    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    @list_route(methods=['POST'])
    def start_transfer(self, request, *args, **kwargs):
        content = request.POST
        
        coupon_num = content.get("coupon_num") or 0
        if coupon_num <= 0:
            res = Response({"code": 1, "info": u"coupon_num必须大于0"})
            res["Access-Control-Allow-Origin"] = "*"
            return res

        to_customer = Customer.objects.normal_customer.filter(user=request.user).first()
        to_mama = to_customer.get_charged_mama()

        if to_mama.can_buy_transfer_coupon():
            res =  Response({"code":2, "info": u"无需申请，请直接支付购券!"})
            res["Access-Control-Allow-Origin"] = "*"
            return res
        
        to_mama_nick = to_customer.nick
        to_mama_thumbnail = to_customer.thumbnail

        coupon_to_mama_id = to_mama.id

        coupon_from_mama_id = get_referal_from_mama_id(coupon_to_mama_id)
        from_mama = XiaoluMama.objects.filter(id=coupon_from_mama_id).first()
        from_customer = Customer.objects.filter(unionid=from_mama.unionid).first()
        from_mama_thumbnail = from_customer.thumbnail
        from_mama_nick = from_customer.nick
        
        transfer_type = CouponTransferRecord.OUT_TRANSFER
        date_field = datetime.date.today()
        template_id = CouponTransferRecord.TEMPLATE_ID
        
        uni_key = CouponTransferRecord.gen_unikey(coupon_from_mama_id, coupon_to_mama_id, template_id, date_field)
        if not uni_key:
            res = Response({"code": 2, "info": u"记录已生成或申请已达当日上限！"})
            res["Access-Control-Allow-Origin"] = "*"
            return res

        coupon = CouponTransferRecord(coupon_from_mama_id=coupon_from_mama_id,from_mama_thumbnail=from_mama_thumbnail,
                                      from_mama_nick=from_mama_nick,coupon_to_mama_id=coupon_to_mama_id,
                                      to_mama_thumbnail=to_mama_thumbnail,to_mama_nick=to_mama_nick,coupon_num=coupon_num,
                                      transfer_type=transfer_type,uni_key=uni_key, date_field=date_field)
        coupon.save()
        res = Response({"code": 0, "info": u"提交成功!"})
        res["Access-Control-Allow-Origin"] = "*"
        
        return res
    
    

    def start_return_coupon(self, request, *args, **kwargs):
        pass

    def update_coupon(self, request, *args, **kwargs):
        pass
        
    @list_route(methods=['GET'])
    def profile(self, request, *args, **kwargs):
        mama = get_charged_mama(request.user)

        mama_id = mama.id
        stock_num, in_num, out_num = CouponTransferRecord.get_stock_num(mama_id)
        waiting_in_num = CouponTransferRecord.get_waiting_in_num(mama_id)
        waiting_out_num = CouponTransferRecord.get_waiting_out_num(mama_id)
        
        #direct_buy = mama.can_buy_transfer_coupon() #可否直接购买精品券
        direct_buy = False
        direct_buy_link = "http://m.xiaolumeimei.com"
        
        res = Response({"mama_id": mama_id, "stock_num": stock_num, "waiting_in_num": waiting_in_num,
                        "waiting_out_num": waiting_out_num, "bought_num": in_num,
                        "direct_buy": direct_buy, "direct_buy_link": direct_buy_link})
        res["Access-Control-Allow-Origin"] = "*"

        return res

    @detail_route(methods=['POST'])
    def process_coupon(self, request, *args, **kwargs):
        record = CouponTransferRecord.objects.filter(id=pk).first()
        info = u"no update"
        if record and record.transfer_status == CouponTransferRecord.PENDING:
            record.transfer_status=CouponTransferRecord.PROCESSED
            record.save(update_fields=['transfer_status'])
            info = u"update succeed"
        res = Response({"code": 0, "info": info})
        res["Access-Control-Allow-Origin"] = "*"
        return res
            
    @list_route(methods=['GET'])
    def list_out_coupons(self, request, *args, **kwargs):
        content = request.GET
        transfer_status = content.get("transfer_status") or None
        status = CouponTransferRecord.EFFECT
        
        mama = get_charged_mama(request.user)
        mama_id = mama.id
        coupons = self.queryset.filter(coupon_from_mama_id=mama_id,status=status)
        if transfer_status:
            coupons = coupons.filter(transfer_status=transfer_status.strip())
            
        serializer = CouponTransferRecordSerializer(coupons, many=True)
        res = Response(serializer.data)
        res["Access-Control-Allow-Origin"] = "*"
        
        return res

    @list_route(methods=['GET'])
    def list_in_coupons(self, request, *args, **kwargs):
        content = request.GET
        transfer_status = content.get("transfer_status") or None
        status = CouponTransferRecord.EFFECT
        
        mama = get_charged_mama(request.user)
        mama_id = mama.id
        coupons = self.queryset.filter(coupon_to_mama_id=mama_id,status=status)
        if transfer_status:
            coupons = coupons.filter(transfer_status=transfer_status.strip())

        serializer = CouponTransferRecordSerializer(coupons, many=True)
        res = Response(serializer.data)
        res["Access-Control-Allow-Origin"] = "*"
        return res
