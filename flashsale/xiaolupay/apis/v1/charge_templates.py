# coding: utf8
from __future__ import absolute_import, unicode_literals

wx = {
    "order_no": "xd161126583703e203023",
    "extra": {},
    "app": "app_LOOajDn9u9WDjfHa",
    "livemode": True,
    "currency": "cny",
    "time_settle": None,
    "time_expire": 1480142679,
    "id": "ch_v5iPK44qDKiPvLWzD4Wrbrb5",
    "subject": "小鹿美美平台交易",
    "failure_msg": None,
    "channel": "wx",
    "metadata": {
      "color": "red"
    },
    "body": "用户订单金额[1, 516401, 139.90]",
    "credential": {
      "object": "credential",
      "wx": {
        "packageValue": "Sign=WXPay",
        "timeStamp": 1480135479,
        "sign": "ABEA30EC9A24E83CD63096B823C90AA1",
        "partnerId": "1268398601",
        "appId": "wx25fcb32689872499",
        "prepayId": "wx201611261244399a1a99b4400809372340",
        "nonceStr": "d3be5ce42085d2de7ac78e6462aac60d"
      }
    },
    "client_ip": "180.97.163.149",
    "description": None,
    "amount_refunded": 0,
    "refunded": False,
    "object": "charge",
    "paid": False,
    "amount_settle": 13990,
    "time_paid": None,
    "failure_code": None,
    "refunds": {
      "url": "/v1/charges/ch_v5iPK44qDKiPvLWzD4Wrbrb5/refunds",
      "has_more": False,
      "object": "list",
      "data": []
    },
    "created": 1480135479,
    "transaction_no": None,
    "amount": 13990
}

wx_pub = {
    "order_no": "xd161126583703e203024",
    "extra": {
      "open_id": "our5huIOSuFF5FdojFMFNP5HNOmA"
    },
    "app": "app_LOOajDn9u9WDjfHa",
    "livemode": True,
    "currency": "cny",
    "time_settle": None,
    "time_expire": 1480142880,
    "id": "ch_DC4iPCGuDuPSvfHe5OOmzrz5",
    "subject": "小鹿美美平台交易",
    "failure_msg": None,
    "channel": "wx_pub",
    "metadata": {
      "color": "red"
    },
    "body": "用户订单金额[1, 516406, 139.90]",
    "credential": {
      "object": "credential",
      "wx_pub": {
        "package": "prepay_id=wx20161126124800898a424f630776089317",
        "timeStamp": "1480135680",
        "signType": "MD5",
        "paySign": "8570C4E889AD24B08CEEA8362E1B09C1",
        "appId": "wx3f91056a2928ad2d",
        "nonceStr": "9f6f29bf382ed38f64d7966a07258f4e"
      }
    },
    "client_ip": "180.97.163.149",
    "description": None,
    "amount_refunded": 0,
    "refunded": False,
    "object": "charge",
    "paid": False,
    "amount_settle": 13906,
    "time_paid": None,
    "failure_code": None,
    "refunds": {
      "url": "/v1/charges/ch_DC4iPCGuDuPSvfHe5OOmzrz5/refunds",
      "has_more": False,
      "object": "list",
      "data": []
    },
    "created": 1480135680,
    "transaction_no": None,
    "amount": 13990
  }

alipay = {
    "order_no": "xd161126583703e203026",
    "extra": {},
    "app": "app_LOOajDn9u9WDjfHa",
    "livemode": True,
    "currency": "cny",
    "time_settle": None,
    "time_expire": 1480222147,
    "id": "ch_Sa5WrHPebTy1GOSqnTevDCOG",
    "subject": "小鹿美美平台交易",
    "failure_msg": None,
    "channel": "alipay",
    "metadata": {
      "color": "red"
    },
    "body": "用户订单金额[1, 516410, 139.90]",
    "credential": {
      "alipay": {
        "orderInfo": "service=\"mobile.securitypay.pay\"&_input_charset=\"utf-8\"&notify_url=\"https%3A%2F%2Fnotify.pingxx.com%2Fnotify%2Fcharges%2Fch_Sa5WrHPebTy1GOSqnTevDCOG\"&partner=\"2088911223385116\"&out_trade_no=\"xd161126583703e203026\"&subject=\"小鹿美美平台交易\"&body=\"用户订单金额[1, 516410, 139.90]\"&total_fee=\"139.90\"&payment_type=\"1\"&seller_id=\"2088911223385116\"&it_b_pay=\"2016-11-27 12:49:07\"&sign=\"E5hvOu82WWVK7I49La74OBoZ4X4U5oCDLu106SzM%2FkAIz7BXa3Z7mK4dwj1YkgDXPqwhYq3i8TlrkX8FzB3aUfzclGHbihrsc8102G1yCWNJ7uB%2FfDnCRWUNzyKYUS5PBO%2B0FDx4JqBkKp2TUZlhSSTyGXNR0ByEabJa5pHJ73Y%3D\"&sign_type=\"RSA\""
      },
      "object": "credential"
    },
    "client_ip": "180.97.163.149",
    "description": None,
    "amount_refunded": 0,
    "refunded": False,
    "object": "charge",
    "paid": False,
    "amount_settle": 13990,
    "time_paid": None,
    "failure_code": None,
    "refunds": {
      "url": "/v1/charges/ch_Sa5WrHPebTy1GOSqnTevDCOG/refunds",
      "has_more": False,
      "object": "list",
      "data": []
    },
    "created": 1480135747,
    "transaction_no": None,
    "amount": 13990
  }

alipay_wap = {
    "order_no": "xd161126583703e203027",
    "extra": {
      "cancel_url": "https://m.xiaolumeimei.com/mall/ol.html?type=1",
      "success_url": "https://m.xiaolumeimei.com/mall/order/success/516413/xd161126583703e203027"
    },
    "app": "app_LOOajDn9u9WDjfHa",
    "livemode": True,
    "currency": "cny",
    "time_settle": None,
    "time_expire": 1480222195,
    "id": "ch_X9SyHGeDSO0Kib9ybPL4mTKG",
    "subject": "小鹿美美平台交易",
    "failure_msg": None,
    "channel": "alipay_wap",
    "metadata": {
      "color": "red"
    },
    "body": "用户订单金额[1, 516413, 139.90]",
    "credential": {
      "alipay_wap": {
        "service": "alipay.wap.auth.authAndExecute",
        "format": "xml",
        "v": "2.0",
        "_input_charset": "utf-8",
        "req_data": "<auth_and_execute_req><request_token>20161126cf9490277a970e2337756290757a8205</request_token></auth_and_execute_req>",
        "sec_id": "0001",
        "partner": "2088911223385116",
        "sign": "dBM76dr5RXig7XfcyGgzUQ2ww7M4U0HK5sU0HKLtpkVtpiZC4fx+8ajJLZHY0Tq6V+H3LrHNh4QLBGxSf6+YJAO8dlPyJt7ffjDJbUM90Aww1CB0BlUzvcd036UWVVOI/eRUNds/b5UnlP3URnrcdNKqAGcuRaz9AoXvp+yAi48="
      },
      "object": "credential"
    },
    "client_ip": "180.97.163.149",
    "description": None,
    "amount_refunded": 0,
    "refunded": False,
    "object": "charge",
    "paid": False,
    "amount_settle": 13990,
    "time_paid": None,
    "failure_code": None,
    "refunds": {
      "url": "/v1/charges/ch_X9SyHGeDSO0Kib9ybPL4mTKG/refunds",
      "has_more": False,
      "object": "list",
      "data": []
    },
    "created": 1480135795,
    "transaction_no": None,
    "amount": 13990
  }