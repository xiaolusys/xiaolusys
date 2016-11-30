# coding=utf-8
import datetime
from django.db import models
from django.db.models import Sum
from django.db.models.signals import post_save
from flashsale.xiaolumm.models import ReferalRelationship
from core.models import BaseModel


def get_referal_from_mama_id(to_mama_id):
    rr = ReferalRelationship.objects.filter(referal_to_mama_id=to_mama_id).first()
    if rr:
        return rr.referal_from_mama_id
    return None


def get_choice_name(choices, val):
    """
    iterate over choices and find the name for this val
    """
    name = ""
    for entry in choices:
        if entry[0] == val:
            name = entry[1]
    return name


class CouponTransferRecord(BaseModel):
    TEMPLATE_ID = 153
    COUPON_VALUE = 128
    MAX_DAILY_TRANSFER = 60  # 每天两人间最大流通次数:60次

    OUT_CASHOUT = 1  # 退券换钱/out
    OUT_TRANSFER = 2  # 转给下属/out
    OUT_CONSUMED = 3  # 直接买货/out
    IN_BUY_COUPON = 4  # 花钱买券/in
    IN_RETURN_COUPON = 5  # 下属退券/in
    IN_RETURN_GOODS = 6  # 退货退券/in
    IN_GIFT_COUPON = 7  # 系统赠送/in
    OUT_EXCHG_SALEORDER = 8  # 兑换订单/out
    TRANSFER_TYPES = ((OUT_CASHOUT, u'退券换钱'), (OUT_TRANSFER, u'转给下属'), (OUT_CONSUMED, u'直接买货'),
                      (IN_BUY_COUPON, u'花钱买券'), (IN_RETURN_COUPON, u'下属退券'), (IN_RETURN_GOODS, u'退货退券'),
                      (IN_GIFT_COUPON, u'系统赠送'), (OUT_EXCHG_SALEORDER, u'兑换订单'))

    PENDING = 1
    PROCESSED = 2
    DELIVERED = 3
    CANCELED = 4
    TRANSFER_STATUS = ((PENDING, u'待审核'), (PROCESSED, u'待发放'), (DELIVERED, u'已完成'), (CANCELED, u'已取消'),)

    EFFECT = 1
    CANCEL = 2
    STATUS_TYPES = ((EFFECT, u'有效'), (CANCEL, u'无效'), )

    # Note:
    # The design follows the route that a coupon is transfered from an agency (coupon_from_mama_id) to
    # another agency (coupon_to_mama_id).
    #
    coupon_from_mama_id = models.IntegerField(default=0, db_index=True, verbose_name=u'From妈妈ID')
    from_mama_thumbnail = models.CharField(max_length=256, blank=True, verbose_name=u'From妈妈头像')
    from_mama_nick = models.CharField(max_length=64, blank=True, verbose_name=u'From妈妈昵称')

    coupon_to_mama_id = models.IntegerField(default=0, db_index=True, verbose_name=u'To妈妈ID')
    to_mama_thumbnail = models.CharField(max_length=256, blank=True, verbose_name=u'To妈妈头像')
    to_mama_nick = models.CharField(max_length=64, blank=True, verbose_name=u'To妈妈昵称')

    init_from_mama_id = models.IntegerField(default=0, db_index=True, verbose_name=u'终端妈妈ID')
    order_no = models.CharField(max_length=64, db_index=True, verbose_name=u'订购标识ID')

    template_id = models.IntegerField(default=TEMPLATE_ID, db_index=True, verbose_name=u'优惠券模版')
    product_img = models.CharField(max_length=256, blank=True, verbose_name=u'产品图片')

    coupon_value = models.IntegerField(default=0, verbose_name=u'面额')
    coupon_num = models.IntegerField(default=0, verbose_name=u'数量')
    transfer_type = models.IntegerField(default=0, db_index=True, choices=TRANSFER_TYPES, verbose_name=u'流通类型')
    transfer_status = models.IntegerField(default=1, db_index=True, choices=TRANSFER_STATUS, verbose_name=u'流通状态')
    status = models.IntegerField(default=1, db_index=True, choices=STATUS_TYPES, verbose_name=u'状态')
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u'唯一ID')
    date_field = models.DateField(default=datetime.date.today, db_index=True, verbose_name=u'日期')
    elite_level = models.CharField(max_length=16, blank=True, null=True, verbose_name=u'等级')
    elite_score = models.IntegerField(default=0, verbose_name=u"精英汇积分")
    product_id = models.BigIntegerField(default=0, verbose_name=u'商品ID')

    class Meta:
        db_table = "flashsale_coupon_transfer_record"
        app_label = 'coupon'
        verbose_name = u"特卖/精品券流通记录"
        verbose_name_plural = u"特卖/精品券流通记录表"

    @staticmethod
    def gen_unikey_with_order_no(from_mama_id, to_mama_id, order_no):
        return "%s-%s-%s" % (from_mama_id, to_mama_id, order_no)


    @classmethod
    def gen_unikey(cls, from_mama_id, to_mama_id, template_id, date_field, prev_coupon_id=0):
        # from_mama_id + to_mama_id + template_id + date_field + idx
        if prev_coupon_id == 0:
            idx = cls.objects.filter(coupon_from_mama_id=from_mama_id, coupon_to_mama_id=to_mama_id,
                                     template_id=template_id, date_field=date_field,
                                     transfer_status__gte=cls.PROCESSED).count()
            idx = idx + 1

            if idx > cls.MAX_DAILY_TRANSFER:
                return None
            return "%s-%s-%s-%s-%s" % (from_mama_id, to_mama_id, template_id, date_field, idx)

        return "%s-%s-%s-%s" % (from_mama_id, to_mama_id, template_id, prev_coupon_id)

    @classmethod
    def gen_order_no(cls, init_from_mama_id, template_id, date_field):
        idx = cls.objects.filter(init_from_mama_id=init_from_mama_id, template_id=template_id,
                                 date_field=date_field).count()
        idx = idx + 1
        if idx > cls.MAX_DAILY_TRANSFER:
            return None
        return "%s-%s-%s-%s" % (init_from_mama_id, template_id, date_field, idx)

    @classmethod
    def get_stock_num(cls, mama_id):
        res = cls.objects.filter(coupon_from_mama_id=mama_id, transfer_status=cls.DELIVERED).aggregate(
            n=Sum('coupon_num'))
        out_num = res['n'] or 0

        res = cls.objects.filter(coupon_to_mama_id=mama_id, transfer_status=cls.DELIVERED).aggregate(
            n=Sum('coupon_num'))
        in_num = res['n'] or 0

        stock_num = in_num - out_num
        return stock_num, in_num, out_num

    @classmethod
    def get_coupon_stock_num(cls, mama_id, template_id):
        """
        """
        res = cls.objects.filter(coupon_from_mama_id=mama_id, transfer_status=cls.DELIVERED, template_id=template_id).aggregate(
            n=Sum('coupon_num'))
        out_num = res['n'] or 0

        res = cls.objects.filter(coupon_to_mama_id=mama_id, transfer_status=cls.DELIVERED, template_id=template_id).aggregate(
            n=Sum('coupon_num'))
        in_num = res['n'] or 0

        stock_num = in_num - out_num
        return stock_num

    @classmethod
    def get_waiting_in_num(cls, mama_id):
        res = cls.objects.filter(coupon_to_mama_id=mama_id, transfer_status__lte=cls.PROCESSED).aggregate(
            n=Sum('coupon_num'))
        num = res['n'] or 0
        return num

    @classmethod
    def get_waiting_out_num(cls, mama_id):
        res = cls.objects.filter(coupon_from_mama_id=mama_id, transfer_status=cls.PENDING).aggregate(
            n=Sum('coupon_num'))
        num = res['n'] or 0
        return num

    @classmethod
    def create_consume_record(cls, coupon_num, sale_trade, template_id):
        from flashsale.xiaolumm.models import XiaoluMama
        from flashsale.pay.models import Customer
        from flashsale.coupon.models import CouponTemplate

        from_customer_id = sale_trade.buyer_id
        from_customer = Customer.objects.filter(id=from_customer_id).first()
        from_mama = XiaoluMama.objects.filter(openid=from_customer.unionid).first()
        coupon_from_mama_id = from_mama.id
        from_mama_nick = from_customer.nick
        from_mama_thumbnail = from_customer.thumbnail
        init_from_mama_id = from_mama.id

        coupon_to_mama_id = 0
        to_mama_nick = 'SYSTEM'
        to_mama_thumbnail = 'http://7xogkj.com2.z0.glb.qiniucdn.com/222-ohmydeer.png?imageMogr2/thumbnail/60/format/png'

        transfer_type = cls.OUT_CONSUMED
        date_field = datetime.date.today()

        uni_key = sale_trade.tid
        order_no = sale_trade.tid

        coupon = cls.objects.filter(uni_key=uni_key).first()
        if coupon:
            res = {"code": 3, "info": u"记录已存在！"}
            return res

        ct = CouponTemplate.objects.filter(id=template_id).first()
        coupon_value = int(ct.value)
        product_img = ct.extras.get("product_img") or ''

        product_id = 0
        elite_score = 0
        sale_orders = sale_trade.normal_orders
        if sale_orders:
            product_id = sale_orders[0].item_id
            from shopback.items.models import Product
            product = Product.objects.filter(id=product_id).first()
            elite_score = product.elite_score * (int(coupon_num))

        transfer_status = cls.DELIVERED
        coupon = cls(coupon_from_mama_id=coupon_from_mama_id, from_mama_thumbnail=from_mama_thumbnail,
                     from_mama_nick=from_mama_nick, coupon_to_mama_id=coupon_to_mama_id,
                     to_mama_thumbnail=to_mama_thumbnail, to_mama_nick=to_mama_nick,coupon_value=coupon_value,
                     init_from_mama_id=init_from_mama_id, order_no=order_no, template_id=template_id,
                     product_img=product_img, coupon_num=coupon_num, transfer_type=transfer_type, product_id=product_id, elite_score=elite_score,
                     uni_key=uni_key, date_field=date_field, transfer_status=transfer_status)
        coupon.save()
        res = {"code": 0, "info": u"成功!"}
        return res

    @classmethod
    def init_transfer_record(cls, request_user, coupon_num, template_id, product_id):
        from flashsale.xiaolumm.models import XiaoluMama
        from flashsale.pay.models import Customer
        from flashsale.coupon.models import CouponTemplate

        to_customer = Customer.objects.normal_customer.filter(user=request_user).first()
        to_mama = to_customer.get_charged_mama()

        if to_mama.can_buy_transfer_coupon():
            res = {"code": 2, "info": u"无需申请，请直接支付购券!"}
            return res

        elite_level = to_mama.elite_level
        to_mama_nick = to_customer.nick
        to_mama_thumbnail = to_customer.thumbnail

        coupon_to_mama_id = to_mama.id
        init_from_mama_id = to_mama.id

        coupon_from_mama_id = get_referal_from_mama_id(coupon_to_mama_id)
        from_mama = XiaoluMama.objects.filter(id=coupon_from_mama_id).first()
        from_customer = Customer.objects.filter(unionid=from_mama.unionid).first()
        from_mama_thumbnail = from_customer.thumbnail
        from_mama_nick = from_customer.nick

        transfer_type = CouponTransferRecord.OUT_TRANSFER
        date_field = datetime.date.today()

        uni_key = CouponTransferRecord.gen_unikey(coupon_from_mama_id, coupon_to_mama_id, template_id, date_field)
        order_no = CouponTransferRecord.gen_order_no(init_from_mama_id, template_id, date_field)

        ct = CouponTemplate.objects.filter(id=template_id).first()
        coupon_value = int(ct.value)
        product_img = ct.extras.get("product_img") or ''

        from shopback.items.models import Product
        product = Product.objects.filter(id=product_id).first()
        elite_score = product.elite_score * (int(coupon_num))

        if not uni_key:
            res = {"code": 2, "info": u"记录已生成或申请已达当日上限！"}
            return res

        coupon = CouponTransferRecord.objects.filter(uni_key=uni_key).first()
        if coupon:
            res = {"code": 3, "info": u"记录已存在！"}
            return res
        coupon = CouponTransferRecord(coupon_from_mama_id=coupon_from_mama_id, from_mama_thumbnail=from_mama_thumbnail,
                                      from_mama_nick=from_mama_nick, coupon_to_mama_id=coupon_to_mama_id,
                                      to_mama_thumbnail=to_mama_thumbnail, to_mama_nick=to_mama_nick,coupon_value=coupon_value,
                                      init_from_mama_id=init_from_mama_id, order_no=order_no, template_id=template_id,
                                      product_img=product_img, coupon_num=coupon_num, elite_level=elite_level, product_id=product_id, elite_score=elite_score,
                                      transfer_type=transfer_type, uni_key=uni_key, date_field=date_field)
        coupon.save()

        from flashsale.xiaolumm.tasks.tasks_mama_dailystats import task_calc_xlmm_elite_score
        task_calc_xlmm_elite_score.delay(coupon_to_mama_id)  # 计算妈妈积分

        res = {"code": 0, "info": u"成功!"}
        return res

    @classmethod
    def gen_transfer_record(cls, request_user, reference_record):
        from flashsale.xiaolumm.models import XiaoluMama
        from flashsale.pay.models import Customer
        from flashsale.coupon.models import CouponTemplate

        to_customer = Customer.objects.normal_customer.filter(user=request_user).first()
        to_mama = to_customer.get_charged_mama()

        if to_mama.can_buy_transfer_coupon():
            res = {"code": 2, "info": u"无需申请，请直接支付购券!"}
            return res

        elite_level = to_mama.elite_level
        to_mama_nick = to_customer.nick
        to_mama_thumbnail = to_customer.thumbnail

        coupon_to_mama_id = to_mama.id
        init_from_mama_id = reference_record.init_from_mama_id

        coupon_from_mama_id = get_referal_from_mama_id(coupon_to_mama_id)
        from_mama = XiaoluMama.objects.filter(id=coupon_from_mama_id).first()
        from_customer = Customer.objects.filter(unionid=from_mama.unionid).first()
        from_mama_thumbnail = from_customer.thumbnail
        from_mama_nick = from_customer.nick

        transfer_type = CouponTransferRecord.OUT_TRANSFER
        date_field = datetime.date.today()

        coupon_num = reference_record.coupon_num
        order_no = reference_record.order_no
        uni_key = CouponTransferRecord.gen_unikey_with_order_no(coupon_from_mama_id, coupon_to_mama_id, order_no)
        template_id = reference_record.template_id

        product_img = reference_record.product_img
        coupon_value = reference_record.coupon_value
        product_id = reference_record.product_id
        elite_score = reference_record.elite_score

        if not uni_key:
            res = {"code": 2, "info": u"记录已生成或申请已达当日上限！"}
            return res

        coupon = CouponTransferRecord.objects.filter(uni_key=uni_key).first()
        if coupon:
            res = {"code": 3, "info": u"记录已存在！"}
            return res

        coupon = CouponTransferRecord(coupon_from_mama_id=coupon_from_mama_id, from_mama_thumbnail=from_mama_thumbnail,
                                      from_mama_nick=from_mama_nick, coupon_to_mama_id=coupon_to_mama_id,
                                      to_mama_thumbnail=to_mama_thumbnail, to_mama_nick=to_mama_nick,coupon_value=coupon_value,
                                      init_from_mama_id=init_from_mama_id, order_no=order_no, template_id=template_id,
                                      product_img=product_img, coupon_num=coupon_num, elite_level=elite_level, product_id=product_id, elite_score=elite_score,
                                      transfer_type=transfer_type, uni_key=uni_key, date_field=date_field)
        coupon.save()

        from flashsale.xiaolumm.tasks.tasks_mama_dailystats import task_calc_xlmm_elite_score
        task_calc_xlmm_elite_score.delay(coupon_to_mama_id)  # 计算妈妈积分

        res = {"code": 0, "info": u"成功!"}
        return res

    @classmethod
    def gen_return_record(cls, customer, coupon_num, template_id, trade_tid):
        from flashsale.coupon.models import CouponTemplate
        
        coupon_from_mama_id = 0
        from_mama_thumbnail = 'http://7xogkj.com2.z0.glb.qiniucdn.com/222-ohmydeer.png?imageMogr2/thumbnail/60/format/png'
        from_mama_nick = 'SYSTEM'
        
        coupon_to_mama_id = customer.mama_id
        to_mama_thumbnail = customer.thumbnail
        to_mama_nick = customer.nick
        init_from_mama_id = coupon_to_mama_id
        order_no = trade_tid


        transfer_type = CouponTransferRecord.IN_RETURN_GOODS
        date_field = datetime.date.today()
        transfer_status = CouponTransferRecord.DELIVERED
        uni_key = "%s-%s-%s" % (coupon_to_mama_id, transfer_type, trade_tid) # every trade, only return once.

        template = CouponTemplate.objects.get(id=template_id)
        coupon_value = int(template.value)
        product_img = template.extras.get("product_img") or ''

        product_id = 0
        elite_score = 0
        from flashsale.pay.models.trade import SaleOrder, SaleTrade
        sale_trade = SaleTrade.objects.filter(tid=trade_tid).first()
        sale_orders = sale_trade.sale_orders.all()
        if sale_orders:
            product_id = sale_orders[0].item_id
            from shopback.items.models import Product
            product = Product.objects.filter(id=product_id).first()
            elite_score = product.elite_score * (int(coupon_num))
    
        coupon = CouponTransferRecord(coupon_from_mama_id=coupon_from_mama_id, from_mama_thumbnail=from_mama_thumbnail,
                                      from_mama_nick=from_mama_nick, coupon_to_mama_id=coupon_to_mama_id,
                                      to_mama_thumbnail=to_mama_thumbnail, to_mama_nick=to_mama_nick,coupon_value=coupon_value,
                                      init_from_mama_id=init_from_mama_id, order_no=order_no, template_id=template_id,
                                      product_img=product_img, coupon_num=coupon_num, transfer_type=transfer_type, product_id=product_id, elite_score=elite_score,
                                      uni_key=uni_key, date_field=date_field, transfer_status=transfer_status)
        coupon.save()

    @classmethod
    def create_exchg_order_record(cls, request_user, coupon_num, sale_order, template_id):
        from flashsale.xiaolumm.models import XiaoluMama
        from flashsale.pay.models import Customer
        from flashsale.coupon.models import CouponTemplate

        from_customer = Customer.objects.normal_customer.filter(user=request_user).first()
        from_mama = from_customer.get_charged_mama()

        from_customer_id = from_customer.id
        coupon_from_mama_id = from_mama.id
        from_mama_nick = from_customer.nick
        from_mama_thumbnail = from_customer.thumbnail
        init_from_mama_id = from_mama.id

        coupon_to_mama_id = 0
        to_mama_nick = 'SYSTEM'
        to_mama_thumbnail = 'http://7xogkj.com2.z0.glb.qiniucdn.com/222-ohmydeer.png?imageMogr2/thumbnail/60/format/png'

        transfer_type = cls.OUT_EXCHG_SALEORDER
        date_field = datetime.date.today()

        uni_key = sale_order.id
        order_no = sale_order.id

        coupon = cls.objects.filter(uni_key=uni_key).first()
        if coupon:
            res = {"code": 3, "info": u"记录已存在！"}
            return res

        ct = CouponTemplate.objects.filter(id=template_id).first()
        coupon_value = int(ct.value)
        product_img = ct.extras.get("product_img") or ''

        product_id = sale_order.item_id
        from shopback.items.models import Product
        product = Product.objects.filter(id=product_id).first()
        elite_score = product.elite_score * (int(coupon_num))

        transfer_status = cls.DELIVERED
        coupon = cls(coupon_from_mama_id=coupon_from_mama_id, from_mama_thumbnail=from_mama_thumbnail,
                     from_mama_nick=from_mama_nick, coupon_to_mama_id=coupon_to_mama_id,
                     to_mama_thumbnail=to_mama_thumbnail, to_mama_nick=to_mama_nick, coupon_value=coupon_value,
                     init_from_mama_id=init_from_mama_id, order_no=order_no, template_id=template_id,
                     product_img=product_img, coupon_num=coupon_num, transfer_type=transfer_type, product_id=product_id,
                     elite_score=elite_score,
                     uni_key=uni_key, date_field=date_field, transfer_status=transfer_status)
        coupon.save()
        res = {"code": 0, "info": u"成功!"}
        return res
        
    
    @property
    def product_model_id(self):
        from flashsale.coupon.models import CouponTemplate
        ct = CouponTemplate.objects.filter(id=self.template_id).first()
        if ct:
            product_model_id = ct.extras.get("product_model_id")
            return product_model_id
        return None
        
    @property
    def month_day(self):
        return self.created.strftime('%m-%d')

    @property
    def hour_minute(self):
        return self.created.strftime('%H:%M')

    @property
    def transfer_status_display(self):
        return get_choice_name(self.TRANSFER_STATUS, self.transfer_status)

    @property
    def is_cancelable(self):
        return (self.transfer_status == self.PENDING) and \
               ((self.init_from_mama_id == self.coupon_to_mama_id and self.transfer_type == self.OUT_TRANSFER) or \
                self.transfer_type == self.IN_RETURN_GOODS)

    @property
    def is_processable(self):
        return (self.transfer_type == self.OUT_TRANSFER or self.transfer_type == self.IN_RETURN_GOODS) and \
               (self.transfer_status == self.PENDING)

    def can_cancel(self, mama_id):
        return (self.transfer_type == self.OUT_TRANSFER and self.transfer_status == self.PENDING and \
                self.init_from_mama_id == mama_id and self.init_from_mama_id == self.coupon_to_mama_id) or \
               (self.transfer_type == self.IN_RETURN_GOODS and self.transfer_status == self.PENDING and \
                self.coupon_from_mama_id == mama_id)

    def can_process(self, mama_id):
        return (self.transfer_type == self.OUT_TRANSFER and self.transfer_status == self.PENDING and \
                self.coupon_from_mama_id == mama_id)


def push_mama_coupon_audit(sender, instance, created, **kwargs):
    from flashsale.xiaolumm.tasks import task_weixin_push_mama_coupon_audit

    if not created or (instance.transfer_status is not instance.PENDING):
        return
    task_weixin_push_mama_coupon_audit.delay(instance)

post_save.connect(push_mama_coupon_audit,
                  sender=CouponTransferRecord, dispatch_uid='post_save_push_mama_coupon_audit')
