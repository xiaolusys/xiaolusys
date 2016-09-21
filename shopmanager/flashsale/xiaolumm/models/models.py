# -*- coding:utf-8 -*-
import datetime
from random import choice

from django.conf import settings
from django.contrib.auth.models import User as DjangoUser
from django.db import models
from django.db.models import Sum
from flashsale.xiaolumm.managers import XiaoluMamaManager

# Create your models here.
from shopback.items.models import Product
from shopapp.weixin.models_sale import WXProductSku
from common.modelutils import update_model_fields
from core.models import BaseModel
from core.fields import JSONCharMyField
from flashsale.clickcount.models import ClickCount
from flashsale.xiaolumm.models.models_rebeta import AgencyOrderRebetaScheme
from flashsale.xiaolumm import ccp_schema
from flashsale.xiaolumm import constants
from flashsale.xiaolumm.models.new_mama_task import NewMamaTask

from django.db.models.signals import post_save, pre_save
from django.db.models import Q
import logging

logger = logging.getLogger('django.request')
ROI_CLICK_START = datetime.date(2015, 8, 25)
ORDER_RATEUP_START = datetime.date(2015, 7, 8)
ORDER_REBETA_START = datetime.datetime(2015, 6, 19)

MM_CLICK_DAY_LIMIT = 1
MM_CLICK_DAY_BASE_COUNT = 10
MM_CLICK_PER_ORDER_PLUS_COUNT = 50


class XiaoluMama(models.Model):
    EFFECT = 'effect'
    FROZEN = 'forzen'
    CANCEL = 'cancel'
    STATUS_CHOICES = (
        (EFFECT, u'正常'),
        (FROZEN, u'已冻结'),
        (CANCEL, u'已注消'),
    )

    NONE = 'none'
    PROFILE = 'profile'
    PAY = 'pay'
    PASS = 'pass'
    PROGRESS_CHOICES = (
        (NONE, u'未申请'),
        (PROFILE, u'填写资料'),
        (PAY, u'支付押金'),
        (PASS, u'申请成功'),
    )

    CHARGED = 'charged'
    UNCHARGE = 'uncharge'

    CHARGE_STATUS_CHOICES = (
        (UNCHARGE, u'待接管'),
        (CHARGED, u'已接管'),
    )

    INNER_LEVEL = 1
    VIP_LEVEL = 2
    A_LEVEL = 3
    VIP2_LEVEL = 12
    VIP4_LEVEL = 14
    VIP6_LEVEL = 16
    VIP8_LEVEL = 18
    AGENCY_LEVEL = (
        (INNER_LEVEL, u"普通"),
        (VIP_LEVEL, "VIP1"),
        (A_LEVEL, u"A类"),
        (VIP2_LEVEL, "VIP2"),
        (VIP4_LEVEL, "VIP4"),
        (VIP6_LEVEL, "VIP6"),
        (VIP8_LEVEL, "VIP8"),
    )
    SCAN  = 3
    TRIAL = 15
    HALF  = 183
    FULL  = 365

    RENEW_TYPE = (
        (SCAN, u'试用3'),
        (TRIAL, u'试用15'),
        (HALF, u'半年'),
        (FULL, u'一年'),
    )
    is_staff = models.BooleanField(default=False, db_index=True, verbose_name=u'特殊账号（公司职员）')
    mobile = models.CharField(max_length=11, db_index=True, blank=False, verbose_name=u"手机")
    openid = models.CharField(max_length=64, blank=False, unique=True, verbose_name=u"UnionID")
    province = models.CharField(max_length=24, blank=True, verbose_name=u"省份")
    city = models.CharField(max_length=24, blank=True, verbose_name=u"城市")
    address = models.CharField(max_length=256, blank=True, verbose_name=u"地址")
    referal_from = models.CharField(max_length=11, db_index=True, blank=True, verbose_name=u"推荐人", help_text=u"妈妈的id")

    qrcode_link = models.CharField(max_length=256, blank=True, verbose_name=u"二维码")
    weikefu = models.CharField(max_length=11, db_index=True, blank=True, verbose_name=u"微客服")
    manager = models.IntegerField(default=0, verbose_name=u"管理员")

    cash = models.IntegerField(default=0, verbose_name=u"可用现金")
    pending = models.IntegerField(default=0, verbose_name=u"冻结佣金")

    hasale = models.BooleanField(default=False, verbose_name=u"有购买")
    hasale_time = models.DateTimeField(null=True, verbose_name=u"有购买时间")
    active = models.BooleanField(default=False, verbose_name=u"已激活", help_text=u'有获得收益')
    active_time = models.DateTimeField(null=True, verbose_name=u"激活时间")

    last_renew_type = models.IntegerField(choices=RENEW_TYPE, default=365, db_index=True, verbose_name=u"最近续费类型")

    agencylevel = models.IntegerField(default=INNER_LEVEL, db_index=True, choices=AGENCY_LEVEL, verbose_name=u"代理类别")
    target_complete = models.FloatField(default=0.0, verbose_name=u"升级指标完成额")
    lowest_uncoushout = models.FloatField(default=0.0, verbose_name=u"最低不可提金额")
    # user_group = models.ForeignKey('weixin.UserGroup', null=True, verbose_name=u"分组")
    user_group_id = models.IntegerField(null=True, verbose_name=u"分组")
    charge_time = models.DateTimeField(default=datetime.datetime.now,
                                       db_index=True, blank=True, null=True, verbose_name=u'接管时间')
    renew_time = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name=u'下次续费时间')

    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    status = models.CharField(max_length=16, blank=True, choices=STATUS_CHOICES,
                              default=EFFECT, verbose_name=u'状态')

    charge_status = models.CharField(max_length=16, blank=True, db_index=True,
                                     choices=CHARGE_STATUS_CHOICES,
                                     default=UNCHARGE, verbose_name=u'接管状态')

    progress = models.CharField(max_length=8, blank=True, db_index=True,
                                choices=PROGRESS_CHOICES,
                                default=NONE, verbose_name=u'申请进度')

    objects = XiaoluMamaManager()

    class Meta:
        db_table = 'xiaolumm_xiaolumama'
        app_label = 'xiaolumm'
        verbose_name = u'小鹿妈妈'
        verbose_name_plural = u'小鹿妈妈列表'

    def __unicode__(self):
        return '%s' % self.id

    def clean(self):
        for field in self._meta.fields:
            if isinstance(field, (models.CharField, models.TextField)):
                setattr(self, field.name, getattr(self, field.name).strip())

    def get_cash_display(self):
        return self.cash / 100.0

    get_cash_display.allow_tags = True
    get_cash_display.admin_order_field = 'cash'
    get_cash_display.short_description = u"可用现金"

    def get_pending_display(self):
        return self.pending / 100.0

    get_pending_display.allow_tags = True
    get_cash_display.admin_order_field = 'pending'
    get_pending_display.short_description = u"冻结佣金"

    @property
    def cash_money(self):
        return self.get_cash_display()

    @property
    def pending_money(self):
        return self.get_pending_display()

    @property
    def user_group(self):
        from shopapp.weixin.models import UserGroup
        if self.user_group_id:
            return UserGroup.objects.get(id=self.user_group_id)

    @property
    def manager_name(self):
        """ 获取小鹿妈妈管理员 """
        try:
            return DjangoUser.objects.get(id=self.manager).username
        except:
            return '%s' % self.manager

    def exam_Passed(self):
        """ 妈妈考试是否通过 """
        return True

    #         from flashsale.mmexam.models import Result
    #         results = Result.objects.filter(daili_user=self.openid)
    #         if results.count() > 0  and results[0].is_Exam_Funished():
    #             return True
    #         return False

    def need_pay_deposite(self):
        """ 是否需要支付押金 """
        return self.progress in ('', self.NONE, self.PROFILE) and self.agencylevel < 2

    def can_send_redenvelop(self):
        """ 是否可以发送订单红包 """
        if not self.charge_time or self.charge_time > datetime.datetime(2015, 8, 25):
            return False
        if self.agencylevel == self.VIP_LEVEL:
            return True
        return False

    def get_Mama_Deposite(self):
        """ 获取妈妈押金金额 """
        agency_levels = AgencyLevel.objects.filter(id=self.agencylevel)
        if agency_levels.count() == 0:
            return 0
        return agency_levels[0].deposit

    def get_Mama_Deposite_Amount(self):
        """ 获取妈妈押金对应账户金额 """
        agency_levels = AgencyLevel.objects.filter(id=self.agencylevel)
        if agency_levels.count() == 0:
            return 0
        return agency_levels[0].cash

    def get_Mama_Thousand_Target_Amount(self):
        """ 获取妈妈千元基准成交额 """
        agency_levels = AgencyLevel.objects.filter(id=self.agencylevel)
        if agency_levels.count() == 0:
            return float('Inf')
        return agency_levels[0].target

    def get_Mama_Thousand_Rate(self):
        """ 获取妈妈千元提成率 """
        agency_levels = AgencyLevel.objects.filter(id=self.agencylevel)
        if agency_levels.count() == 0:
            return float('Inf')
        return agency_levels[0].extra_rate_percent()

    def get_Mama_Agency_Rebeta_Rate(self):
        """ 获取代理妈妈获取子级代理的提成点数 """
        if self.agencylevel > 1:
            return 0.05
        return 0

    def get_Mama_Order_Rebeta_Rate(self):
        """ 获取小鹿妈妈订单提成点数 """
        agency_levels = AgencyLevel.objects.filter(id=self.agencylevel)
        if agency_levels.count() == 0:
            return 0

        agency_level = agency_levels[0]
        return agency_level.get_Rebeta_Rate()

    def get_Mama_Order_Product_Rate(self, product):
        """
                如果特卖商品detail设置代理了返利，
                则返回设置值，否则返回小鹿妈妈统一设置值
        """
        try:
            pdetail = product.details
        except:
            return self.get_Mama_Order_Rebeta_Rate()
        else:
            rate = pdetail.mama_rebeta_rate()
            if rate is None:
                return self.get_Mama_Order_Rebeta_Rate()
            return rate

    def get_Mama_Order_Rebeta_Scheme(self, product):
        """ 获取妈妈佣金返利计划 """
        product_detail = product.detail
        scheme_id = product_detail and product_detail.rebeta_scheme_id or 0
        scheme = AgencyOrderRebetaScheme.get_rebeta_scheme(scheme_id)
        return scheme

    def get_Mama_Order_Rebeta(self, order):
        # 如果订单来自小鹿特卖平台
        if hasattr(order, 'item_id'):
            product_qs = Product.objects.filter(id=order.item_id)
        # 如果订单来自微信小店
        elif hasattr(order, 'product_sku'):
            try:
                wxsku = WXProductSku.objects.get(sku_id=order.product_sku,
                                                 product=order.product_id)
                product_qs = Product.objects.filter(outer_id=wxsku.outer_id)
            except Exception, exc:
                logger.error(exc.message, exc_info=True)
                product_qs = Product.objects.none()
        else:
            product_qs = Product.objects.none()

        product_ins = product_qs.count() > 0 and product_qs[0] or None
        order_payment = 0
        if hasattr(order, 'order_total_price'):
            order_payment = order.order_total_price
        elif hasattr(order, 'payment'):
            order_payment = int(order.payment * 100)

        # 订单是特卖订单明细,则保存订单佣金明细
        if hasattr(order, 'id') and hasattr(order, 'payment'):
            from flashsale.clickrebeta.models import StatisticsShopping, OrderDetailRebeta

            shopping_order, state = StatisticsShopping.objects.get_or_create(
                linkid=self.id,
                wxorderid=order.sale_trade.tid
            )
            order_detail, state = OrderDetailRebeta.objects.get_or_create(
                order=shopping_order,
                detail_id=order.oid
            )
            if state:
                rebeta_scheme = self.get_Mama_Order_Rebeta_Scheme(product_ins)
                rebeta_amount = rebeta_scheme.get_scheme_rebeta(
                    agencylevel=self.agencylevel,
                    payment=order_payment
                )
                order_detail.pay_time = order.pay_time
                order_detail.order_amount = order_payment
                order_detail.scheme_id = rebeta_scheme.id
                order_detail.rebeta_amount = rebeta_amount
                order_detail.save()
            return order_detail.rebeta_amount

        else:
            rebeta_rate = self.get_Mama_Order_Product_Rate(product_ins)
            return rebeta_rate * order_payment

    def get_Mama_Order_Amount(self, order):
        # 如果订单来自小鹿特卖平台
        order_price = 0
        if hasattr(order, 'order_total_price'):
            order_price = order.order_total_price
        elif hasattr(order, 'payment'):
            order_price = int(order.payment * 100)
        return order_price

    def get_Mama_Trade_Rebeta(self, trade):
        """ 获取妈妈交易返利提成 """
        if hasattr(trade, 'pay_time') and trade.pay_time < ORDER_REBETA_START:
            return 0
        if hasattr(trade, 'normal_orders'):
            if hasattr(trade, 'is_wallet_paid') and trade.is_wallet_paid():
                return 0
            rebeta = 0
            for order in trade.normal_orders:
                rebeta += self.get_Mama_Order_Rebeta(order)
            return rebeta
        return self.get_Mama_Order_Rebeta(trade)

    def get_Mama_Trade_Amount(self, trade):
        """ 获取妈妈交易订单金额 """
        if hasattr(trade, 'pay_time') and trade.pay_time < ORDER_REBETA_START:
            return 0
        if hasattr(trade, 'normal_orders'):
            amount = 0
            for order in trade.normal_orders:
                amount += self.get_Mama_Order_Amount(order)
            return amount
        return self.get_Mama_Order_Amount(trade)

    def get_Mama_Click_Price(self, ordernum):
        """ 获取今日小鹿妈妈点击价格 """
        cur_date = datetime.date.today()
        return self.get_Mama_Click_Price_By_Day(ordernum, day_date=cur_date)

    def get_Mama_Click_Price_By_Day(self, ordernum, day_date=None):
        """ 按日期获取小鹿妈妈点击价格
            agency_level = agency_levels[0]
            if not day_date or day_date < ROI_CLICK_START:
                return base_price + agency_level.get_Click_Price(ordernum)
            return 0

            pre_date = day_date - datetime.timedelta(days=1)
            mm_stats = MamaDayStats.objects.filter(xlmm=self.id,day_date=pre_date)
            if mm_stats.count() > 0:
                base_price = mm_stats[0].base_click_price

            return base_price + agency_level.get_Click_Price(ordernum)
        """
        if self.agencylevel < 2:
            return 0

        cc_price = ccp_schema.get_ccp_price(day_date, ordernum)
        if cc_price is not None:
            return cc_price

        return 10

    def get_Mama_Max_Valid_Clickcount(self, ordernum, day_date):
        """ 获取小鹿妈妈最大有效点击数  """
        if self.agencylevel < 2:
            return 0

        cc_count = ccp_schema.get_ccp_count(day_date, ordernum)
        if cc_count is not None:
            return cc_count

        return MM_CLICK_DAY_BASE_COUNT + MM_CLICK_PER_ORDER_PLUS_COUNT * ordernum

    def set_active(self):
        self.active = True
        self.active_time = datetime.datetime.now()
        self.save()

    def set_hasale(self):
        self.hasale = True
        self.hasale_time = datetime.datetime.now()
        self.save()

    def push_carrylog_to_cash(self, clog):

        if self.id != clog.xlmm or clog.status == CarryLog.CONFIRMED:
            raise Exception(u'收支记录状态不可更新')

        if clog.carry_type == CarryLog.CARRY_OUT and self.cash < clog.value:
            return

        try:
            clog = CarryLog.objects.get(id=clog.id, status=CarryLog.PENDING)
        except CarryLog.DoesNotExist:
            raise Exception(u'妈妈收支记录重复确认:%s' % clog.id)

        clog.status = CarryLog.CONFIRMED
        clog.save()

        if clog.carry_type == CarryLog.CARRY_IN:
            self.cash = models.F('cash') + clog.value
            self.pending = models.F('pending') - clog.value
        else:
            self.cash = models.F('cash') - clog.value

        update_model_fields(self, update_fields=['cash', 'pending'])

    def get_base_deposite(self):
        """ 获取妈妈实际押金金额 """
        from flashsale.clickrebeta.models import StatisticsShopping
        shopscount = StatisticsShopping.objects.filter(linkid=self.id).count()
        clickcounts = ClickCount.objects.filter(linkid=self.id)
        click_nums = clickcounts.aggregate(total_count=Sum('valid_num')).get('total_count') or 0
        if (click_nums >= 150 and shopscount >= 1) or shopscount >= 6:
            return self.get_Mama_Deposite()
        return self.get_Mama_Deposite_Amount()

    def is_available_rank(self):
        return self.charge_status == self.CHARGED and self.status in [XiaoluMama.EFFECT, XiaoluMama.FROZEN] \
               and self.progress in [XiaoluMama.PAY, XiaoluMama.PASS]

    def is_available(self):
        return self.charge_status == self.CHARGED and self.status == XiaoluMama.EFFECT \
               and self.progress in [XiaoluMama.PAY, XiaoluMama.PASS]

    def is_chargeable(self):
        return self.charge_status != self.CHARGED

    def chargemama(self):
        """ 接管妈妈 """
        update_fields = []
        self.charge_time = datetime.datetime.now()  # 接管时间
        update_fields.append("charge_time")
        if self.progress != XiaoluMama.PAY:
            update_fields.append('progress')
            self.progress = XiaoluMama.PAY
        if self.charge_status != XiaoluMama.CHARGED:
            update_fields.append('charge_status')
            self.charge_status = XiaoluMama.CHARGED  # 接管状态
        if self.agencylevel < XiaoluMama.VIP_LEVEL:  # 如果代理等级是普通类型更新代理等级到A类
            update_fields.append("agencylevel")
            self.agencylevel = XiaoluMama.A_LEVEL
        if update_fields:
            self.save(update_fields=update_fields)
            return True
        return False

    def is_direct_pay(self):
        """ 直接付费接管的状态 """
        if self.charge_status == XiaoluMama.CHARGED and self.last_renew_type in (XiaoluMama.HALF, XiaoluMama.FULL):
            return False
        return True

    def is_trialable(self):
        """ 是否　可以　试用　"""
        if self.charge_status == XiaoluMama.UNCHARGE:  # 如果是没有接管的可以试用
            return True
        elif self.charge_status == XiaoluMama.CHARGED and self.status == XiaoluMama.FROZEN and \
                self.last_renew_type in [XiaoluMama.TRIAL, XiaoluMama.SCAN]:
            return True
        return False

    def is_renewable(self):
        """　是否可以续费 """
        if self.charge_status != XiaoluMama.CHARGED:
            return False
        if self.last_renew_type in [XiaoluMama.TRIAL, XiaoluMama.SCAN]:
            return False
        return True

    def is_cashoutable(self):
        if self.agencylevel >= self.VIP_LEVEL and \
                        self.charge_status == self.CHARGED and self.status == self.EFFECT and \
                        self.last_renew_type > XiaoluMama.TRIAL:  # 最后续费类型大于　试用类型　可以提现
            return True
        return False

    def is_noaudit_cashoutable(self):
        """
        无需审核，小额提现
        """
        return self.agencylevel >= self.VIP_LEVEL and \
            self.charge_status == self.CHARGED and self.status == self.EFFECT

    def is_relationshipable(self):
        return self.agencylevel >= self.VIP_LEVEL and \
               self.charge_status == self.CHARGED and self.status == self.EFFECT

    def is_click_countable(self):
        today = datetime.date.today()
        today_time = datetime.datetime(today.year, today.month, today.day)
        return self.agencylevel >= self.VIP_LEVEL and self.charge_status == self.CHARGED and \
            self.status == self.EFFECT and self.renew_time > today_time
           

    def get_cash_iters(self):
        if not self.is_cashoutable():
            return 0
        cash = self.cash / 100.0
        clog_outs = CarryLog.objects.filter(xlmm=self.id, log_type=CarryLog.ORDER_BUY,
                                            carry_type=CarryLog.CARRY_OUT, status=CarryLog.CONFIRMED)
        consume_value = (clog_outs.aggregate(total_value=Sum('value')).get('total_value') or 0) / 100.0
        clog_refunds = CarryLog.objects.filter(xlmm=self.id, log_type=CarryLog.REFUND_RETURN,
                                               carry_type=CarryLog.CARRY_IN, status=CarryLog.CONFIRMED)
        refund_value = (clog_refunds.aggregate(total_value=Sum('value')).get('total_value') or 0) / 100.0

        payment = consume_value - refund_value
        x_choice = self.get_base_deposite()
        mony_without_pay = cash + payment  # 从未消费情况下的金额
        leave_cash_out = mony_without_pay - x_choice - self.lowest_uncoushout  # 减去代理的最低不可提现金额(充值) = 可提现金额
        could_cash_out = cash
        if leave_cash_out < cash:
            could_cash_out = leave_cash_out
        if could_cash_out < 0:
            could_cash_out = 0
        return could_cash_out

    def get_share_qrcode_path(self):
        return constants.MAMA_LINK_FILEPATH.format(**{'mm_linkid': self.id})

    def get_share_qrcode_url(self):
        if self.qrcode_link.strip():
            return self.qrcode_link

        qr_path = self.get_share_qrcode_path().lstrip('\/')
        share_link = constants.MAMA_SHARE_LINK.format(**{'site_url': settings.M_SITE_URL,
                                                         'mm_linkid': self.id})
        from core.upload.xqrcode import push_qrcode_to_remote
        qrcode_url = push_qrcode_to_remote(qr_path, share_link)

        return qrcode_url

    def get_customer(self):
        """ 获取妈妈的特卖用户对象 """
        if not hasattr(self, '_customer_'):
            from flashsale.pay.models import Customer
            self._customer_ = Customer.objects.filter(unionid=self.openid).first()
        return self._customer_

    def get_mama_customer(self):
        """ 获取妈妈的特卖用户对象 """
        if not hasattr(self, '_mama_customer_'):
            from flashsale.pay.models import Customer
            self._mama_customer_ = Customer.objects.filter(unionid=self.openid, status=Customer.NORMAL).first()
        return self._mama_customer_

    @property
    def customer_id(self):
        from flashsale.pay.models import Customer
        c = Customer.objects.filter(unionid=self.openid).first()
        if c:
            return c.id
        return 0

    @property
    def nick(self):
        return self.get_mama_customer().nick if self.get_mama_customer() else ''

    @property
    def thumbnail(self):
        return self.get_mama_customer().thumbnail if self.get_mama_customer() else ''

    @property
    def mama_fortune(self):
        from flashsale.xiaolumm.models import MamaFortune
        if not hasattr(self, '_mama_fortune_'):
            self._mama_fortune_ = MamaFortune.objects.filter(mama_id=self.id).first()
        return self._mama_fortune_

    def get_parent_mama_ids(self):
        from .models_fortune import ReferalRelationship
        res = []
        parent = ReferalRelationship.objects.filter(referal_to_mama_id=self.id).first()
        if parent:
            res.append(parent.referal_from_mama_id)
        if self.last_renew_type == XiaoluMama.TRIAL:
            parent = PotentialMama.objects.filter(potential_mama=self.id).first()
            if parent:
                res.append(parent.referal_mama)
        return res

    def get_lv_team_member_ids(self):
        """
            获取下二级用户
        """
        from .models_fortune import ReferalRelationship
        lv1_id = [self.id]
        lv2_ids = [i['referal_to_mama_id'] for i in
                   ReferalRelationship.objects.filter(referal_from_mama_id=self.id).values('referal_to_mama_id')]
        lv3_ids = [i['referal_to_mama_id'] for i in
                   ReferalRelationship.objects.filter(referal_from_mama_id__in=lv2_ids).values('referal_to_mama_id')]
        return lv1_id, lv2_ids, lv3_ids

    def get_team_member_ids(self):
        from .models_fortune import ReferalRelationship
        ids = [r['referal_to_mama_id'] for r in ReferalRelationship.objects.filter(Q(referal_from_mama_id=self.id)|Q(referal_from_grandma_id=self.id)).values('referal_to_mama_id')]
        return [self.id] + ids

    def get_family_memeber_ids(self):
        """
            获取自己，妈妈和奶奶的id
        """
        res = [self.id]
        from .models_fortune import ReferalRelationship
        r = ReferalRelationship.objects.filter(referal_to_mama_id=self.id).first()
        if r:
            if r.referal_from_mama_id:
                res.append(r.referal_from_mama_id)
            if r.referal_from_grandma_id:
                res.append(r.referal_from_grandma_id)
        return res

    def get_invite_normal_mama_ids(self):
        from .models_fortune import ReferalRelationship
        return [i['referal_to_mama_id'] for i in
                ReferalRelationship.objects.filter(referal_from_mama_id=self.id).values('referal_to_mama_id')]

    def get_activite_num(self):
        from .models_fortune import CarryRecord
        i = 0
        mmids = self.get_invite_normal_mama_ids() + self.get_invite_potential_mama_ids()
        for mmid in mmids:
            t = CarryRecord.objects.filter(mama_id=mmid).values('carry_num'). \
                    aggregate(total=Sum('carry_num')).get('total') or 0
            if t > 0:
                i += 1
        return i

    def get_invite_potential_mama_ids(self):
        return [p['potential_mama'] for p in PotentialMama.objects.filter(referal_mama=self.id).values('potential_mama')]

    def get_active_invite_potential_mama_ids(self):
        from .models_fortune import CarryRecord
        res = []
        mmids = self.get_invite_potential_mama_ids()
        for mmid in mmids:
            t = CarryRecord.objects.filter(mama_id=mmid).values('carry_num'). \
                    aggregate(total=Sum('carry_num')).get('total') or 0
            if t > 0:
                res.append(mmid)
        return res

    def upgrade_agencylevel_by_cashout(self):
        """ 代理 升级 提现满足条件升级（仅仅从Ａ类升级到VIP1）
        :type
        """
        if self.agencylevel < XiaoluMama.VIP_LEVEL:  # 当前等级小于2则返回false
            return False
        if self.charge_status != XiaoluMama.CHARGED:  # 没有接管返回false
            return False
        if self.status != XiaoluMama.EFFECT:  # 非正常状态 返回false
            return False
        if self.agencylevel == XiaoluMama.A_LEVEL:  # A_LEVEL 升级到VIP_LEVEL
            self.agencylevel = XiaoluMama.VIP_LEVEL
            self.save(update_fields=['agencylevel'])
            return True

    def upgrade_agencylevel_by_exam(self, level=None):
        """ 代理 升级
        :type level: int 表示要升级的等级数 升级的
        """
        level_map = {
            XiaoluMama.A_LEVEL: XiaoluMama.VIP2_LEVEL,  # A 类升级到v2
            XiaoluMama.VIP_LEVEL: XiaoluMama.VIP2_LEVEL,  # v1 类升级到v2
            XiaoluMama.VIP2_LEVEL: XiaoluMama.VIP4_LEVEL,  # v2 类升级到v4
            XiaoluMama.VIP4_LEVEL: XiaoluMama.VIP6_LEVEL,  # v4 类升级到v6
            XiaoluMama.VIP6_LEVEL: XiaoluMama.VIP8_LEVEL  # v6 类升级到v8
        }
        try:
            upper_level = level_map[self.agencylevel]
        except KeyError:  # 没有找到升级值返回False
            return False
        if upper_level != level:  # 要升级的等级　和指定升级的等级不一致　则不处理
            return False
        if self.agencylevel < XiaoluMama.VIP_LEVEL:  # 当前等级小于2则返回false
            return False
        if self.charge_status != XiaoluMama.CHARGED:  # 没有接管返回false
            return False
        if self.status != XiaoluMama.EFFECT:  # 非正常状态 返回false
            return False
        # 当前等级小于考试通过指定的等级 并且是接管状态的 则升级
        self.agencylevel = level
        self.save(update_fields=['agencylevel'])
        return True

    def upgrade_agencylevel_by_invite_and_payment(self):
        """ 邀请数量和销售额升级 """
        if self.agencylevel != XiaoluMama.A_LEVEL:
            return False
        else:
            self.agencylevel = XiaoluMama.VIP_LEVEL
            self.save(update_fields=['agencylevel'])
            return True

    def next_agencylevel_info(self):
        level_map = {
            XiaoluMama.INNER_LEVEL: (XiaoluMama.A_LEVEL, XiaoluMama.AGENCY_LEVEL[2][1]),
            XiaoluMama.A_LEVEL: (XiaoluMama.VIP_LEVEL, XiaoluMama.AGENCY_LEVEL[1][1]),
            XiaoluMama.VIP_LEVEL: (XiaoluMama.VIP2_LEVEL, XiaoluMama.AGENCY_LEVEL[3][1]),
            XiaoluMama.VIP2_LEVEL: (XiaoluMama.VIP4_LEVEL, XiaoluMama.AGENCY_LEVEL[4][1]),
            XiaoluMama.VIP4_LEVEL: (XiaoluMama.VIP6_LEVEL, XiaoluMama.AGENCY_LEVEL[5][1]),
            XiaoluMama.VIP6_LEVEL: (XiaoluMama.VIP8_LEVEL, XiaoluMama.AGENCY_LEVEL[6][1]),
            XiaoluMama.VIP8_LEVEL: (XiaoluMama.VIP8_LEVEL, XiaoluMama.AGENCY_LEVEL[6][1]),
        }
        return level_map[self.agencylevel]

    def fill_info(self, mobile, referal_from):
        update_fields = []
        if self.mobile is None or (not self.mobile.strip()):
            self.mobile = mobile
            update_fields.append('mobile')
        if self.referal_from is None or (not self.mobile.strip()):
            self.referal_from = referal_from
            update_fields.append('referal_from')
        if self.progress != XiaoluMama.PROFILE:
            self.progress = XiaoluMama.PROFILE
            update_fields.append('progress')
        if update_fields:
            self.save(update_fields=update_fields)
        return

    @staticmethod
    def ranking_list_income():
        """
            个人收入排行榜
        """

        return []

    @staticmethod
    def ranking_list_turnover():
        """
            个人交易额排行榜
        """
        return []

    @staticmethod
    def ranking_list_team_income():
        """
            团队收入排行榜
        """
        return []

    @staticmethod
    def ranking_list_team_turnover():
        """
           团队交易额排行榜
        """
        return []

    def update_renew_day(self, days):
        """
        修改该代理的下次续费时间
        """
        if days not in [XiaoluMama.SCAN, XiaoluMama.TRIAL, XiaoluMama.HALF,
                        XiaoluMama.FULL]:
            raise AssertionError(u'续费天数异常')
        now = datetime.datetime.now()
        update_fields = ['renew_time']
        renew_time = now + datetime.timedelta(days=days + 1)
        if isinstance(self.renew_time, datetime.datetime):  # 有效状态则累加
            readd_renew_time = self.renew_time + datetime.timedelta(days=days + 1)
            renew_time = max(readd_renew_time, renew_time)
        self.renew_time = renew_time
        if renew_time > now and self.status == XiaoluMama.FROZEN:
            self.status = XiaoluMama.EFFECT
            update_fields.append('status')

        last_renew_type = days
        if self.last_renew_type == XiaoluMama.HALF and days == XiaoluMama.HALF:  # 如果用户已经是半年类型了 再次续费则变为一年
            last_renew_type = XiaoluMama.FULL
        if self.last_renew_type != last_renew_type:  # days  对应 HALF　FULL
            self.last_renew_type = last_renew_type
            update_fields.append('last_renew_type')
        self.save(update_fields=update_fields)
        return True

    def update_mobile(self, mobile=None):
        if mobile and self.mobile != mobile and len(mobile) == 11:
            self.mobile = mobile
            self.save(update_fields=['mobile'])
            return True
        return False

    def get_next_new_mama_task(self):
        """
        获取未完成的新手任务
        """
        from flashsale.coupon.models import OrderShareCoupon
        from flashsale.xiaolumm.models import XlmmFans, PotentialMama
        from flashsale.xiaolumm.models.models_fortune import CarryRecord, OrderCarry, ReferalRelationship
        from shopapp.weixin.models_base import WeixinFans

        customer = self.get_customer()

        subscribe_weixin = WeixinFans.objects.filter(
            unionid=customer.unionid, subscribe=True, app_key=settings.WXPAY_APPID).exists()
        if not subscribe_weixin:
            return NewMamaTask.TASK_SUBSCRIBE_WEIXIN

        carry_record = CarryRecord.objects.filter(mama_id=self.id, carry_type=CarryRecord.CR_CLICK).exists()
        if not carry_record:
            return NewMamaTask.TASK_FIRST_CARRY

        coupon_share = OrderShareCoupon.objects.filter(share_customer=customer.id).exists()
        if not coupon_share:
            return NewMamaTask.TASK_FIRST_SHARE_COUPON

        fans_record = XlmmFans.objects.filter(xlmm=self.id).exists()
        if not fans_record:
            return NewMamaTask.TASK_FIRST_FANS

        mama_recommend = PotentialMama.objects.filter(referal_mama=self.id).exists() or \
            ReferalRelationship.objects.filter(referal_from_mama_id=self.id).exists()
        if not mama_recommend:
            return NewMamaTask.TASK_FIRST_MAMA_RECOMMEND

        commission = OrderCarry.objects.filter(mama_id=self.id).exists()
        if not commission:
            return NewMamaTask.TASK_FIRST_COMMISSION

        from flashsale.xiaolumm.tasks_mama_fortune import task_new_guy_task_complete_send_award
        task_new_guy_task_complete_send_award.delay(self)

        return None

    @classmethod
    def get_referal_mama_id(cls, customer, extras_info=None):
        """ 根据订单获取用户的推荐人 订单上面没有的话则寻找粉丝记录的妈妈作为推荐人 """
        extra_link = extras_info.get('mm_linkid') or 0 if extras_info else 0
        mama_id = str(extra_link).strip()
        mm_linkid = int(mama_id) if mama_id.isdigit() else 0
        if not mm_linkid:   # 没有则获取粉丝记录
            from flashsale.xiaolumm.models import XlmmFans
            fans = XlmmFans.objects.filter(fans_cusid=customer.id).first()
            return fans.xlmm if fans else 0
        else:
            return mm_linkid


def xiaolumama_update_mamafortune(sender, instance, created, **kwargs):
    from flashsale.xiaolumm import tasks_mama_fortune
    tasks_mama_fortune.task_xiaolumama_update_mamafortune.delay(instance.pk, instance.cash)


post_save.connect(xiaolumama_update_mamafortune,
                  sender=XiaoluMama, dispatch_uid='post_save_xiaolumama_update_mamafortune')


def update_trial_mama_full_member_by_condition(sender, instance, created, **kwargs):
    from flashsale.xiaolumm.tasks import task_update_trial_mama_full_member_by_condition

    task_update_trial_mama_full_member_by_condition.delay(instance)


post_save.connect(update_trial_mama_full_member_by_condition,
                  sender=XiaoluMama, dispatch_uid='post_save_update_trial_mama_full_member_by_condition')


def created_instructor_for_mama(sender, instance, created, **kwargs):
    """
    为小鹿妈妈创建讲师
    """
    if instance.charge_status == XiaoluMama.CHARGED and instance.status == XiaoluMama.EFFECT:
        from flashsale.xiaolumm.models import Instructor
        customer = instance.get_customer()
        if not customer:
            return
        instructor = Instructor.objects.filter(mama_id=instance.id).first()
        if instructor:
            instructor.update_status(status=Instructor.STATUS_EFFECT)  # 改为合格
        else:  # 没有则创建讲师记录
            Instructor.create_instruct(
                name=customer.nick,
                title='特聘讲师',
                image=customer.thumbnail,
                introduction='',
                mama_id=instance.id,
                status=Instructor.STATUS_EFFECT)

# post_save.connect(created_instructor_for_mama, sender=XiaoluMama,
#                   dispatch_uid=u'post_save_created_instructor_for_mama')


class AgencyLevel(models.Model):
    category = models.CharField(max_length=11, unique=True, blank=False, verbose_name=u"类别")
    deposit = models.IntegerField(default=0, verbose_name=u"押金(元)")
    cash = models.IntegerField(default=0, verbose_name=u"现金(元)")
    basic_rate = models.IntegerField(default=0, verbose_name=u"基本佣金率（百分比）")
    target = models.IntegerField(default=0, verbose_name=u"达标额度（元）")
    extra_rate = models.IntegerField(default=0, verbose_name=u"奖励佣金率（百分比）")
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')

    class Meta:
        db_table = 'xiaolumm_agencylevel'
        app_label = 'xiaolumm'
        verbose_name = u'代理类别'
        verbose_name_plural = u'代理类别列表'

    def __unicode__(self):
        return '%s' % self.id

    def get_basic_rate_display(self):
        return self.basic_rate / 100.0

    get_basic_rate_display.allow_tags = True
    get_basic_rate_display.short_description = u"基本佣金率"

    @property
    def basic_rate_percent(self):
        return self.get_basic_rate_display()

    def get_extra_rate_display(self):
        return self.extra_rate / 100.0

    get_extra_rate_display.allow_tags = True
    get_extra_rate_display.admin_order_field = 'extra_rate'
    get_extra_rate_display.short_description = u"奖励佣金率"

    def extra_rate_percent(self):
        return self.get_extra_rate_display()

    def get_Click_Price(self, order_num):
        """ 点击据订单价格提成 """
        if self.id < 2:
            return 0
        return 0

    #         click_price = 0
    #         if order_num > 2:
    #             click_price = 0.3
    #         else:
    #             click_price += order_num * 0.1
    #
    #         return click_price * 100

    def get_Max_Valid_Clickcount(self, order_num):
        return MM_CLICK_DAY_BASE_COUNT + MM_CLICK_PER_ORDER_PLUS_COUNT * order_num

    def get_Rebeta_Rate(self, *args, **kwargs):

        today = datetime.date.today()
        if today > ORDER_RATEUP_START:
            return self.basic_rate / 100.0
        return (self.basic_rate / 100.0) / 2


class CashOut(BaseModel):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    COMPLETED = 'completed'
    CANCEL = 'cancel'
    SENDFAIL = 'fail'

    STATUS_CHOICES = (
        (PENDING, u'待审核'),
        (APPROVED, u'审核通过'),
        (REJECTED, u'已拒绝'),
        (CANCEL, u'取消'),
        (COMPLETED, u'完成'),
        (SENDFAIL, u'发送失败')
    )
    MAMA_RENEW = 'renew'
    USER_BUDGET = 'budget'
    RED_PACKET = 'red'
    EXCHANGE_COUPON = 'coupon'

    TYPE_CHOICES = (
        (MAMA_RENEW, u'妈妈续费'),
        (USER_BUDGET, u'提至余额'),
        (RED_PACKET, u'微信红包'),
        (EXCHANGE_COUPON, u'兑换优惠券')
    )

    xlmm = models.IntegerField(default=0, db_index=True, verbose_name=u"妈妈编号")
    value = models.IntegerField(default=0, verbose_name=u"金额(分)")
    status = models.CharField(max_length=16, blank=True, choices=STATUS_CHOICES, default=PENDING, verbose_name=u'状态')
    approve_time = models.DateTimeField(blank=True, null=True, verbose_name=u'审核时间')
    # created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    cash_out_type = models.CharField(max_length=8, choices=TYPE_CHOICES, default=RED_PACKET, verbose_name=u'提现类型')
    date_field = models.DateField(default=datetime.date.today, db_index=True, verbose_name=u'日期')
    uni_key = models.CharField(max_length=128, blank=True, null=True, unique=True, verbose_name=u'唯一ID')
    
    class Meta:
        db_table = 'xiaolumm_cashout'
        app_label = 'xiaolumm'
        verbose_name = u'提现记录'
        verbose_name_plural = u'提现记录列表'
        permissions = [('xiaolumm_cashout_bat_handler', u'提现批量审核')]

    def __unicode__(self):
        return '%s' % self.id

    def get_value_display(self):
        return self.value / 100.0

    get_value_display.allow_tags = True
    get_value_display.admin_order_field = 'value'
    get_value_display.short_description = u"提现金额"

    @classmethod
    def is_cashout_limited(cls, mama_id):
        from flashsale.restpro.v2.views.xiaolumm import CashOutPolicyView
        CASHOUT_NUM_LIMIT = CashOutPolicyView.DAILY_CASHOUT_TRIES
        date_field = datetime.date.today()
        cnt = cls.objects.filter(xlmm=mama_id, cash_out_type=cls.RED_PACKET, date_field=date_field).\
              exclude(status=cls.CANCEL).exclude(status=cls.REJECTED).count()
        if cnt < CASHOUT_NUM_LIMIT and cnt >= 0:
            return False
        return True

    @classmethod
    def gen_uni_key(cls, mama_id, cash_out_type):
        date_field = datetime.date.today()
        count = cls.objects.filter(xlmm=mama_id, cash_out_type=cash_out_type, date_field=date_field).count()
        return '%s-%d-%d|%s' % (cash_out_type, mama_id, count+1, date_field)
                    
    @property
    def value_money(self):
        return self.get_value_display()

    def cancel_cashout(self):
        """取消提现"""
        if self.status == CashOut.PENDING:  # 待审核状态才允许取消
            self.status = CashOut.CANCEL
            self.save()
            return True
        return False

    def reject_cashout(self):
        """拒绝提现"""
        if self.status == CashOut.PENDING:  # 待审核状态才允许拒绝
            self.status = CashOut.REJECTED
            self.save()
            return True
        return False

    def approve_cashout(self):
        """同意提现"""
        if self.status == CashOut.PENDING:  # 待审核状态才允许同意
            self.status = CashOut.APPROVED
            self.approve_time = datetime.datetime.now()  # 通过时间
            self.save()
            return True
        return False

    def fail_and_return(self):
        if self.status == CashOut.APPROVED:
            self.status = CashOut.SENDFAIL
            self.save()
            return True
        return False

    def is_confirmed(self):
        return self.status == CashOut.APPROVED


def cashout_update_mamafortune(sender, instance, created, **kwargs):
    from flashsale.xiaolumm import tasks_mama_fortune
    tasks_mama_fortune.task_cashout_update_mamafortune.delay(instance.xlmm)


post_save.connect(cashout_update_mamafortune,
                  sender=CashOut, dispatch_uid='post_save_cashout_update_mamafortune')


class CarryLog(models.Model):
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    CANCELED = 'canceled'

    STATUS_CHOICES = (
        (PENDING, u'待确认'),
        (CONFIRMED, u'已确定'),
        (CANCELED, u'已取消'),
    )

    ORDER_REBETA = 'rebeta'
    ORDER_BUY = 'buy'
    CLICK_REBETA = 'click'
    REFUND_RETURN = 'refund'
    REFUND_OFF = 'reoff'
    CASH_OUT = 'cashout'
    DEPOSIT = 'deposit'
    THOUSAND_REBETA = 'thousand'
    AGENCY_SUBSIDY = 'subsidy'
    MAMA_RECRUIT = 'recruit'
    ORDER_RED_PAC = 'ordred'
    COST_FLUSH = 'flush'
    RECHARGE = 'recharge'
    FANSCARRY = 'fan_cary'  # fans_carry
    GROUPBONUS = 'grp_bns'  # group_bonus
    ACTIVITY = 'activity'  # activity bonus

    LOG_TYPE_CHOICES = (
        (ORDER_REBETA, u'订单返利'),
        (ORDER_BUY, u'消费支出'),
        (REFUND_RETURN, u'退款返现'),
        (REFUND_OFF, u'退款扣除'),
        (CLICK_REBETA, u'点击兑现'),
        (CASH_OUT, u'钱包提现'),
        (DEPOSIT, u'押金'),
        (THOUSAND_REBETA, u'千元提成'),
        (AGENCY_SUBSIDY, u'代理补贴'),
        (MAMA_RECRUIT, u'招募奖金'),
        (ORDER_RED_PAC, u'订单红包'),
        (COST_FLUSH, u'补差额'),
        (RECHARGE, u'充值'),
        (FANSCARRY, u'粉丝提成'),
        (GROUPBONUS, u'团员奖金'),
        (ACTIVITY, u'活动奖金')
    )

    CARRY_OUT = 'out'
    CARRY_IN = 'in'
    CARRY_TYPE_CHOICES = (
        (CARRY_OUT, u'支出'),
        (CARRY_IN, u'收入'),
    )

    xlmm = models.BigIntegerField(default=0, db_index=True, verbose_name=u"妈妈编号")
    order_num = models.BigIntegerField(default=0, db_index=True, verbose_name=u"记录标识")
    buyer_nick = models.CharField(max_length=32, blank=True, verbose_name=u'买家昵称')
    value = models.IntegerField(default=0, verbose_name=u"金额")

    log_type = models.CharField(max_length=8, blank=True,
                                choices=LOG_TYPE_CHOICES,
                                default=ORDER_REBETA, verbose_name=u"类型")

    carry_type = models.CharField(max_length=8, blank=True,
                                  choices=CARRY_TYPE_CHOICES,
                                  default=CARRY_OUT, verbose_name=u"盈负")

    status = models.CharField(max_length=16, blank=True,
                              choices=STATUS_CHOICES,
                              default=CONFIRMED, verbose_name=u'状态')

    carry_date = models.DateField(default=datetime.date.today, verbose_name=u'业务日期')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')

    class Meta:
        db_table = 'xiaolumm_carrylog'
        app_label = 'xiaolumm'
        verbose_name = u'妈妈钱包/收支记录'
        verbose_name_plural = u'妈妈钱包/收支记录列表'

    def __unicode__(self):
        return '%s' % self.id

    def get_value_display(self):
        return self.value / 100.0

    get_value_display.allow_tags = True
    get_value_display.admin_order_field = 'value'
    get_value_display.short_description = u"金额"

    @property
    def value_money(self):
        return self.get_value_display()

    @property
    def log_type_name(self):
        return self.get_log_type_display()

    @property
    def carry_type_name(self):
        return self.get_carry_type_display()

    @property
    def status_name(self):
        return self.get_status_display()

    def cancel_and_return(self):
        """ 取消并返回妈妈账户 """
        if self.status not in (self.PENDING, self.CONFIRMED):
            return False
        self.status = self.CANCELED
        self.save()
        xlmm = XiaoluMama.objects.get(id=self.xlmm)
        xlmm.cash = models.F('cash') + self.value
        update_model_fields(xlmm, update_fields=['cash'])

    def dayly_in_value(self):
        """ 计算当天的收入总额 """
        log_types = [CarryLog.ORDER_REBETA, CarryLog.CLICK_REBETA,
                     CarryLog.THOUSAND_REBETA, CarryLog.AGENCY_SUBSIDY, CarryLog.MAMA_RECRUIT, CarryLog.ORDER_RED_PAC]
        cls = self.__class__.objects.filter(xlmm=self.xlmm, carry_date=self.carry_date, log_type__in=log_types)
        cls = cls.exclude(carry_type=CarryLog.CARRY_OUT).exclude(status=CarryLog.CANCELED)
        sum_value = cls.aggregate(sum_value=Sum('value')).get('sum_value') or 0
        return sum_value / 100.0

    def dayly_clk_value(self):
        cls = self.__class__.objects.filter(xlmm=self.xlmm,
                                            carry_date=self.carry_date,
                                            log_type=CarryLog.CLICK_REBETA).exclude(status=CarryLog.CANCELED)
        sum_value = cls.aggregate(sum_value=Sum('value')).get('sum_value') or 0
        return sum_value / 100.0

    def get_type_clk_cnt(self):
        """ 计算点击类型的当天点击数量"""
        clks = ClickCount.objects.filter(linkid=self.xlmm, date=self.carry_date)
        cnt = clks.aggregate(cliknum=Sum('valid_num')).get('cliknum') or 0
        return cnt

    def get_type_shop_cnt(self):
        """ 计算订单补贴类型的当天订单数量"""
        from flashsale.clickrebeta.models import StatisticsShopping
        lefttime = self.carry_date
        righttime = lefttime + datetime.timedelta(days=1)
        cnt = StatisticsShopping.objects.filter(linkid=self.xlmm,
                                                shoptime__gte=lefttime, shoptime__lt=righttime,
                                                status__in=(StatisticsShopping.FINISHED,
                                                            StatisticsShopping.WAIT_SEND)).count()
        return cnt

    def get_carry_desc(self):
        """
        如果是点击类型，计算当天的点击数量添加到描述
        如果是订单类型，计算当天的订单数量添加到描述
        其他类型，返回相应的描述
        """
        if self.carry_type == CarryLog.CARRY_IN:
            if self.log_type == CarryLog.CLICK_REBETA:
                clk_cnt = self.get_type_clk_cnt()
                des = choice(constants.CARRY_LOG_CLK_DESC).format(clk_cnt, self.get_status_display())
            elif self.log_type == CarryLog.ORDER_REBETA:
                shop_cnt = self.get_type_shop_cnt()
                des = choice(constants.CARRY_LOG_SHOP_DESC).format(shop_cnt, self.get_status_display())
            elif self.log_type == CarryLog.AGENCY_SUBSIDY:
                des = choice(constants.CARRY_LOG_AGENCY_SUBSIDY).format(self.order_num, self.get_status_display())
            else:
                des = constants.CARRY_IN_DEFAULT_DESC.format(self.get_status_display())
        else:
            des = constants.CARRY_OUT_DES.format(self.get_status_display())
        return des


from flashsale.xiaolumm import signals


def push_Pending_Carry_To_Cash(obj, *args, **kwargs):
    from flashsale.xiaolumm import tasks
    # 更新提成金额
    tasks.task_Push_Pending_Carry_Cash.delay(xlmm_id=obj)


signals.signal_push_pending_carry_to_cash.connect(push_Pending_Carry_To_Cash, sender=XiaoluMama)


class PotentialMama(BaseModel):
    """
    潜在代理: 针对一元开店用户
    """
    potential_mama = models.IntegerField(db_index=True, unique=True, verbose_name=u"潜在妈妈专属id")
    referal_mama = models.IntegerField(db_index=True, verbose_name=u"推荐人专属id")
    nick = models.CharField(max_length=32, blank=True, verbose_name=u"潜在妈妈昵称")
    thumbnail = models.CharField(max_length=256, blank=True, verbose_name=u"潜在妈妈头像")
    uni_key = models.CharField(max_length=32, unique=True, verbose_name=u"唯一key")
    is_full_member = models.BooleanField(default=False, verbose_name=u"是否转正")
    last_renew_type = models.IntegerField(default=XiaoluMama.TRIAL,
                                          choices=XiaoluMama.RENEW_TYPE, verbose_name=u'最后续费类型')
    extras = JSONCharMyField(max_length=512, default={}, blank=True, null=True, verbose_name=u"附加信息")
    # 最后续费类型使用一次 转正的时候 同步到 ReferalRelationship

    class Meta:
        db_table = 'xiaolumm_potential_record'
        app_label = 'xiaolumm'
        verbose_name = u'小鹿妈妈/潜在小鹿妈妈表'
        verbose_name_plural = u'小鹿妈妈/潜在小鹿妈妈列表'

    def __unicode__(self):
        return '%s-%s' % (self.potential_mama, self.referal_mama)

    @classmethod
    def gen_uni_key(cls, mama_id, referal_from_mama_id):
        return '/'.join([str(mama_id), str(referal_from_mama_id)])

    def update_full_member(self, last_renew_type, extra=None):
        """ 妈妈成为正式妈妈　切换is_full_member状态为True """
        update_fields = []
        if self.last_renew_type != last_renew_type:
            self.last_renew_type = last_renew_type
            update_fields.append('last_renew_type')
        if not self.is_full_member:
            self.is_full_member = True
            update_fields.append('is_full_member')
        if isinstance(self.extras, dict):
            self.extras.update(extra)
            update_fields.append('extras')
        else:
            self.extras = extra
            update_fields.append('extras')
        if update_fields:
            self.save(update_fields=update_fields)
            return True
        return False


def potentialmama_xlmm_newtask(sender, instance, **kwargs):
    """
    检测新手任务：发展第一个代理　
    """
    from flashsale.xiaolumm.tasks_mama_push import task_push_new_mama_task
    from flashsale.xiaolumm.models.new_mama_task import NewMamaTask
    from flashsale.xiaolumm.models.models_fortune import ReferalRelationship

    potentialmama = instance
    xlmm_id = potentialmama.referal_mama
    xlmm = XiaoluMama.objects.filter(id=xlmm_id).first()

    item = PotentialMama.objects.filter(referal_mama=xlmm_id).exists() or \
        ReferalRelationship.objects.filter(referal_from_mama_id=xlmm_id).exists()

    if not item:
        task_push_new_mama_task.delay(xlmm, NewMamaTask.TASK_FIRST_MAMA_RECOMMEND)

pre_save.connect(potentialmama_xlmm_newtask,
                 sender=PotentialMama, dispatch_uid='pre_save_potentialmama_xlmm_newtask')


#def potentialmama_push_sms(sender, instance, created, **kwargs):
#    """
#    新加入一元妈妈，发送短信引导关注小鹿美美
#    如果已经关注，直接微信发新手任务
#    """
#    from flashsale.xiaolumm.tasks_mama_push import task_sms_push_mama, task_push_new_mama_task
#    from flashsale.xiaolumm.tasks_mama_fortune import task_subscribe_weixin_send_award
#    from flashsale.xiaolumm.models.new_mama_task import NewMamaTask
#    from shopapp.weixin.models_base import WeixinFans
#
#    potentialmama = instance
#
#    if created:
#        xlmm = XiaoluMama.objects.filter(id=potentialmama.potential_mama).first()
#        customer = xlmm.get_customer()
#        has_subscribe = WeixinFans.objects.filter(
#            unionid=customer.unionid, app_key=settings.WXPAY_APPID, subscribe=True).first()
#
#        if not has_subscribe:  # 没关注
#            task_sms_push_mama.delay(xlmm)
#        else:  # 已关注
#            task_subscribe_weixin_send_award.delay(xlmm)
#            task_push_new_mama_task.delay(xlmm, NewMamaTask.TASK_SUBSCRIBE_WEIXIN)
#
#post_save.connect(potentialmama_push_sms,
#                  sender=PotentialMama, dispatch_uid='pre_save_potentialmama_push_sms')


def update_mama_relationship(sender, instance, created, **kwargs):
    #if not instance.is_full_member:
    #    return
    from flashsale.xiaolumm.models import ReferalRelationship
    from core.options import log_action, CHANGE, get_systemoa_user

    ship = ReferalRelationship.objects.filter(referal_to_mama_id=instance.potential_mama).first()  # 推荐关系记录
    if not ship:  # 没有推荐关系 则新建
        try:
            ship = ReferalRelationship.create_relationship_by_potential(instance)
            sys_oa = get_systemoa_user()
            log_action(sys_oa, ship, CHANGE, u'通过潜在关系创建推荐关系记录')
            return
        except Exception as exc:
            logger.info({"action": 'update_mama_relationship', 'potential_mama': instance.id, 'message': exc.message})
            return
    # 否则更新
    ship.update_referal_relationship(instance)


post_save.connect(update_mama_relationship,
                  sender=PotentialMama, dispatch_uid='post_save_update_mama_relationship')


# The invite_trial_num calculation is implementation in invite_num calculation function.
# This one gets retired. -- zifei 2016-9-8
#
#def update_mamafortune_invite_trial_num(sender, instance, created, **kwargs):
#    from flashsale.xiaolumm import tasks_mama_fortune
#    mama_id = instance.referal_mama
#    tasks_mama_fortune.task_update_mamafortune_invite_trial_num.delay(mama_id)
#
#post_save.connect(update_mamafortune_invite_trial_num,
#                  sender=PotentialMama, dispatch_uid='post_save_update_mamafortune_invite_trial_num')


#def send_invite_trial_award(sender, instance, created, **kwargs):
#    if not created:
#        return
#    from flashsale.xiaolumm import tasks_mama_fortune
#    tasks_mama_fortune.task_send_activate_award.delay(instance)
#
#post_save.connect(send_invite_trial_award,
#                  sender=PotentialMama, dispatch_uid='post_save_send_invite_trial_award')
#
#
#def send_invite_trial_weixin_push(sender, instance, created, **kwargs):
#    if not created:
#        return
#    from flashsale.xiaolumm import tasks_mama_push
#    tasks_mama_push.task_weixin_push_invite_trial.delay(instance)
#
#post_save.connect(send_invite_trial_weixin_push,
#                  sender=PotentialMama, dispatch_uid='post_save_send_invite_trial_weixin_push')


def unitary_mama(obj):
    """
    一元开店
    1. 修改记录为接管状态
    2. 添加 renew_time　now + 15d
    3. 修改代理等级到 A 类
    """
    from flashsale.xiaolumm.tasks import task_unitary_mama
    task_unitary_mama(obj)


def register_mama(obj):
    """
    代理注册
    1. 修改记录为接管状态
    2. 添加 renew_time　now + 365d　or 183d
    3. 修改代理等级到 A 类
    4. 填写推荐人
    """
    from flashsale.xiaolumm.tasks import task_register_mama
    task_register_mama(obj)


def renew_mama(obj):
    """
    代理续费
    1. 更新 renew_time
    """
    from flashsale.xiaolumm.tasks import task_renew_mama

    task_renew_mama(obj)

from flashsale.pay.signals import signal_saletrade_pay_confirm
from flashsale.pay.models import SaleTrade


def trigger_mama_deposit_action(sender, obj, *args, **kwargs):
    # 这里的先后顺序不能变　
    # 先判断是否能续费　在看接管状态
    renew_mama(obj)
    unitary_mama(obj)
    register_mama(obj)


signal_saletrade_pay_confirm.connect(trigger_mama_deposit_action,
                                     sender=SaleTrade,
                                     dispatch_uid="post_save_trigger_mama_deposit_action")


# 首单红包，10单红包

class OrderRedPacket(models.Model):
    xlmm = models.IntegerField(unique=True, blank=False, verbose_name=u"妈妈编号")
    first_red = models.BooleanField(default=False, verbose_name=u"首单红包")
    ten_order_red = models.BooleanField(default=False, verbose_name=u"十单红包")
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')

    class Meta:
        db_table = 'xiaolumm_order_red_packet'
        app_label = 'xiaolumm'
        verbose_name = u'妈妈订单红包表'
        verbose_name_plural = u'妈妈订单红包列表'


class MamaDayStats(models.Model):
    xlmm = models.IntegerField(default=0, verbose_name=u'妈妈编号')
    day_date = models.DateField(verbose_name=u'统计日期')
    base_click_price = models.IntegerField(default=0, verbose_name=u'基础点击价格')

    lweek_clicks = models.IntegerField(default=0, verbose_name=u'周有效点击')
    lweek_buyers = models.IntegerField(default=0, verbose_name=u'周购买用户')
    lweek_payment = models.IntegerField(default=0, verbose_name=u'周购买金额')

    tweek_clicks = models.IntegerField(default=0, verbose_name=u'两周有效点击')
    tweek_buyers = models.IntegerField(default=0, verbose_name=u'两周购买用户')
    tweek_payment = models.IntegerField(default=0, verbose_name=u'两周购买金额')

    class Meta:
        db_table = 'xiaolumm_dailystat'
        unique_together = ('xlmm', 'day_date')
        app_label = 'xiaolumm'
        verbose_name = u'妈妈/每日统计'
        verbose_name_plural = u'妈妈/每日统计列表'

    def get_base_click_price_display(self):
        return self.base_click_price / 100.0

    get_base_click_price_display.allow_tags = True
    get_base_click_price_display.admin_order_field = 'base_click_price'
    get_base_click_price_display.short_description = u"基础点击价格"

    def get_lweek_payment_display(self):
        return self.lweek_payment / 100.0

    get_lweek_payment_display.allow_tags = True
    get_lweek_payment_display.admin_order_field = 'lweek_payment'
    get_lweek_payment_display.short_description = u"周购买金额"

    def get_tweek_payment_display(self):
        return self.tweek_payment / 100.0

    get_tweek_payment_display.allow_tags = True
    get_tweek_payment_display.admin_order_field = 'tweek_payment'
    get_tweek_payment_display.short_description = u"两周购买金额"

    @property
    def lweek_roi(self):
        if self.lweek_clicks == 0:
            return 0
        return float('%.4f' % (self.lweek_buyers / (self.lweek_clicks * 1.0)))

    def get_lweek_roi_display(self):
        return self.lweek_roi

    get_lweek_roi_display.allow_tags = True
    get_lweek_roi_display.short_description = u"周转化率"

    @property
    def tweek_roi(self):
        if self.tweek_clicks == 0:
            return 0
        return float('%.4f' % (self.tweek_buyers / (self.tweek_clicks * 1.0)))

    def get_tweek_roi_display(self):
        return self.tweek_roi

    get_tweek_roi_display.allow_tags = True
    get_tweek_roi_display.short_description = u"两周转化率"

    def calc_click_price(self):

        if self.lweek_clicks < 50:
            return 20

        xlmm = XiaoluMama.objects.get(id=self.xlmm)
        if not xlmm.charge_time:
            return 0
        # 如果代理接管时间少于一周，点击价格为0.2元
        delta_days = (datetime.datetime.now() - xlmm.charge_time).days
        if delta_days < 5:
            return 20
        # 如果两周连续转化率为0
        if delta_days > 7 and self.tweek_clicks > 99 and self.tweek_roi == 0:
            return 1
        # 如果一周转化率为0
        if self.lweek_roi == 0:
            return 10

        return 20
