# -*- coding:utf8 -*-
__author__ = 'meixqhi'
import os.path
import json
from django.db import models
from django.conf import settings
from django.db.models import Sum, F
from shopback import paramconfig as pcfg
from shopback.items.models import Item, Product, ProductSku
from shopback.orders.models import Trade
from shopback.fenxiao.models import PurchaseOrder
from shopback.trades.models import MergeTrade, MergeOrder
from core.options import log_action, User, ADDITION, CHANGE
from shopback.signals import rule_signal
import logging

logger = logging.getLogger('django.request')

RULE_STATUS = (
    ('US', '使用'),
    ('SX', '失效'),
)
SCOPE_CHOICE = (
    ('trade', '交易域'),
    ('product', '商品域'),
)
RULE_TYPE_CHOICE = (
    (pcfg.RULE_PAYMENT_TYPE, '满就送'),
    (pcfg.RULE_SPLIT_TYPE, '组合拆分'),
    (pcfg.RULE_GIFTS_TYPE, '买就送'),
)


class TradeRule(models.Model):
    formula = models.CharField(max_length=64, blank=True, )
    memo = models.CharField(max_length=64, blank=True, )

    formula_desc = models.TextField(max_length=256, blank=True, )

    scope = models.CharField(max_length=10, choices=SCOPE_CHOICE, )
    status = models.CharField(max_length=2, choices=RULE_STATUS, )

    items = models.ManyToManyField(Item, related_name='rules',
                                   symmetrical=False,
                                   db_table='shop_memorule_itemrulemap')

    class Meta:
        db_table = 'shop_memorule_traderule'
        app_label = 'memorule'


FIELD_TYPE_CHOICE = (
    ('single', '单选'),
    ('check', '复选'),
    ('text', '文本'),
)


class RuleFieldType(models.Model):
    field_name = models.CharField(max_length=64, primary_key=True)
    field_type = models.CharField(max_length=10, choices=FIELD_TYPE_CHOICE)

    alias = models.CharField(max_length=64)
    default_value = models.TextField(max_length=256, blank=True)

    class Meta:
        db_table = 'shop_memorule_rulefieldtype'
        app_label = 'memorule'

    def __unicode__(self):
        return self.field_name + self.field_type


class ProductRuleField(models.Model):
    outer_id = models.CharField(max_length=64, db_index=True)
    field = models.ForeignKey(RuleFieldType)

    custom_alias = models.CharField(max_length=256, blank=True)
    custom_default = models.TextField(max_length=256, blank=True)

    class Meta:
        db_table = 'shop_memorule_productrulefield'
        app_label = 'memorule'
        verbose_name = u'待审核规则'

    @property
    def alias(self):
        return self.custom_alias or self.field.alias

    @property
    def default(self):
        value = self.custom_default or self.field.default_value
        if self.field.field_type == 'check' or self.field.field_type == 'single':
            return value.split(',')
        return value

    def to_json(self):
        return [self.field.field_name, self.alias, self.field.field_type, self.default]


class RuleMemo(models.Model):
    tid = models.BigIntegerField(primary_key=True)

    is_used = models.BooleanField(default=False)
    rule_memo = models.TextField(max_length=1000, blank=True)
    seller_flag = models.IntegerField(null=True)

    created = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    modified = models.DateTimeField(null=True, blank=True, auto_now=True)

    class Meta:
        db_table = 'shop_memorule_rulememo'
        app_label = 'memorule'

    def __unicode__(self):
        return str(self.tid)


class ComposeRule(models.Model):
    RULE_PAYMENT_TYPE = pcfg.RULE_PAYMENT_TYPE
    RULE_SPLIT_TYPE = pcfg.RULE_SPLIT_TYPE
    RULE_GIFTS_TYPE = pcfg.RULE_GIFTS_TYPE

    DEFAULT_SELLER_CODE = 0
    PRODUCT_ALL = 'ALL'
    # 匹配规则
    outer_id = models.CharField(max_length=64, db_index=True,
                                blank=True, verbose_name=u'商品外部编码')
    outer_sku_id = models.CharField(max_length=64, db_index=True,
                                    blank=True, verbose_name=u'商品规格编码')

    seller_id = models.IntegerField(default=DEFAULT_SELLER_CODE, verbose_name=u'卖家ID')

    payment = models.IntegerField(null=True, default=0, verbose_name=u'金额')
    type = models.CharField(max_length=10,
                            choices=RULE_TYPE_CHOICE,
                            verbose_name=u'规则类型')

    gif_count = models.IntegerField(default=0, verbose_name=u'剩余名额')
    scb_count = models.IntegerField(default=0, verbose_name=u'已送名额')

    extra_info = models.TextField(blank=True, verbose_name=u'信息')

    start_time = models.DateTimeField(null=True, blank=True, verbose_name=u'开始时间')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name=u'结束时间')

    created = models.DateTimeField(null=True, blank=True, auto_now_add=True, verbose_name=u'创建时间')
    modified = models.DateTimeField(null=True, blank=True, auto_now=True, verbose_name=u'修改时间')

    status = models.BooleanField(default=False, verbose_name=u'生效')

    class Meta:
        db_table = 'shop_memorule_composerule'
        unique_together = ("outer_id", "outer_sku_id", "type")
        app_label = 'memorule'
        verbose_name = u'匹配规则'
        verbose_name_plural = u'拆分规则列表'

    def __unicode__(self):
        return str(self.id)

    def clean(self):
        for field in self._meta.fields:
            if isinstance(field, (models.CharField, models.TextField)):
                setattr(self, field.name, getattr(self, field.name).strip())


class ComposeItem(models.Model):
    # 匹配后拆分商品

    compose_rule = models.ForeignKey(ComposeRule,
                                     related_name="compose_items",
                                     verbose_name=u'商品规则')

    outer_id = models.CharField(max_length=64, db_index=True,
                                blank=True, verbose_name=u'组合商品外部编码')

    outer_sku_id = models.CharField(max_length=64, db_index=True,
                                    blank=True, verbose_name=u'组合商品规格编码')

    num = models.IntegerField(default=1, verbose_name=u'商品数量')
    extra_info = models.TextField(blank=True, verbose_name=u'信息')

    created = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    modified = models.DateTimeField(null=True, blank=True, auto_now=True)

    class Meta:
        db_table = 'shop_memorule_composeitem'
        app_label = 'memorule'
        verbose_name = u'拆分规则商品'
        verbose_name_plural = u'拆分规则商品列表'

    def __unicode__(self):
        return str(self.id)

    def get_item_cost(self):
        """ 获取单项成本 """
        cost = 0
        if self.outer_sku_id:
            prod_sku = ProductSku.objects.get(outer_id=self.outer_sku_id,
                                              product__outer_id=self.outer_id)
            cost = prod_sku.cost or 0
        else:
            prod = Product.objects.get(outer_id=self.outer_id)
            cost = prod.cost or 0
        return float(cost)

    def clean(self):
        for field in self._meta.fields:
            if isinstance(field, (models.CharField, models.TextField)):
                setattr(self, field.name, getattr(self, field.name).strip())


def rule_match_product(sender, trade_id, *args, **kwargs):
    # 匹配规则

    is_rule_match = False
    try:
        trade = MergeTrade.objects.get(id=trade_id)
    except Trade.DoesNotExist:
        pass
    else:
        orders = trade.merge_orders.filter(sys_status=pcfg.IN_EFFECT)
        for order in orders:
            outer_id = order.outer_id
            outer_sku_id = order.outer_sku_id
            prod_sku = None
            prod = None
            if outer_sku_id:
                try:
                    prod_sku = ProductSku.objects.get(product__outer_id=outer_id, outer_id=outer_sku_id)
                except:
                    continue
                else:
                    if not prod_sku.is_match:
                        continue
            else:
                try:
                    prod = Product.objects.get(outer_id=outer_id)
                except:
                    continue
                else:
                    if not prod.is_match:
                        continue
            is_rule_match = True
            order.is_rule_match = True
            order.save()

        if is_rule_match:
            raise Exception('订单商品有匹配')


rule_signal.connect(rule_match_product, sender='product_rule', dispatch_uid='rule_match_product')


def rule_match_trade(sender, trade_id, *args, **kwargs):
    try:
        trade = Trade.objects.get(id=trade_id)
    except Trade.DoesNotExist:
        pass
    else:
        orders = trade.trade_orders.exclude(refund_status__in=pcfg.REFUND_APPROVAL_STATUS)
        trade_rules = TradeRule.objects.filter(scope='trade', status='US')
        memo_list = []
        payment = 0
        trade_payment = 0
        for order in orders:
            payment = float(order.payment)
            trade_payment += payment
            item = Item.get_or_create(trade.user.visitor_id, order.num_iid)
            order_rules = item.rules.filter(scope='product', status='US')
            for rule in order_rules:
                try:
                    if eval(rule.formula):
                        memo_list.append(rule.memo)
                except Exception, exc:
                    logger.error('交易商品规则(%s)匹配出错'.decode('utf8') % rule.formula, exc_info=True)

        trade.payment = trade_payment
        for rule in trade_rules:
            try:
                if eval(rule.formula):
                    memo_list.append(rule.memo)
            except Exception, exc:
                logger.error('交易订单规则(%s)匹配出错'.decode('utf8') % rule.formula, exc_info=True)

        MergeTrade.objects.filter(id=trade_id).update(sys_memo=','.join(memo_list))


# rule_signal.connect(rule_match_trade,sender='trade_rule',dispatch_uid='rule_match_orders')


def rule_match_payment(sender, trade_id, *args, **kwargs):
    """
    赠品规则:
        1,针对实付订单，不能根据有效来计算，由于需拆分的实付订单拆分后会变成无效；
        2，赠品是根据最大匹配金额来赠送；
        3，该规则执行前，应先将所以满就送的订单删除；
    """
    try:
        trade = MergeTrade.objects.get(id=trade_id)
    except MergeTrade.DoesNotExist:
        pass
    else:
        trade.merge_orders.filter(gift_type=pcfg.OVER_PAYMENT_GIT_TYPE).delete()
        try:
            orders = trade.merge_orders.filter(gift_type=pcfg.REAL_ORDER_GIT_TYPE
                                               , status__in=(pcfg.WAIT_SELLER_SEND_GOODS, pcfg.WAIT_BUYER_CONFIRM_GOODS)
                                               ).exclude(refund_status=pcfg.REFUND_SUCCESS)

            payment = orders.aggregate(total_payment=Sum('payment'))['total_payment'] or 0
            post_fee = trade.post_fee or 0

            real_payment = payment - float(post_fee)
            self_rule = None
            payment_rules = ComposeRule.objects.filter(type='payment').order_by('-payment')
            for rule in payment_rules:
                if real_payment >= rule.payment and rule.gif_count > 0:
                    for item in rule.compose_items.all():
                        MergeOrder.gen_new_order(trade.id, item.outer_id, item.outer_sku_id, item.num,
                                                 gift_type=pcfg.OVER_PAYMENT_GIT_TYPE)
                        msg = u'交易金额匹配（实付:%s）' % str(real_payment)
                        log_action(trade.user.user.id, trade, CHANGE, msg)

                    ComposeRule.objects.filter(id=rule.id).update(gif_count=F('gif_count') - 1)
                    break

            MergeTrade.objects.filter(id=trade_id).update(order_num=orders.filter(sys_status=pcfg.IN_EFFECT).count(),
                                                          payment=payment)
        except Exception, exc:
            logger.error(exc.message or 'payment rule error', exc_info=True)
            trade.append_reason_code(pcfg.PAYMENT_RULE_ERROR_CODE)


rule_signal.connect(rule_match_payment, sender='payment_rule', dispatch_uid='rule_match_payment')


def rule_match_combose_split(sender, trade_id, *args, **kwargs):
    """
    拆分规则:
        1,针对实付订单，不能根据有效来计算，由于需拆分的实付订单拆分后会变成无效；
        2，赠品是根据最大匹配金额来赠送；
        3，该规则执行前，应先将所以满就送的订单删除；
    """
    try:
        trade = MergeTrade.objects.get(id=trade_id)
    except MergeTrade.DoesNotExist:
        pass
    else:
        trade.merge_orders.filter(gift_type=pcfg.COMBOSE_SPLIT_GIT_TYPE).delete()
        try:
            orders = trade.merge_orders.filter(gift_type=pcfg.REAL_ORDER_GIT_TYPE
                                               , status__in=(pcfg.WAIT_SELLER_SEND_GOODS,
                                                             pcfg.WAIT_BUYER_CONFIRM_GOODS)
                                               ).exclude(refund_status=pcfg.REFUND_SUCCESS)
            for order in orders:
                outer_id = order.outer_id
                outer_sku_id = order.outer_sku_id
                order_num = order.num
                order_payment = order.payment

                prod = Product.objects.getProductByOuterid(outer_id)
                prod_sku = Product.objects.getProductSkuByOuterid(outer_sku_id)
                if not (prod and prod.is_split) or not (prod_sku and prod_sku.is_split):
                    continue

                try:
                    compose_rule = ComposeRule.objects.get(outer_id=outer_id, outer_sku_id=outer_sku_id, type='product')
                except Exception, exc:
                    pass
                else:
                    items = compose_rule.compose_items.all()

                    total_cost = 0  # 计算总成本
                    for item in items:
                        total_cost += item.get_item_cost()

                    for item in items:
                        cost = item.get_item_cost()
                        payment = total_cost and str(round((cost / total_cost) * float(order_payment), 2)) or '0'
                        MergeOrder.gen_new_order(trade.id, item.outer_id, item.outer_sku_id, item.num * order_num,
                                                 gift_type=pcfg.COMBOSE_SPLIT_GIT_TYPE, payment=payment)
                    order.sys_status = pcfg.INVALID_STATUS
                    order.save()
                    msg = u'拆分订单商品(oid:%s)' % str(order.id)
                    log_action(trade.user.user.id, trade, CHANGE, msg)

        except Exception, exc:
            logger.error(exc.message or 'combose split error', exc_info=True)
            trade.append_reason_code(pcfg.COMPOSE_RULE_ERROR_CODE)


rule_signal.connect(rule_match_combose_split, sender='combose_split_rule', dispatch_uid='rule_match_combose_split')


def rule_match_gifts(sender, trade_id, *args, **kwargs):
    try:
        trade = MergeTrade.objects.get(id=trade_id)
    except MergeTrade.DoesNotExist:
        pass
    else:
        trade.merge_orders.filter(gift_type=pcfg.ITEM_GIFT_TYPE).delete()
        try:
            orders = trade.merge_orders.filter(gift_type=pcfg.REAL_ORDER_GIT_TYPE
                                               , status__in=(pcfg.WAIT_SELLER_SEND_GOODS,
                                                             pcfg.WAIT_BUYER_CONFIRM_GOODS)
                                               ).exclude(refund_status=pcfg.REFUND_SUCCESS)
            for order in orders:
                outer_id = order.outer_id
                outer_sku_id = order.outer_sku_id
                order_num = order.num

                prod = Product.objects.getProductByOuterid(outer_id)
                prod_sku = Product.objects.getProductSkuByOuterid(outer_sku_id)
                if not (prod and prod.is_split) or not (prod_sku and prod_sku.is_split):
                    continue

                try:
                    compose_rule = ComposeRule.objects.get(outer_id=outer_id,
                                                           outer_sku_id=outer_sku_id, type=ComposeRule.RULE_GIFTS_TYPE)
                except Exception, exc:
                    pass
                else:
                    rules = compose_rule.compose_items.all()

                    for rule in rules:
                        if rule.gif_count > 0:
                            MergeOrder.gen_new_order(trade.id,
                                                     rule.outer_id,
                                                     rule.outer_sku_id,
                                                     rule.num * order_num,
                                                     gift_type=pcfg.ITEM_GIFT_TYPE,
                                                     payment=0)

                            ComposeRule.objects.filter(id=rule.id).update(gif_count=F('gif_count') - 1)

                    msg = u'买(oid:%s)就送(%s)' % str(order.id,
                                                   ','.join(['%s-%s' % (r.outer_id, r.outer_sku_id) for r in rules]))
                    log_action(trade.user.user.id, trade, CHANGE, msg)

        except Exception, exc:
            logger.error(exc.message or 'combose split error', exc_info=True)
            trade.append_reason_code(pcfg.COMPOSE_RULE_ERROR_CODE)


rule_signal.connect(rule_match_gifts, sender='gifts_rule', dispatch_uid='rule_match_gifts')
