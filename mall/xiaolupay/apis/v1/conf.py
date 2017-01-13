# coding: utf8
from __future__ import absolute_import, unicode_literals

class UnionPayConf(object):

    CLIENT_IP = '118.178.116.5'

    TIME_EXPIRED = 7200 # s



PINGPP_CREDENTIAL_TPL = {
    "alipay_wap": {
    },
    "alipay": {
        "orderInfo": "service=\"mobile.securitypay.pay\"&_input_charset=\"utf-8\"&notify_url=\"https%3A%2F%2Fnotify.pingxx.com%2Fnotify%2Fcharges%2Fch_9OGWD8eH0K4OWbjXn5TizT0G\"&partner=\"2088911223385116\"&out_trade_no=\"xd161124583703e203039\"&subject=\"小鹿美美平台交易\"&body=\"用户订单金额[1, 514978, 139.90]\"&total_fee=\"139.90\"&payment_type=\"1\"&seller_id=\"2088911223385116\"&it_b_pay=\"2016-11-26 10:15:49\"&sign=\"V%2FUbygHIduidH2yu%2FmRbmoqc1giI82Xk82lTHt1KSD5KJH2ty9LOpdZ6v8awZWWrgAfJdRPjLqLOQ1N40YpKv7eLs3KIza4A%2FfVizVso4S6q4WlXHR79j%2FCVbe57pLyQ9rX2Uxs0gPlYhbeFyHANIRThKS48hfgxtt8QBDUssI0%3D\"&sign_type=\"RSA\""
    },
    "wx": {
        "packageValue": "Sign=WXPay",
        "timeStamp": 1480041732,
        "sign": "B276E4FF8B63C7FE9F2E5FE5B0DE1DE6",
        "partnerId": "1268398601",
        "appId": "wx25fcb32689872499",
        "prepayId": "wx201611251042121d2d60876b0135790716",
        "nonceStr": "511c1f93fe774740d58ef9d7897c511b"
    },
    "weapp": {
        "package": "prepay_id=wx201611251043317b2dafe4170529308336",
        "timeStamp": "1480041811",
        "signType": "MD5",
        "paySign": "A0BC39734A54DC333EE8660A5A784A62",
        "appId": "wx3f91056a2928ad2d",
        "nonceStr": "b6480fd5b19fbe8495e58b85b7f79d03"
    },
    "wx_pub": {
        "package": "prepay_id=wx201611251043317b2dafe4170529308336",
        "timeStamp": "1480041811",
        "signType": "MD5",
        "paySign": "A0BC39734A54DC333EE8660A5A784A62",
        "appId": "wx3f91056a2928ad2d",
        "nonceStr": "b6480fd5b19fbe8495e58b85b7f79d03"
    }
}

PINGPP_CHARGE_TPL = {
    "order_no": "", # do
    "extra": {}, # do
    "app": "app_LOOajDn9u9WDjfHa",
    "livemode": True,
    "currency": "cny",
    "time_settle": None,
    "time_expire": 0, # do
    "id": "",
    "subject": "", # do
    "failure_msg": None,
    "channel": "", # do
    "metadata": {
      "color": "red"
    },
    "body": "", #do
    "credential": {   # do
      "object": "credential"
    },
    "client_ip": "", #do
    "description": None,
    "amount_refunded": 0,
    "refunded": False,
    "object": "charge",
    "paid": False,
    "amount_settle": 0, #do
    "time_paid": None,
    "failure_code": None,
    "refunds": None,
    "created": None,  # do
    "transaction_no": None,
    "amount": 0 # do
}