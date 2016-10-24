# coding=utf-8
import datetime

from rest_framework import viewsets
from rest_framework import authentication
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.decorators import list_route, detail_route

from flashsale.xiaolumm.models import ReferalRelationship

from flashsale.restpro import permissions as perms

from flashsale.coupon.models import CouponTransferRecord
from flashsale.pay.models import Customer
from flashsale.restpro.v2.serializers import CouponTransferRecordSerializer

def get_mama_id(user):
    customer = Customer.objects.normal_customer.filter(user=user).first()
    mama_id = None
    if customer:
        xlmm = customer.get_charged_mama()
        if xlmm:
            mama_id = xlmm.id
    # mama_id = 5 # debug test
    return mama_id


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
    def stock_num(self, request, *args, **kwargs):
        mama_id = get_mama_id(request.user)
        
        stock_num = CouponTransferRecord.get_stock_num(mama_id)
        return Response({"stock_num": stock_num})

    @list_route(methods=['GET'])
    def list_out_coupons(self, request, *args, **kwargs):
        content = request.GET
        transfer_status = content.get("transfer_status") or None
        status = CouponTransferRecord.EFFECT
        
        #mama_id = get_mama_id(request.user)
        mama_id=44
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
        
        #mama_id = get_mama_id(request.user)
        mama_id=1
        coupons = self.queryset.filter(coupon_to_mama_id=mama_id,status=status)
        if transfer_status:
            coupons = coupons.filter(transfer_status=transfer_status.strip())

        serializer = CouponTransferRecordSerializer(coupons, many=True)
        res = Response(serializer.data)
        res["Access-Control-Allow-Origin"] = "*"
        return res
