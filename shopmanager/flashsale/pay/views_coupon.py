# coding=utf-8
from .models_coupon_new import UserCoupon
from django.http import HttpResponse


def release_sale_refund_coupon(request):
    # 调用类方法　生成邮费优惠券 并且退货原因是因为质量问题　才发放
    content = request.REQUEST
    buyer_id = content.get("buyer_id", None)
    trade_id = content.get("trade_id", None)
    if buyer_id and trade_id:
        kwargs = {"buyer_id": buyer_id, "trade_id": trade_id}
        # 查看该用户该订单是否有发过邮费优惠券
        uc = UserCoupon.objects.filter(customer=buyer_id, sale_trade=trade_id)
        if uc.exists():
            return HttpResponse("already")
        else:
            ucr = UserCoupon()
            ucr.release_refund_post_fee(**kwargs)
        return HttpResponse("ok")
    else:
        return HttpResponse("arg_error")