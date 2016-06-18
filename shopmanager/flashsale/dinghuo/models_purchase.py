# -*- coding:utf-8 -*-
from django.db import models
from django.db.models.signals import post_save

from core.models import BaseModel


class PurchaseOrder(BaseModel):
    OPEN = 1
    BOOKED = 2
    FINISHED = 3
    CANCELED = 4
    
    STATUS = ((OPEN, 'OPEN'),(BOOKED,'BOOKED'),(FINISHED,'FINISHED'),(CANCELED,'CANCELED'))

    uni_key = models.CharField(max_length=32, db_index=True, blank=True, verbose_name=u'订货单唯一ID')

    supplier_id = models.IntegerField(default=0, verbose_name=u'Supplier ID')
    supplier_name = models.CharField(max_length=128, verbose_name=u'Supplier名称')

    book_num = models.IntegerField(default=0, verbose_name=u'Book数量')
    need_num = models.IntegerField(default=0, verbose_name=u'Need数量')
    #extra_num = models.IntegerField(default=0, verbose_name=u'Extra数量')
    arrival_num = models.IntegerField(default=0, verbose_name=u'Arrival数量')
    inferior_num = models.IntegerField(default=0, verbose_name=u'次品数量')

    total_price = models.IntegerField(default=0, verbose_name=u'总价')
    
    status =  models.IntegerField(choices=STATUS,default=OPEN,db_index=True, verbose_name=u'状态')
    

    class Meta:
        db_table = 'flashsale_dinghuo_purchase_order'
        app_label = 'dinghuo'
        verbose_name = u'v2/订货'
        verbose_name_plural = u'v2/订货表'


class PurchaseDetail(BaseModel):
    uni_key = models.CharField(max_length=32, unique=True, verbose_name=u'唯一id ') #sku_id+purchase_order_unikey
    purchase_order_unikey = models.CharField(max_length=32, db_index=True, blank=True, verbose_name=u'订货单唯一ID')

    outer_id = models.CharField(max_length=20, blank=True, verbose_name=u'商品编码')
    outer_sku_id = models.CharField(max_length=20, blank=True, verbose_name=u'规格ID')
    
    sku_id = models.CharField(db_index=True, max_length=32, verbose_name=u'sku商品id')
    title = models.CharField(max_length=128, verbose_name=u'产品名称')
    sku_properties_name = models.CharField(max_length=16, blank=True, verbose_name=u'购买规格') #sku level info (size)

    book_num = models.IntegerField(default=0, verbose_name=u'Book数量')
    need_num = models.IntegerField(default=0, verbose_name=u'Need数量')
    extra_num = models.IntegerField(default=0, verbose_name=u'Extra数量')
    arrival_num = models.IntegerField(default=0, verbose_name=u'Arrival数量')
    inferior_num = models.IntegerField(default=0, verbose_name=u'次品数量')
    
    status =  models.IntegerField(choices=PurchaseOrder.STATUS,default=PurchaseOrder.OPEN,db_index=True, verbose_name=u'状态')
    
    unit_price = models.IntegerField(default=0, verbose_name=u'买入价格')
    total_price = models.IntegerField(default=0, verbose_name=u'单项总价')
    

    class Meta:
        db_table = 'flashsale_dinghuo_purchase_detail'
        app_label = 'dinghuo'
        verbose_name = u'v2/订货明细'
        verbose_name_plural = u'v2/订货明细表'

    def __unicode__(self):
        return "%s-%s/%s" % (self.id, self.title, self.sku_properties_name)

    @property
    def unit_price_display(self):
        return float('%.2f' % (self.unit_price * 0.01))

    @property
    def total_price_display(self):
        total = self.unit_price * self.book_num * 0.01
        return float('%.2f' % total)
    
    def has_extra(self):
        return self.status == PurchaseOrder.BOOKED and self.book_num > self.need_num

    def is_open(self):
        return self.status == PurchaseOrder.OPEN

    def is_booked(self):
        return self.status == PurchaseOrder.BOOKED


def update_purchase_order(sender, instance, created, **kwargs):
    from flashsale.dinghuo.tasks import task_purchase_detail_update_purchase_order
    task_purchase_detail_update_purchase_order.delay(instance)

post_save.connect(update_purchase_order, sender=PurchaseDetail, dispatch_uid='post_save_update_purchase_order')

    
def check_arrangement(sender, instance, created, **kwargs):
    if not instance.has_extra():
        return

    from flashsale.dinghuo.tasks import task_check_arrangement
    task_check_arrangement.delay(instance)
    
post_save.connect(check_arrangement, sender=PurchaseDetail, dispatch_uid='post_save_check_arrangement')


def update_orderdetail(sender, instance, created, **kwargs):
    from flashsale.dinghuo.tasks import task_purchasedetail_update_orderdetail
    task_purchasedetail_update_orderdetail.delay(instance)
    
post_save.connect(update_orderdetail, sender=PurchaseDetail, dispatch_uid='post_save_update_orderdetail')



class PurchaseRecord(BaseModel):
    EFFECT = 1
    CANCEL = 2
    STATUS = ((EFFECT, u'有效'),(CANCEL, u'取消'))

    package_sku_item_id = models.IntegerField(default=0,db_index=True, verbose_name=u'包裹ID')
    oid =  models.CharField(max_length=32,db_index=True, verbose_name=u'sku交易单号')

    uni_key = models.CharField(max_length=32, unique=True, verbose_name=u'唯一id ') #sale_order_id + num_of_purchase_try
    #purchase_order_unikey =  models.CharField(max_length=32, db_index=True, blank=True, verbose_name=u'订货单唯一id')

    outer_id = models.CharField(max_length=32, db_index=True, verbose_name=u'产品外部编码') #color-level code
    outer_sku_id = models.CharField(max_length=32, blank=True, verbose_name=u'规格ID') #size-level code

    sku_id = models.CharField(max_length=32, db_index=True, verbose_name=u'sku商品id') #sku-level id
    title = models.CharField(max_length=128, verbose_name=u'颜色级产品名称') #color-level product name
    sku_properties_name = models.CharField(max_length=16, blank=True, verbose_name=u'购买规格') #sku level info (size)

    request_num = models.IntegerField(default=0, verbose_name=u'Request量')
    book_num = models.IntegerField(default=0, verbose_name=u'订购量')
    
    status =  models.IntegerField(choices=STATUS,default=EFFECT,db_index=True, verbose_name=u'状态')
    note = models.CharField(max_length=128, blank=True, verbose_name=u'备注信息')
    
    class Meta:
        db_table = 'flashsale_dinghuo_purchase_record'
        app_label = 'dinghuo'
        verbose_name = u'v2/订单订货记录'
        verbose_name_plural = u'v2/订单订货记录表'        

    def __unicode__(self):
        return "%s-%s/%s" % (self.id, self.title, self.sku_properties_name)

    @property
    def need_num(self):
        if self.request_num > self.book_num:
            return self.request_num - self.book_num
        return 0

    def need_booking(self):
        if self.status == PurchaseRecord.EFFECT and self.book_num < self.request_num:
            return True
        return False

    def is_booked(self):
        return self.book_num > 0
    
    def is_overbooked(self):
        return self.book_num > self.request_num and self.status == PurchaseRecord.EFFECT


def sync_purchase_arrangement(sender, instance, created, **kwargs):
    if not instance.is_booked():
        return

    from flashsale.dinghuo.tasks import task_purchaserecord_sync_purchasearrangement_status
    task_purchaserecord_sync_purchasearrangement_status.delay(instance)        

post_save.connect(sync_purchase_arrangement, sender=PurchaseRecord, dispatch_uid='post_save_sync_purchase_arrangement')


def adjust_purchase_arrangement_overbooking(sender, instance, created, **kwargs):
    """
    """
    if not instance.is_overbooked():
        return
    
    from flashsale.dinghuo.tasks import task_purchaserecord_adjust_purchasearrangement_overbooking
    task_purchaserecord_adjust_purchasearrangement_overbooking.delay(instance)

post_save.connect(adjust_purchase_arrangement_overbooking, sender=PurchaseRecord, dispatch_uid='post_save_adjust_purchase_arrangement_overbooking')


def start_booking(sender, instance, created, **kwargs):
    """
    """
    if not instance.need_booking():
        return
    
    from flashsale.dinghuo.tasks import task_start_booking
    task_start_booking.delay(instance)


post_save.connect(start_booking, sender=PurchaseRecord, dispatch_uid='post_save_start_booking')


class PurchaseArrangement(BaseModel):
    package_sku_item_id = models.IntegerField(default=0,db_index=True, verbose_name=u'包裹ID')
    oid =  models.CharField(max_length=32,db_index=True, verbose_name=u'sku交易单号')

    #PurchaseRecord.uni_key + purchase_order_unikey
    uni_key = models.CharField(max_length=32, unique=True, verbose_name=u'唯一id ')
    purchase_order_unikey =  models.CharField(max_length=32, db_index=True, blank=True, verbose_name=u'订货单唯一id')
    purchase_record_unikey = models.CharField(max_length=32, db_index=True, blank=True, verbose_name=u'PR唯一id')
    
    outer_id = models.CharField(max_length=32, db_index=True, verbose_name=u'产品外部编码') #color-level code
    outer_sku_id = models.CharField(max_length=32, blank=True, verbose_name=u'规格ID') #size-level code

    sku_id = models.CharField(max_length=32, db_index=True, verbose_name=u'sku商品id') #sku-level id
    title = models.CharField(max_length=128, verbose_name=u'颜色级产品名称') #color-level product name
    sku_properties_name = models.CharField(max_length=16, blank=True, verbose_name=u'购买规格') #sku level info (size)

    num =  models.IntegerField(default=0, verbose_name=u'订购量')
    status =  models.IntegerField(choices=PurchaseRecord.STATUS,default=PurchaseRecord.EFFECT,db_index=True, verbose_name=u'状态')
    purchase_order_status = models.IntegerField(choices=PurchaseOrder.STATUS,default=PurchaseOrder.OPEN,db_index=True, verbose_name=u'PO状态')
    initial_book =  models.BooleanField(default=False,db_index=True, verbose_name=u'是否已订货')
    
    class Meta:
        db_table = 'flashsale_dinghuo_purchase_arrangement'
        app_label = 'dinghuo'
        verbose_name = u'v2/订货分配记录'
        verbose_name_plural = u'v2/订货分配表'        

    def __unicode__(self):
        return "%s-%s/%s" % (self.id, self.title, self.sku_properties_name)

def update_purchase_detail(sender, instance, created, **kwargs):
    from flashsale.dinghuo.tasks import task_purchasearrangement_update_purchasedetail
    task_purchasearrangement_update_purchasedetail.delay(instance)

post_save.connect(update_purchase_detail, sender=PurchaseArrangement, dispatch_uid='post_save_update_purchase_detail')


def update_purchase_record_book_num(sender, instance, created, **kwargs):
    
    from flashsale.dinghuo.tasks import task_purchasearrangement_update_purchaserecord_book_num
    task_purchasearrangement_update_purchaserecord_book_num.delay(instance)

post_save.connect(update_purchase_record_book_num, sender=PurchaseArrangement, dispatch_uid='post_save_update_purchase_record_book_num')

    


