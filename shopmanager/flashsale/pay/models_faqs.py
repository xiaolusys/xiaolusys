# coding=utf-8

from django.db import models
from core.models import BaseModel


class SaleFaqs(BaseModel):
    OTHER = 0
    SALE = 1
    TRADE = 2
    AGENCY = 3

    QUESTION_TYPE = ((SALE, u'购物问题'), (TRADE, u'订单问题'), (AGENCY, u'代理问题'), (OTHER, u'其他问题'))

    LOGISTICS = 0
    AFTER_SALE = 1
    SALES_RETURN = 2
    SALES_REFUND = 3

    MAMA_JOIN = 4
    MAMA_OUT = 5
    CARRY_Q = 6
    ACTIVE_Q = 7

    TRADE_MODIFY = 8
    SALE_CHOOSE = 9
    PAY_TRADE = 10
    PAY_PRIVILEGE = 11

    XL_WALLET = 12
    ACCOUNT = 13
    MY_COUPON = 14
    COMPLAINT = 15

    DETAIL_TYPE = ((LOGISTICS, u'物流配送'), (AFTER_SALE, u'售后咨询'), (SALES_RETURN, u'退货问题'), (SALES_REFUND, u'退款问题'),

                   (MAMA_JOIN, u'招募问题'), (MAMA_OUT, u'退出问题'), (CARRY_Q, u'佣金问题'), (ACTIVE_Q, u'活动问题'),

                   (TRADE_MODIFY, u'订单修改'), (SALE_CHOOSE, u'选购商品'), (PAY_TRADE, u'结算支付'), (PAY_PRIVILEGE, u'特卖优惠'),

                   (XL_WALLET, u'小鹿钱包'), (ACCOUNT, u'帐号问题'), (MY_COUPON, u'我的卡券'), (COMPLAINT, u'投诉与建议'))

    question_type = models.IntegerField(choices=QUESTION_TYPE, default=0, db_index=True, verbose_name=u'主分类')
    detail_type = models.IntegerField(choices=DETAIL_TYPE, default=0, db_index=True, verbose_name=u'详细分类')
    question = models.CharField(max_length=256, verbose_name=u'问题')
    answer = models.TextField(max_length=10240, verbose_name=u'回答')

    class Meta:
        db_table = 'flashsale_sale_faqs'
        verbose_name = u'特卖/常见问题表'
        verbose_name_plural = u'特卖/常见问题表'

    def __unicode__(self):
        return u'<%s,%s>' % (self.id, self.question_type)
