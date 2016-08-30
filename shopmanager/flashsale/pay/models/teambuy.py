# -*- coding:utf-8 -*-
import datetime
from django.db import models
from core.models import AdminModel
from flashsale.pay.models import Customer, ModelProduct, SaleOrder, SaleTrade
from shopback.items.models import ProductSku, Product
from django.db.models.signals import post_save, pre_save
from flashsale.xiaolumm.models import XiaoluMama


class TeamBuy(AdminModel):
    sku = models.ForeignKey(ProductSku)
    share_xlmm = models.ForeignKey(XiaoluMama, default=None, verbose_name=u'分享的妈妈')
    # model_product = models.ForeignKey(ModelProduct)
    limit_time = models.DateTimeField(db_index=True, verbose_name=u"最迟成团时间")
    limit_days = models.IntegerField(default=3, verbose_name=u'限制天数')
    limit_person_num = models.IntegerField(default=3, verbose_name=u'成团人数')
    STATUS_CHOICES = ((0, u'开团'), (1, u'成团'), (2, u'失败'))
    status = models.IntegerField(default=0, verbose_name=u'状态')

    class Meta:
        db_table = 'flashsale_pay_teambuy'
        app_label = 'pay'
        verbose_name = u'团购'
        verbose_name_plural = u'团购列表'

    @staticmethod
    def create_or_join(saletrade, limit_days=3, limit_person_num=3):
        teambuy_id = saletrade.extras_info.get('teambuy_id', '')
        if TeamBuyDetail.objects.filter(tid=saletrade.tid).first():
            return
        saleorder = saletrade.sale_orders.first()
        if teambuy_id:
            teambuy = TeamBuy.objects.get(id=teambuy_id)
            new_teambuy = teambuy.details.count() >= teambuy.limit_person_num
        else:
            new_teambuy = True
        if new_teambuy:
            teambuy = TeamBuy(
                creator=saletrade.buyer_id,
                sku_id=saleorder.sku_id,
                limit_days=limit_days,
                limit_person_num=limit_person_num,
            )
            teambuy.limit_time = datetime.datetime.now() + datetime.timedelta(days=3)
            teambuy.save()
            if saletrade.extras_info['teambuy_id'] != teambuy.id:
                saletrade.extras_info['teambuy_id'] = teambuy.id
                saletrade.save()
        TeamBuyDetail(
            teambuy=teambuy,
            tid=saletrade.tid,
            oid=saleorder.oid,
            customer_id=saletrade.buyer_id,
            originizer=new_teambuy
        ).save()
        teambuy.check_finish_teambuy()

    def check_finish_teambuy(self):
        if self.details.count() >= self.limit_person_num:
            self.trigger_saleorder()
            self.set_status_success()

    def trigger_saleorder(self):
        from flashsale.pay.tasks import task_saleorder_update_package_sku_item
        oids = [o.oid for o in self.details.all()]
        for saleorder in SaleOrder.objects.filter(oid__in=oids):
            task_saleorder_update_package_sku_item(saleorder)

    def set_check(self):
        if self.details.count() >= self.limit_person_num:
            self.status = 1
        else:
            self.status = 2
        self.save()

    def set_status_success(self):
        self.status = 1
        self.save()

    def set_status_failed(self):
        self.status = 2
        self.save()
        for detail in self.details.all():
            SaleOrder.objects.get(oid=detail.oid).do_refund(u'开团失败')


def update_teambuy_status(sender, instance, created, **kwargs):
    if instance.status == 0:
        instance.check_finish_teambuy()


post_save.connect(update_teambuy_status, sender=TeamBuy, dispatch_uid='post_save_update_teambuy_status')


class TeamBuyDetail(models.Model):
    teambuy = models.ForeignKey(TeamBuy, related_name='details')
    tid = models.CharField(max_length=40, unique=True, verbose_name=u'订单tid')
    oid = models.CharField(max_length=40, unique=True, verbose_name=u'订单oid')
    customer = models.ForeignKey(Customer)
    originizer = models.BooleanField(default=False)

    class Meta:
        db_table = 'flashsale_pay_teambuy_detail'
        app_label = 'pay'
        verbose_name = u'团购详情'
        verbose_name_plural = u'团购详情列表'
