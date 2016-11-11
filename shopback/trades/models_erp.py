# encoding=utf8
from django.db import models
from core.models import BaseModel


class ErpOrder(BaseModel):

    SUCCESS = 'success'
    FAIL = 'fail'

    STATUS_CHOICES = (
        (SUCCESS, u'成功'),
        (FAIL, u'失败'),
    )

    CANCEL_TRADE = 'cancel_trade'
    PRE_TRADE = 'pre_trade'
    CHECK_TRADE = 'check_trade'
    FINANCE_TRADE = 'finance_trade'
    WAIT_SEND_TRADE = 'wait_send_trade'
    OVER_TRADE = 'over_trade'

    ORDER_STATUS = (
        (CANCEL_TRADE, u'已取消'),
        (PRE_TRADE, u'预订单'),
        (CHECK_TRADE, u'待审核'),
        (FINANCE_TRADE, u'待财审'),
        (WAIT_SEND_TRADE, u'待发货'),
        (OVER_TRADE, u'已完成'),
    )

    sale_order_oid = models.CharField(unique=True, max_length=32, verbose_name=u'订单oid')
    erp_order_id = models.CharField(max_length=32, verbose_name=u'ERP系统订单ID')
    package_sku_item_id = models.CharField(max_length=32, verbose_name=u'包裹sku_item_id')
    supplier_id = models.CharField(max_length=32, verbose_name=u'供应商ID')
    supplier_name = models.CharField(max_length=32, verbose_name=u'供应商名称')
    erp_type = models.CharField(max_length=16, default='wdt', verbose_name=u'ERP系统类型')
    sync_status = models.CharField(max_length=16, choices=STATUS_CHOICES, verbose_name=u'同步状态')
    sync_result = models.TextField(max_length=2048, blank=True, default='', verbose_name=u'同步结果')
    order_status = models.CharField(max_length=16, choices=ORDER_STATUS, default=CHECK_TRADE, verbose_name=u'订单状态')
    logistics_code = models.CharField(max_length=16, verbose_name=u'物流公司编号')
    logistics_name = models.CharField(max_length=16, verbose_name=u'物流公司名称')
    post_id = models.CharField(max_length=16, verbose_name=u'物流编号')
    delivery_time = models.DateTimeField(verbose_name=u'发货时间')

    class Meta:
        db_table = 'shop_trades_erp_orders'
        app_label = 'trades'

    def update_logistics(self, logistics_code, logistics_name, post_id, delivery_time):
        self.order_status = self.OVER_TRADE
        self.logistics_code = logistics_code
        self.logistics_name = logistics_name
        self.post_id = post_id
        self.delivery_time = delivery_time
        self.save()
