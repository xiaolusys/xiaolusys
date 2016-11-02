# -*- coding:utf8 -*-
import datetime
from django.db import models
from shopapp.signals import modify_fee_signal
from auth import apis


class FeeRule(models.Model):
    payment = models.FloatField(verbose_name='交易金额')
    discount = models.FloatField(default=1, verbose_name='邮费折扣')
    adjust_fee = models.FloatField(null=True, verbose_name='邮费调整金额')

    class Meta:
        db_table = 'shop_modifyfee_feerule'
        app_label = 'modifyfee'
        verbose_name = u'邮费规则'
        verbose_name_plural = u'邮费规则列表'

    def __unicode__(self):
        return '<%d,%s,%s,%s>' % (self.id, str(self.payment), str(self.discount), str(self.adjust_fee))


class ModifyFee(models.Model):
    id = models.AutoField(primary_key=True)
    tid = models.BigIntegerField(verbose_name='淘宝交易ID')
    buyer_nick = models.CharField(max_length=32, verbose_name='买家昵称')
    total_fee = models.CharField(max_length=10, verbose_name='订单金额')
    payment = models.CharField(max_length=10, verbose_name='实付金额')
    post_fee = models.CharField(max_length=10, verbose_name='实付邮费')
    modify_fee = models.CharField(max_length=10, verbose_name='修改邮费')
    modified = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'shop_modifyfee_modifyfee'
        app_label = 'modifyfee'
        verbose_name = u'邮费修改记录'
        verbose_name_plural = u'邮费修改记录列表'

    def __unicode__(self):
        return '<%d,%s,%s,%s>' % (self.id, self.name, self.payment, self.modify_fee)


def modify_post_fee_func(sender, user_id, trade_id, *args, **kwargs):
    from shopback.orders.models import Trade
    from shopback.trades.models import MergeTrade
    try:
        trade = Trade.get_or_create(trade_id, user_id)
    except:
        pass
    else:
        payment = float(trade.payment or '0')
        post_fee = float(trade.post_fee or '0')
        fee_rules = FeeRule.objects.order_by('-payment')
        for rule in fee_rules:
            if payment >= rule.payment:
                modify_fee = rule.adjust_fee if rule.adjust_fee != None else post_fee * (rule.discount or 1.0)
                response = apis.taobao_trade_postage_update(tid=trade_id,
                                                            post_fee=modify_fee,
                                                            tb_user_id=trade.user.visitor_id)
                postage = response['trade_postage_update_response']['trade']
                ModifyFee.objects.get_or_create(tid=trade_id,
                                                buyer_nick=trade.buyer_nick,
                                                total_fee=postage['total_fee'],
                                                post_fee=post_fee,
                                                modify_fee=postage['post_fee'],
                                                payment=postage['payment'],
                                                modified=postage['modified'])
                Trade.objects.filter(id=trade_id).update(total_fee=postage['total_fee'],
                                                         post_fee=postage['post_fee'],
                                                         payment=postage['payment'],
                                                         modified=postage['modified'])
                MergeTrade.objects.filter(tid=trade_id).update(total_fee=postage['total_fee'],
                                                               post_fee=postage['post_fee'],
                                                               payment=postage['payment'],
                                                               modified=postage['modified'])
                break


modify_fee_signal.connect(modify_post_fee_func, sender='modify_post_fee', dispatch_uid='modify_post_fee')
