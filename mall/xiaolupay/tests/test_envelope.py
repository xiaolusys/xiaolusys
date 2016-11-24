# encoding=utf8
import os
import sys
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shopmanager.local_settings')
import django
django.setup()
from mall import xiaolupay


if __name__ == '__main__':
    # xiaolupay.RedEnvelope.create(
    print xiaolupay.admin
    print dir(xiaolupay)
    print xiaolupay.apis.v1.envelope.create(
        order_no='testhongbao007',  # 商户订单号
        amount='100',  # 金额，分
        subject='主题',  # 红包主题
        body='祝福你',  # 红包祝福语
        recipient='our5huD8xO6QY-lJc1DTrqRut3us',  # 接受者openid
        remark='备注'  # 备注信息
    )
    # xiaolupay.RedEnvelope.retrieve(envelop_id)

    # from mall.xiaolupay.tasks.tasks_envelope import task_sync_weixin_red_envelope
    # task_sync_weixin_red_envelope(8)
