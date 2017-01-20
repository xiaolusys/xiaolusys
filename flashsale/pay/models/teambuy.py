# -*- coding:utf-8 -*-
from __future__ import unicode_literals

import datetime
import urlparse
from django.db import models
from core.models import AdminModel, BaseModel
from flashsale.pay.models import Customer, ModelProduct, SaleOrder, SaleTrade
from shopback.items.models import Product
from .product import ProductSku
from django.db.models.signals import post_save, pre_save
from django.conf import settings


class TeamBuy(AdminModel):
    sku = models.ForeignKey(ProductSku)
    share_xlmm_id = models.IntegerField(default=None, null=True, verbose_name=u'分享的妈妈')
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
    def create_or_join(saletrade):
        teambuy_id = saletrade.extras_info.get('teambuy_id', '')
        if TeamBuyDetail.objects.filter(tid=saletrade.tid).first():
            return
        saleorder = saletrade.sale_orders.first()
        if teambuy_id:
            teambuy = TeamBuy.objects.get(id=teambuy_id)
            new_teambuy = teambuy.details.count() >= teambuy.limit_person_num
            if not new_teambuy and TeamBuyDetail.objects.filter(teambuy=teambuy,
                                            customer_id=saletrade.buyer_id).exists():
                new_teambuy = True
        else:
            new_teambuy = True
        if new_teambuy:
            p = Product.objects.get(id=saletrade.sale_orders.first().item_id)
            model_product = p.get_product_model()
            teambuy = TeamBuy(
                creator=saletrade.buyer_id,
                sku_id=saleorder.sku_id,
                limit_days=1, #model_product.limit_days, 目前限制全部是1天
                limit_person_num=model_product.teambuy_person_num,
            )
            teambuy.limit_time = datetime.datetime.now() + datetime.timedelta(days=1)
            buyer_id = saletrade.buyer_id
            customer = Customer.objects.filter(id=buyer_id).first()
            xlmm = customer.get_xiaolumm()
            if xlmm and xlmm.is_available():
                mama_id = xlmm.id
            else:
                mama_id = saletrade.extras_info.get('mm_linkid', '')
            if mama_id:
                teambuy.share_xlmm_id = mama_id
            teambuy.save()
        TeamBuyDetail(
            teambuy=teambuy,
            tid=saletrade.tid,
            oid=saleorder.oid,
            customer_id=saletrade.buyer_id,
            originizer=new_teambuy
        ).save()
        if saletrade.extras_info.get('teambuy_id', '') != teambuy.id:
            saletrade.extras_info['teambuy_id'] = teambuy.id
            saletrade.save()
        teambuy.check_finish_teambuy()

    def check_finish_teambuy(self):
        if TeamBuyDetail.objects.filter(teambuy_id=self.id).count() >= self.limit_person_num:
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
        self.trigger_saleorder()
        from shopapp.weixin.tasks import task_pintuan_success_push
        task_pintuan_success_push.delay(self)  # 拼团成功微信推送

    def set_status_failed(self):
        from shopback.trades.models import PackageSkuItem
        # from shopback.warehouse.constants import WARE_THIRD
        from flashsale.pay.constants import BUDGET
        self.status = 2
        oids = []
        for detail in self.details.all():
            saleorder = detail.saleorder
            salerefund = saleorder.do_refund(desc=u'开团失败', refund_channel=BUDGET)
            if not salerefund.is_postrefund:  # and not saleorder.product.ware_by == WARE_THIRD:  # 不是发货后　不是第三方仓库
                psi = PackageSkuItem.objects.filter(oid=saleorder.oid).first()
                if psi and psi.is_booked():  # 已经订货 不做退款操作
                    pass
                else:   # 没有订货　则退款给用户
                    salerefund.refund_approve()  # 退款给用户
            oids.append(detail.oid)
        PackageSkuItem.objects.filter(oid__in=oids).update(assign_status=3)
        if len(oids) == 0:
            raise Exception(u'此团购名下没有订单')
        self.save()
        from shopapp.weixin.tasks import task_pintuan_fail_push
        task_pintuan_fail_push.delay(self)  # 拼团失败微信推送

    def get_shareparams(self, **params):
        if self.share_xlmm_id:
            share_link = '/mall/order/spell/group/' + str(self.id) + '?mm_linkid=' + str(self.share_xlmm_id) + '&from_page=share'
        else:
            share_link = '/mall/order/spell/group/' + str(self.id) + '?from_page=share'

        share_link = urlparse.urljoin(settings.M_SITE_URL, share_link)
        return {
            'id': self.id,
            'title': u'一起来团购 %s' %(self.sku.product.name,),
            'share_type': 'link',
            'share_icon': self.sku.product.pic_path,
            'share_link': share_link,
            'active_dec': u'我在小鹿美美发现一个好东西,团购更便宜,一起来拼团吧.',
        }

    def get_qrcode_page_link(self, **params):
        from core.upload.xqrcode import push_qrcode_to_remote
        qrcode_link = '/mall/order/spell/group/%d?from_page=share' % (self.id,)
        if self.share_xlmm_id:
            qrcode_link += '&mm_linkid=' + str(self.share_xlmm_id)
        qrcode_link = urlparse.urljoin(settings.M_SITE_URL, qrcode_link)
        print qrcode_link
        return push_qrcode_to_remote('teambuy_' + str(self.id), qrcode_link)

    def get_creator(self):
        """
        获取团长
        """
        customer = Customer.objects.filter(id=self.creator).first()
        return customer

    @staticmethod
    def end_teambuy(sku):
        for teambuy in TeamBuy.objects.filter(status=0, sku=sku):
            if teambuy.details.count() >= teambuy.limit_person_num:
                teambuy.set_status_success()
            else:
                teambuy.set_status_failed()


def update_teambuy_status(sender, instance, created, **kwargs):
    if instance.status == 0:
        instance.check_finish_teambuy()


post_save.connect(update_teambuy_status, sender=TeamBuy, dispatch_uid='post_save_update_teambuy_status')


class TeamBuyDetail(BaseModel):
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

    @property
    def saleorder(self):
        if not hasattr(self, '_sale_order_'):
            from flashsale.pay.models import SaleOrder

            self._sale_order_ = SaleOrder.objects.filter(oid=self.oid).first()
        return self._sale_order_
