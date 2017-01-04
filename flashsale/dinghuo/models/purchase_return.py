# -*- coding:utf-8 -*-
from __future__ import unicode_literals

import datetime
import random
from django.db import models
from django.db.models import Sum, Count, F, Q
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from core.models import BaseModel
from shopback.items.models import ProductSku, Product, SkuStock
from supplychain.supplier.models import SaleSupplier, SaleProduct
from .purchase_order import OrderList
from flashsale.pay.models import UserAddress
import logging

logger = logging.getLogger(__name__)


class ReturnGoods(models.Model):
    CREATE_RG = 0
    VERIFY_RG = 1
    OBSOLETE_RG = 2
    DELIVER_RG = 3
    REFUND_RG = 31
    SUCCEED_RG = 4
    FAILED_RG = 5
    MEMO_DEFAULT = u'\u6536\u4ef6\u4eba:\r\n\u624b\u673a/\u7535\u8bdd:\r\n\u6536\u4ef6\u5730\u5740:'
    RG_STATUS = ((CREATE_RG, u"新建"), (VERIFY_RG, u"已审核"), (OBSOLETE_RG, u"已作废"),
                 (DELIVER_RG, u"已发货"), (REFUND_RG, u"待验退款"),
                 (SUCCEED_RG, u"退货成功"), (FAILED_RG, u"退货失败"))
    product_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u"退货商品id")
    # supplier_id = models.IntegerField(db_index=True, verbose_name=u"供应商id")
    supplier = models.ForeignKey(SaleSupplier, null=True, verbose_name=u"供应商")
    return_num = models.IntegerField(default=0, verbose_name=u"退件总数")
    sum_amount = models.FloatField(default=0.0, verbose_name=u"计划退款总额")
    plan_amount = models.FloatField(default=0.0, verbose_name=u"计划退款总额")
    real_amount = models.FloatField(default=0.0, verbose_name=u"实际退款额")
    # confirm_pic_url = models.FileField(blank=True, verbose_name=u"付款截图")
    confirm_pic_url = models.URLField(blank=True, verbose_name=u"付款截图")
    upload_time = models.DateTimeField(null=True, verbose_name=u"上传截图时间")
    refund_fee = models.FloatField(default=0.0, verbose_name=u"客户退款额")
    confirm_refund = models.BooleanField(default=False, verbose_name=u"退款额确认")
    refund_confirmer_id = models.IntegerField(default=None, null=True, verbose_name=u"退款额确认人")
    transactor_id = models.IntegerField(default=None, null=True, db_index=True, verbose_name=u"处理人id")
    # transactor_id = models.IntegerField(choices=[(i.id, i.username) for i in return_goods_transcations()], default=None,
    #                                     null=True, db_index=True, verbose_name=u"处理人id")
    # transactor = models.ForeignKey(User, choices=ReturnGoods.transactors, null=True, verbose_name=u"处理人id")
    transaction_number = models.CharField(default='', max_length=64, verbose_name=u"交易单号")
    noter = models.CharField(max_length=32, verbose_name=u"录入人")
    consigner = models.CharField(max_length=32, blank=True, verbose_name=u"发货人")

    consign_time = models.DateTimeField(blank=True, null=True, verbose_name=u'发货时间')
    sid = models.CharField(max_length=64, null=True, blank=True, verbose_name=u"发货物流单号")
    logistics_company_id = models.BigIntegerField(null=True, verbose_name='物流公司ID')
    # logistics_company = models.ForeignKey(LogisticsCompany, null=True, blank=True, verbose_name=u'物流公司')
    status = models.IntegerField(default=0, choices=RG_STATUS, db_index=True, verbose_name=u"状态")
    TYPE_COMMON = 0
    TYPE_CHANGE = 1
    type = models.IntegerField(default=0, choices=((TYPE_COMMON, u'退货回款'), (TYPE_CHANGE, u'退货更换')),
                               verbose_name=u'退货类型')
    REFUND_STATUS = ((0, u"未付"), (1, u"已完成"), (2, u"部分支付"), (3, u"已关闭"))
    refund_status = models.IntegerField(default=0, choices=REFUND_STATUS, db_index=True, verbose_name=u"退款状态")
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'生成时间')
    modify = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    memo = models.TextField(max_length=512,
                            blank=True,
                            default=MEMO_DEFAULT,
                            verbose_name=u"退货备注")

    class Meta:
        db_table = 'flashsale_dinghuo_returngoods'
        app_label = 'dinghuo'
        verbose_name = u'仓库退货单'
        verbose_name_plural = u'仓库退货单列表'

    @property
    def sku_ids(self):
        if not hasattr(self, '_sku_ids_'):
            self._sku_ids_ = [i['skuid'] for i in self.rg_details.values('skuid')]
        return self._sku_ids_

    def is_supplier_addr(self):
        supplier_id = self.supplier.id
        user_address = UserAddress.objects.filter(supplier_id=supplier_id).first()
        if user_address:
            return True
        else:
            return False

    def is_supplier_addr_incomplete(self):
        supplier_id = self.supplier.id
        user_address = UserAddress.objects.filter(supplier_id=supplier_id).first()
        if all([user_address.supplier_id,user_address.receiver_name,user_address.receiver_state,
               user_address.receiver_city,user_address.receiver_district,user_address.receiver_address,user_address.receiver_mobile]):
            return True
        else:
            return False

    @property
    def product_skus(self):
        if not hasattr(self, '_product_skus_'):
            self._product_skus_ = ProductSku.objects.filter(id__in=self.sku_ids)
        return self._product_skus_

    @property
    def products(self):
        if not hasattr(self, '_products_'):
            self._products_ = Product.objects.filter(prod_skus__id__in=self.sku_ids).distinct()
        return self._products_

    @property
    def logistics_company(self):
        if not hasattr(self, '_logistics_company_'):
            from shopback.logistics.models import LogisticsCompany
            self._logistics_company_ = LogisticsCompany.objects.get(id=self.logistics_company_id)
        return self._logistics_company_

    @property
    def transactor(self):
        if not hasattr(self, '_transactor_'):
            self._transactor_ = User.objects.get(id=self.transactor_id)
        return self._transactor_

    def products_item_sku(self):
        products = self.products
        for sku in self.product_skus:
            for product in products:
                if sku.product_id == product.id:
                    if not hasattr(product, 'detail_skus'):
                        product.detail_skus = []
                    product.detail_skus.append(sku)
                    break
                    continue
        for product in products:
            product.detail_sku_ids = [sku.id for sku in product.detail_skus]
            product.detail_length = len(product.detail_sku_ids)

        for detail in self.rg_details.all():
            for product in products:
                if detail.skuid in product.detail_sku_ids:
                    if not hasattr(product, 'detail_items'):
                        product.detail_items = []
                    product.detail_items.append(detail)
        return products

    @staticmethod
    def generate(sku_dict, noter, days=10):
        """
            产生sku
        :param sku_dict:
        :param noter:
        :return:
        """
        product_sku_dict = dict([(p.id, p) for p in ProductSku.objects.filter(id__in=sku_dict.keys())])
        supplier = {}
        for sku_id in product_sku_dict:
            if sku_dict[sku_id] > 0 and \
                    ReturnGoods.can_return(sku=sku_id):
                sku = product_sku_dict[sku_id]
                # if sku.product.offshelf_time<datetime.datetime.now()- datetime.timedelta(days=12):
                detail = RGDetail(
                    skuid=sku_id,
                    num=sku_dict[sku_id],
                    price=sku.cost,
                )
                if sku.product.sale_product_item:
                    supplier_id = sku.product.sale_product_item.sale_supplier_id
                    if supplier_id not in supplier:
                        supplier[supplier_id] = []
                    supplier[supplier_id].append(detail)
        res = []
        for supplier_id in supplier:
            if ReturnGoods.can_return(supplier_id=supplier_id,days=days):
                rg_details = supplier[supplier_id]
                ReturnGoods.objects.filter(supplier_id=supplier_id,type=0,status=0).update(status=2)
                rg = ReturnGoods(supplier_id=supplier_id,
                                 noter=noter,
                                 return_num=sum([d.num for d in rg_details]),
                                 sum_amount=sum([d.num * d.price for d in rg_details])
                                 )
                rg.transactor_id = ReturnGoods.get_user_by_supplier(supplier_id)
                rg.save()
                details = []
                for detail in supplier[supplier_id]:
                    detail.return_goods = rg
                    detail.return_goods_id = rg.id
                    details.append(detail)
                RGDetail.objects.bulk_create(details)
                res.append(rg)
        return res

    @staticmethod
    def generate_by_inbound(inbound, noter):
        if not inbound.wrong and not inbound.out_stock:
            raise Exception(u'此入库单无错货多货无法生成退货单')
        supplier_id = inbound.supplier_id
        rg_details = []
        # inbounddetail 中存在sku_id=0的情况，为了防止异常
        for detail in inbound.details.filter(Q(out_stock=True) | Q(inferior_quantity__gt=0)).exclude(wrong=False):
            rg_detail = RGDetail(
                skuid=detail.sku_id,
                num=detail.out_stock_cnt,
                inferior_num=detail.inferior_quantity,
                price=0,
                type=RGDetail.TYPE_CHANGE,
                src=inbound.id
            )
            rg_details.append(rg_detail)
            rg_details.append(rg_detail)
        rg = ReturnGoods(supplier_id=supplier_id,
                         noter=noter,
                         return_num=sum([d.num for d in rg_details]),
                         sum_amount=sum([d.num * d.price for d in rg_details]),
                         type=ReturnGoods.TYPE_CHANGE
                         )
        rg.save()
        details = []
        for detail in rg_details:
            detail.return_goods = rg
            detail.return_goods_id = rg.id
            details.append(detail)
        RGDetail.objects.bulk_create(details)
        return rg

    @staticmethod
    def generate_by_supplier(supplier_id, noter):
        """
            重新生成供应商的所有退货单，自动作废未审核的退货单，提示手工作废已审核的退货单
        :param supplier_id:
        :return:
        """
        from flashsale.dinghuo.models.inbound import InBound, InBoundDetail
        inbounds = InBound.objects.filter(supplier_id=supplier_id).exclude(
            status__in=[InBound.COMPLETE_RETURN, InBound.INVALID])
        inbound_ids = [i.id for i in inbounds]
        rg_details = []
        return_inbound_ids = []
        # inbounddetail 中存在sku_id=0的情况，为了防止异常
        for detail in InBoundDetail.objects.filter(inbound_id__in=inbound_ids).filter(
                        Q(out_stock=True) | Q(inferior_quantity__gt=0)):  # | Q(wrong=True)):
            rg_detail = RGDetail(
                skuid=detail.sku_id,
                num=detail.out_stock_cnt,
                inferior_num=detail.inferior_quantity,
                price=0,
                type=RGDetail.TYPE_CHANGE,
                src=detail.inbound_id
            )
            if detail.wrong:
                rg_detail.wrong_desc = detail.memo
            rg_details.append(rg_detail)
            return_inbound_ids.append(detail.inbound_id)
        if not rg_details:
            return
        rg = ReturnGoods(supplier_id=supplier_id,
                         noter=noter,
                         return_num=sum([d.num for d in rg_details]),
                         sum_amount=sum([d.num * d.price for d in rg_details]),
                         type=ReturnGoods.TYPE_CHANGE
                         )
        rg.save()
        details = []
        for detail in rg_details:
            detail.return_goods = rg
            detail.return_goods_id = rg.id
            details.append(detail)
        InBound.objects.filter(id__in=return_inbound_ids).update(status=InBound.COMPLETE_RETURN, return_goods_id=rg.id)
        inbounds.exclude(id__in=return_inbound_ids).update(status=InBound.COMPLETE_RETURN)
        RGDetail.objects.bulk_create(details)
        return rg

    @staticmethod
    def can_return(supplier_id=None, sku=None, days=0):

        """
            近七天内没有有效退货单
            且    RG_STATUS = ((CREATE_RG, u"新建"), (VERIFY_RG, u"已审核"), (OBSOLETE_RG, u"已作废"),
                 (DELIVER_RG, u"已发货"), (REFUND_RG, u"待验退款"),
                 (SUCCEED_RG, u"退货成功"), (FAILED_RG, u"退货失败"))
            不在不可退货商品列表中
        :param supplier_id:
        :return:
        """
        # if supplier_id:
        #     return not ReturnGoods.objects.filter(supplier_id=supplier_id,
        #                                           status__in=[ReturnGoods.CREATE_RG, ReturnGoods.VERIFY_RG,
        #                                                       ReturnGoods.DELIVER_RG, ReturnGoods.REFUND_RG,
        #                                                       ReturnGoods.SUCCEED_RG]).exists()

        # if supplier_id:
        #     supplier = SaleSupplier.objects.get(id=supplier_id)
        #     if ReturnGoods.objects.filter(supplier_id=supplier_id, status__in=[ReturnGoods.CREATE_RG,
        #                                                                        ReturnGoods.VERIFY_RG]).exists():
        #         return False
        #     sale_product_ids = [i["id"] for i in supplier.supplier_products.values("id")]
        #     product_ids = [p["id"] for p in Product.objects.filter(sale_product__in=sale_product_ids).values("id")]
        #     unreturn_sku_ids = [i["sku_id"] for i in supplier.unreturnsku_set.values("sku_id")]
        #     return SkuStock.objects.filter(product__id__in=product_ids,
        #                                           product__offshelf_time__lt=datetime.datetime.now() - datetime.timedelta(
        #                                               days),
        #                                           sold_num__lt=F('history_quantity') + F('adjust_quantity') + F(
        #                                               'inbound_quantity') + F(
        #                                               'return_quantity') \
        #                                                        - F('rg_quantity')).exclude(
        #         sku__id__in=unreturn_sku_ids).exists()
        #
        # if sku:
        #     not_in_unreturn = not UnReturnSku.objects.filter(sku_id=sku, status=UnReturnSku.EFFECT).exists()
        #     onshelf = datetime.datetime.now() < ProductSku.objects.get(
        #         id=sku).product.offshelf_time < datetime.datetime.now() + datetime.timedelta(days=7)
        #     return not_in_unreturn and not onshelf
        return True
    @staticmethod
    def get_user_by_supplier(supplier_id):
        from django.contrib.auth.models import Group
        g = Group.objects.get(name=u'小鹿订货员')
        uids = [u['id'] for u in g.user_set.values('id')]
        r = OrderList.objects.filter(supplier_id=supplier_id, buyer_id__in=uids).values('buyer_id').annotate(
            s=Count('buyer_id'))

        def get_max_from_list(l):
            max_i = 0
            buyer_id = None
            for i in l:
                if i['s'] > max_i:
                    max_i = i['s']
                    buyer_id = i['buyer_id']
            return buyer_id
        res = get_max_from_list(r)
        if not res:
            res = uids[random.randint(0, len(uids)-1)]
        return res

    def set_stat(self):
        self.rg_details.filter(num=0, inferior_num=0).delete()
        rgds = self.rg_details.all()
        total_num = 0
        total_amount = 0
        for rgd in rgds:
            sum_num = rgd.num + rgd.inferior_num
            total_num += sum_num
            total_amount += sum_num * rgd.price
        self.return_num = total_num
        self.sum_amount = total_amount
        self.save()

    def has_sent(self):
        return self.status >= ReturnGoods.DELIVER_RG and not self.status == ReturnGoods.FAILED_RG

    def has_refund(self):
        return self.status in [ReturnGoods.REFUND_RG, ReturnGoods.SUCCEED_RG]

    def set_transactor(self, transactor):
        self.transactor_id = User.objects.get(username=transactor).id
        self.save()

    def delivery_by(self, logistics_no, logistics_company_id, consigner):
        self.sid = logistics_no
        self.logistics_company_id = logistics_company_id
        self.consigner = consigner
        self.consign_time = datetime.datetime.now()
        self.status = ReturnGoods.DELIVER_RG
        self.save()
        for d in self.rg_details.filter(type=RGDetail.TYPE_REFUND):
            ProductSku.objects.filter(id=d.skuid).update(quantity=F('quantity') - d.num)
        self.create_refund_bill()

    def create_refund_bill(self):
        if self.type == ReturnGoods.TYPE_CHANGE:
            return
        from flashsale.finance.models import Bill
        if self.sum_amount == 0:
            return
        bill = Bill(type=Bill.RECEIVE,
                    status=0,
                    creater=self.transactor,
                    pay_method=Bill.TRANSFER_PAY,
                    plan_amount=self.sum_amount,
                    note='',
                    supplier_id=self.supplier_id)
        bill.save()
        bill.relate_to([self])
        return bill

    def supply_notify_refund(self, receive_method, amount, note='', pic=None):
        """
            供应商说他已经退款了
        :return:
        """
        from flashsale.finance.models import Bill
        bill = Bill(type=Bill.RECEIVE,
                    status=0,
                    creater=self.transactor,
                    pay_method=receive_method,
                    plan_amount=amount,
                    note=note,
                    supplier_id=self.supplier_id)
        if pic:
            bill.attachment = pic
        bill.save()
        bill.relate_to([self])
        self.status = ReturnGoods.REFUND_RG
        self.save()
        return bill

    def set_confirm_refund_status(self, refund_status=u'已完成'):
        self.refund_status = dict([(r[1], r[0]) for r in ReturnGoods.REFUND_STATUS]).get(refund_status, 0)
        if self.refund_status == 1:
            self.status = ReturnGoods.REFUND_RG
        self.save()

    def set_failed(self):
        self.status = ReturnGoods.FAILED_RG
        rd = self.rg_details.all()
        for item in rd:
            skuid = item.skuid
            num = item.num
            inferior_num = item.inferior_num
            ProductSku.objects.filter(id=skuid).update(quantity=F('quantity') + num,
                                                       sku_inferior_num=F('sku_inferior_num') + inferior_num)
            self.save()
        return

    # def set_fail_closed(self):
    #     self.status = ReturnGoods.FAILED_RG
    #     self.save()

    @staticmethod
    def transactors():
        return User.objects.filter(is_staff=True,
                                   groups__name__in=(u'小鹿买手资料员', u'小鹿采购管理员', u'小鹿采购员', u'管理员', u'小鹿管理员')). \
            distinct().order_by('id')

    def add_sku(self, skuid, num, price=None, inferior=False):
        from shopback.items.models import ProductSku
        sku = ProductSku.objects.get(id=skuid)
        if self.status in [self.CREATE_RG, self.VERIFY_RG]:
            rgd = self.rg_details.filter(skuid=skuid).first()
            if rgd:
                if inferior and rgd.inferior_num > 0:
                    raise Exception(u'重复添加')
                if not inferior and rgd.num > 0:
                    raise Exception(u'重复添加')
            rgd = RGDetail()
            rgd.return_goods = self
            rgd.skuid = skuid
            rgd.type = self.type
            if inferior:
                rgd.inferior_num = num
            else:
                rgd.num = num
            rgd.price = price or sku.cost
            rgd.save()
        else:
            raise Exception(u'已发货的退货单不可更改')

    @property
    def pay_choices(self):
        from flashsale.finance.models import Bill
        return [{'value': x, 'text': y} for x, y in Bill.PAY_CHOICES]

    @property
    def bill(self):
        from flashsale.finance.models import BillRelation
        bill_relation = BillRelation.objects.filter(type=3, object_id=self.id).order_by('-id').first()
        if not bill_relation:
            return None
        return bill_relation.bill

    def __unicode__(self):
        return u'<%s,%s>' % (self.supplier_id, self.id)

    @property
    def bill_relation_dict(self):
        from django.template.loader import render_to_string
        from django.utils.safestring import mark_safe
        return {
            # 'payinfo': mark_safe(render_to_string('dinghuo/returngoods_payinfo.html', {'memo': self.memo, 'sum_amount': self.sum_amount})),
            'object_id': self.id,
            'payinfo': self.memo,
            'object_url': '/admin/dinghuo/returngoods/%d/' % self.id,
            'amount': self.sum_amount
        }

    def deal(self, confirm_pic_url):
        self.confirm_pic_url = confirm_pic_url
        self.status = self.REFUND_RG
        self.save()

    def confirm(self):
        self.status = self.SUCCEED_RG
        self.save()


def update_product_sku_stat_rg_quantity(sender, instance, created, **kwargs):
    if instance.created >= SkuStock.PRODUCT_SKU_STATS_COMMIT_TIME and instance.status in [
        ReturnGoods.REFUND_RG, ReturnGoods.DELIVER_RG,
        ReturnGoods.SUCCEED_RG, ReturnGoods.FAILED_RG, ReturnGoods.OBSOLETE_RG
    ]:
        from shopback.items.tasks_stats import task_update_product_sku_stat_rg_quantity
        for rg in instance.rg_details.all():
            task_update_product_sku_stat_rg_quantity.delay(rg.skuid)


post_save.connect(update_product_sku_stat_rg_quantity,
                  sender=ReturnGoods,
                  dispatch_uid='post_save_update_product_sku_stat_rg_quantity')


def update_sku_inferior_rg_num(sender, instance, created, **kwargs):
    from shopback.items.tasks import task_update_inferiorsku_rg_quantity
    if instance.has_sent():
        for detail in instance.rg_details.all():
            task_update_inferiorsku_rg_quantity.delay(detail.skuid)


post_save.connect(update_sku_inferior_rg_num, sender=ReturnGoods, dispatch_uid='post_save_update_sku_inferior_rg_num')


class RGDetail(models.Model):
    skuid = models.BigIntegerField(db_index=True, verbose_name=u"退货商品skuid")
    return_goods = models.ForeignKey(ReturnGoods,
                                     related_name='rg_details',
                                     verbose_name=u'退货单信息')
    num = models.IntegerField(default=0, verbose_name=u"正品退货数量")
    inferior_num = models.IntegerField(default=0, verbose_name=u"次品退货数量")
    price = models.FloatField(default=0.0, verbose_name=u"退回价格")
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'生成时间')
    modify = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    TYPE_REFUND = 0
    TYPE_CHANGE = 1
    TYPE_CHOICES = ((TYPE_REFUND, u'退货收款'),
                    (TYPE_CHANGE, u'退货更换'))
    type = models.IntegerField(choices=TYPE_CHOICES, default=0)
    src = models.IntegerField(default=0, verbose_name=u"来源", help_text=u"0或入库单id")
    wrong_desc = models.CharField(default='', max_length=100, verbose_name=u"错货描述", help_text=u"0或入库单id")

    class Meta:
        db_table = 'flashsale_dinghuo_rg_detail'
        app_label = 'dinghuo'
        verbose_name = u'商品库存退货明细表'
        verbose_name_plural = u'商品库存退货明细列表'

    def __unicode__(self):
        return u'<%s,%s>' % (self.skuid, self.return_goods)

    def sync_rg_field(self):
        rgds = self.return_goods.rg_details.all()
        total_num = 0
        total_amount = 0
        for rgd in rgds:
            sum_num = rgd.num + rgd.inferior_num
            total_num += sum_num
            total_amount += sum_num * rgd.price
        self.return_goods.return_num = total_num
        self.return_goods.sum_amount = total_amount
        self.return_goods.save()

    @property
    def product_sku(self):
        return ProductSku.objects.get(id=self.skuid)

    def get_src_desc(self):
        if not self.src:
            return u'库存退货'
        return u'入仓单<%d>' % self.src

    @staticmethod
    def get_inferior_total(sku_id, begin_time=SkuStock.PRODUCT_SKU_STATS_COMMIT_TIME):
        res = RGDetail.objects.filter(skuid=sku_id, created__gt=begin_time,
                                      return_goods__status__in=[ReturnGoods.DELIVER_RG, ReturnGoods.REFUND_RG,
                                                                ReturnGoods.SUCCEED_RG]).aggregate(
            n=Sum("inferior_num")).get('n', 0)
        return res or 0


def sync_rgd_return(sender, instance, created, **kwargs):
    instance.return_goods.set_stat()


post_save.connect(sync_rgd_return, sender=RGDetail, dispatch_uid='post_save_sync_rgd_return')


class UnReturnSku(BaseModel):
    EFFECT = 1
    INVALIED = 2
    supplier = models.ForeignKey(SaleSupplier, null=True, verbose_name=u"供应商")
    sale_product = models.ForeignKey(SaleProduct, null=True, verbose_name=u"关联选品")
    product = models.ForeignKey(Product, null=True, verbose_name=u"商品")
    sku = models.ForeignKey(ProductSku, null=True, verbose_name=u"sku")
    creater = models.ForeignKey(User, verbose_name=u'创建人')
    status = models.IntegerField(choices=((EFFECT, u'有效'), (INVALIED, u'无效')), default=0, verbose_name=u'状态')
    reason = models.IntegerField(choices=((1, u'保护商品'), (2, u'商家不许退货'), (3, u'其它原因')),
                                 default=2, verbose_name=u'不可退货原因')

    class Meta:
        db_table = 'flashsale_dinghuo_unreturn_sku'
        app_label = 'dinghuo'
        verbose_name = u'不可退货商品明细表'
        verbose_name_plural = u'不可退货商品明细列表'
