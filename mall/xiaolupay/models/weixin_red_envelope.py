# encoding=utf8
from datetime import datetime
from django.db import models
from core.models import BaseModel


class WeixinRedEnvelope(BaseModel):

    UNSEND = 'UNSEND'
    SENDING = 'SENDING'
    SENT = 'SENT'
    FAILED = 'FAILED'
    RECEIVED = 'RECEIVED'
    RFUND_ING = 'RFUND_ING'
    REFUND = 'REFUND'

    STATUS_CHOICES = (
        (UNSEND, u'待发放'),
        (SENDING, u'发放中'),
        (SENT, u'已发放待领取'),
        (FAILED, u'发放失败'),
        (RECEIVED, u'已领取'),
        (RFUND_ING, u'退款中'),
        (REFUND, u'已退款'),
    )

    mch_billno = models.CharField(max_length=28, unique=True, verbose_name=u'商户订单号')
    mch_id = models.CharField(max_length=32, verbose_name=u'商户号')
    wxappid = models.CharField(max_length=32, verbose_name=u'公众号appid')
    send_name = models.CharField(max_length=32, verbose_name=u'商户名称')
    openid = models.CharField(max_length=32, db_index=True, verbose_name=u'接收者openid')
    total_amount = models.IntegerField(default=0, verbose_name=u'红包金额(分)')
    total_num = models.IntegerField(default=1, verbose_name=u'红包发放人数')
    wishing = models.CharField(max_length=128, verbose_name=u'红包祝福语')
    client_ip = models.CharField(max_length=15, verbose_name=u'调用接口的IP')
    act_name = models.CharField(max_length=32, verbose_name=u'活动名称')
    remark = models.CharField(max_length=256, blank=True, verbose_name=u'备注')
    send_listid = models.CharField(max_length=32, blank=True, verbose_name=u'红包订单的微信单号')

    return_code = models.CharField(max_length=16, verbose_name=u'返回状态码')
    return_msg = models.CharField(max_length=128, blank=True, verbose_name=u'返回信息')

    result_code = models.CharField(max_length=16, verbose_name=u'业务结果')
    err_code = models.CharField(max_length=32, blank=True, verbose_name=u'错误代码')
    err_code_des = models.CharField(max_length=128, blank=True, verbose_name=u'错误代码描述')

    status = models.CharField(max_length=16, default=UNSEND, choices=STATUS_CHOICES, verbose_name=u'发送状态')

    send_time = models.DateTimeField(null=True, verbose_name=u'红包发送时间')
    refund_time = models.DateTimeField(null=True, verbose_name=u'红包退款时间')
    rcv_time = models.DateTimeField(null=True, verbose_name=u'红包领取时间')

    class Meta:
        db_table = 'xiaolupay_weixin_red_envelope'
        app_label = 'xiaolupay'

    def update_sync_result(self, result):
        """
        根据微信创建红包的接口修改
        """
        self.return_code = result['return_code']
        self.return_msg = result.get('return_msg', '')

        if self.return_code == 'SUCCESS':
            self.result_code = result['result_code']
            self.err_code = result.get('err_code', '')
            self.err_code_des = result.get('err_code_des', '')

            if self.result_code == 'SUCCESS':
                # 红包发送成功
                self.send_listid = result['send_listid']
                self.status = self.SENDING
        self.save()
        return self

    def sync_envelope_info(self, result):
        """
        根据微信查询红包的接口修改
        """
        self.return_code = result['return_code']
        self.return_msg = result.get('return_msg', '')

        if self.return_code == 'SUCCESS':
            self.result_code = result['result_code']
            self.err_code = result.get('err_code', '')
            self.err_code_des = result.get('err_code_des', '')

            if self.result_code == 'SUCCESS':
                # 红包发送成功
                self.status = result['status']
                self.send_time = datetime.strptime(result['send_time'], '%Y-%m-%d %H:%M:%S')
                refund_time = result.get('refund_time', '')
                if refund_time:
                    self.refund_time = datetime.strptime(refund_time, '%Y-%m-%d %H:%M:%S')
                rcv_time = result.get('hblist', {}).get('hbinfo', {}).get('rcv_time', '')
                if rcv_time:
                    self.rcv_time = datetime.strptime(rcv_time, '%Y-%m-%d %H:%M:%S')
        self.save()
        return self

    def set_status_fail(self):
        from flashsale.pay.models.envelope import Envelop

        self.status = WeixinRedEnvelope.FAILED
        self.save()

        item = Envelop.objects.filter(envelop_id=self.mch_billno).first()
        item.handle_envelop(self)
