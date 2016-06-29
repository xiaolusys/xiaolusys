# coding=utf-8
"""alipay_wap
/mm/callback/?
out_trade_no=T122&request_token=requestToken&
result=success&trade_no=2015041300001000100061825518&
sign=e6hSj2gP%2BlxZeClZXq5AuKbXRyytF3EHN1cMYLdFjf1MnfZjpfkAVCEDFVV7Iektk4TbIHZzWlVFEkT2QXXJhsvcH32RuMijkSOadt1K9gQjJQT%2FlJhhIFpVk95N%2FC4bWBI5s2WHBXxWxrl2BMCVjQ5B%2BihZba9mFprshk%2FO6wc%3D&
sign_type=0001
"""
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
