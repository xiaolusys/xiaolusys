# encoding=utf8
import os
import sys

sys.path.append('/Users/bo/code/xiaolusys')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.local_settings")

import django
django.setup()
from flashsale import xiaolupay
from flashsale.xiaolupay.apis.v1 import transfers
from flashsale.xiaolupay.apis.v1.transfers import WeixinTransfersAPI


if __name__ == '__main__':
    # xiaolupay.RedEnvelope.create(
    # print xiaolupay.admin
    # print dir(xiaolupay)
    # print xiaolupay.apis.v1.envelope.create(
    #     order_no='testhongbao007',  # 商户订单号
    #     amount='100',  # 金额，分
    #     subject='主题',  # 红包主题
    #     body='祝福你',  # 红包祝福语
    #     recipient='our5huD8xO6QY-lJc1DTrqRut3us',  # 接受者openid
    #     remark='备注'  # 备注信息
    # )
    # xiaolupay.RedEnvelope.retrieve(envelop_id)

    # from flashsale.xiaolupay.tasks.tasks_envelope import task_sync_weixin_red_envelope
    # task_sync_weixin_red_envelope(8)


    openid = 'our5huD8xO6QY-lJc1DTrqRut3us'  # bo.zhang
    name = 'kk'
    amount = 100
    desc = '测试转账'
    trade_id = '20170406122'

    transfers.transfer(openid, name, amount, desc, trade_id)

