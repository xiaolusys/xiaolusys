# coding=utf-8

import urllib

WX = 'wx'
ALIPAY = 'alipay'
WX_PUB = 'wx_pub'
ALIPAY_WAP = 'alipay_wap'
UPMP_WAP = 'upmp_wap'
WALLET = 'wallet'
BUDGET = 'budget'

CHANNEL_CHOICES = (
    (BUDGET, u'小鹿钱包'),
    (WALLET, u'妈妈钱包'),
    (WX, u'微信APP'),
    (ALIPAY, u'支付宝APP'),
    (WX_PUB, u'微支付'),
    (ALIPAY_WAP, u'支付宝'),
    (UPMP_WAP, u'银联'),
)

NO_REFUND = 0
REFUND_CLOSED = 1
REFUND_REFUSE_BUYER = 2
REFUND_WAIT_SELLER_AGREE = 3
REFUND_WAIT_RETURN_GOODS = 4
REFUND_CONFIRM_GOODS = 5
REFUND_APPROVE = 6
REFUND_SUCCESS = 7

REFUND_STATUS = (
    (NO_REFUND,'没有退款'),
    (REFUND_WAIT_SELLER_AGREE,'买家已经申请退款'),
    (REFUND_WAIT_RETURN_GOODS,'卖家已经同意退款'),
    (REFUND_CONFIRM_GOODS,'买家已经退货'),
    (REFUND_REFUSE_BUYER,'卖家拒绝退款'),
    (REFUND_APPROVE,'确认退款，等待返款'),
    (REFUND_CLOSED,'退款关闭'),
    (REFUND_SUCCESS,'退款成功'),
)

#订单状态变成已完成天数
ORDER_WAIT_CONFIRM_TO_FINISHED_DAYS = 14
ORDER_SIGNED_TO_FINISHED_DAYS = 7

MALL_LOGIN_URL = '/mall/user/login'

MALL_PAY_SUCCESS_URL = '/mall/order/success/{order_id}/{order_tid}'
#TEAMBUY_SUCCESS_URL = '/mall/order/spell/group/progress/{teambuy_id}/{order_tid}'
TEAMBUY_SUCCESS_URL = '/mall/order/spell/group/{order_tid}'
# MALL_PAY_SUCCESS_URL = '/mall/ol.html?type=2'
MALL_PAY_CANCEL_URL = '/mall/ol.html?type=1'

COUPON_ID_FOR_20160223_AWARD = 22

ENVELOP_BODY = u'一份耕耘，一份收获，谢谢你的努力！'
ENVELOP_CASHOUT_DESC = u"用户编号:{0},提现前:{1}"

IS_USERBUDGET_COULD_CASHOUT = 1  # 等于１的时候允许提现

CHILD_CID_LIST = [12, 13, 14, 15, 16, 17, 23, 25, 26]
FEMALE_CID_LIST = [18, 19, 20, 21, 22, 24, 27]
