# -*- coding:utf-8 -*-
import datetime
from django.db import models, transaction
from django.db.models import Q, Sum, F, Manager
from django.db.models.signals import post_save
from django.conf import settings

from shopback.users.models import User
from shopback.items.models import Item, Product, ProductSku
from flashsale.pay.models import SaleOrder, SaleTrade
from shopback.logistics.models import Logistics, LogisticsCompany
from flashsale.pay.models import SaleTrade
from shopback.items.models import SkuStock
from flashsale import pay
import logging
from shopback.warehouse import WARE_NONE, WARE_GZ, WARE_SH, WARE_THIRD, WARE_CHOICES
from shopback.trades.constants import PSI_STATUS, SYS_ORDER_STATUS, IN_EFFECT, PO_STATUS
#
from shopback import paramconfig as pcfg
from models import TRADE_TYPE, TAOBAO_TRADE_STATUS

logger = logging.getLogger('django.request')


class PackageOrder(models.Model):
    WARE_SH = 1
    WARE_GZ = 2
    WARE_CHOICES = WARE_CHOICES
    pid = models.AutoField(verbose_name=u'包裹单号', primary_key=True)
    id = models.CharField(max_length=100, verbose_name=u'包裹码', unique=True)
    tid = models.CharField(max_length=32, verbose_name=u'参考交易单号')
    ware_by = models.IntegerField(default=WARE_SH, db_index=True, choices=WARE_CHOICES, verbose_name=u'所属仓库')
    status = models.CharField(max_length=32, db_index=True,
                              choices=TAOBAO_TRADE_STATUS, blank=True,
                              default=pcfg.TRADE_NO_CREATE_PAY, verbose_name=u'系统状态')
    PKG_NEW_CREATED = PO_STATUS.PKG_NEW_CREATED
    WAIT_PREPARE_SEND_STATUS = PO_STATUS.WAIT_PREPARE_SEND_STATUS
    WAIT_CHECK_BARCODE_STATUS = PO_STATUS.WAIT_CHECK_BARCODE_STATUS
    WAIT_SCAN_WEIGHT_STATUS = PO_STATUS.WAIT_SCAN_WEIGHT_STATUS
    WAIT_CUSTOMER_RECEIVE = PO_STATUS.WAIT_CUSTOMER_RECEIVE
    FINISHED_STATUS = PO_STATUS.FINISHED_STATUS
    DELETE = PO_STATUS.DELETE
    sys_status = models.CharField(max_length=32, db_index=True,
                                  choices=PO_STATUS.CHOICES, blank=True,
                                  default=PKG_NEW_CREATED, verbose_name=u'系统状态')
    sku_num = models.IntegerField(default=0, verbose_name=u'当前SKU种类数')
    order_sku_num = models.IntegerField(default=0, verbose_name=u'用户订货SKU种类总数')
    ready_completion = models.BooleanField(default=False, verbose_name=u'是否备货完毕')
    # 物流信息
    seller_id = models.BigIntegerField(db_index=True, verbose_name=u'卖家ID')
    # 收货信息
    receiver_name = models.CharField(max_length=25,
                                     blank=True, verbose_name=u'收货人姓名')
    receiver_state = models.CharField(max_length=16, blank=True, verbose_name=u'省')
    receiver_city = models.CharField(max_length=16, blank=True, verbose_name=u'市')
    receiver_district = models.CharField(max_length=16, blank=True, verbose_name=u'区')
    receiver_address = models.CharField(max_length=128, blank=True, verbose_name=u'详细地址')
    receiver_zip = models.CharField(max_length=10, blank=True, verbose_name=u'邮编')
    receiver_mobile = models.CharField(max_length=24, db_index=True,
                                       blank=True, verbose_name=u'手机')
    receiver_phone = models.CharField(max_length=20, db_index=True, blank=True, verbose_name=u'电话')

    user_address_id = models.BigIntegerField(null=False, db_index=True, verbose_name=u'地址ID')
    # 物流信息
    buyer_id = models.BigIntegerField(db_index=True, verbose_name=u'买家ID')
    buyer_nick = models.CharField(max_length=64, blank=True, verbose_name=u'买家昵称')

    buyer_message = models.TextField(max_length=1000, blank=True, verbose_name=u'买家留言')
    seller_memo = models.TextField(max_length=1000, blank=True, verbose_name=u'卖家备注')
    sys_memo = models.TextField(max_length=1000, blank=True, verbose_name=u'系统备注')
    seller_flag = models.IntegerField(null=True, default=0, verbose_name=u'淘宝旗帜')
    post_cost = models.FloatField(default=0.0, verbose_name=u'物流成本')
    is_lgtype = models.BooleanField(default=False, verbose_name=u'速递')
    lg_aging = models.DateTimeField(null=True, blank=True, verbose_name=u'速递送达时间')
    lg_aging_type = models.CharField(max_length=20, blank=True, verbose_name=u'速递类型')
    out_sid = models.CharField(max_length=64, db_index=True, blank=True, verbose_name=u'物流编号')
    logistics_company = models.ForeignKey(LogisticsCompany, null=True,
                                          blank=True, verbose_name=u'物流公司')
    # 仓库信息
    weight = models.CharField(max_length=10, blank=True, verbose_name=u'包裹重量')
    is_qrcode = models.BooleanField(default=False, verbose_name=u'热敏订单')
    qrcode_msg = models.CharField(max_length=32, blank=True, verbose_name=u'打印信息')
    can_review = models.BooleanField(default=False, verbose_name=u'复审')
    priority = models.IntegerField(default=0, verbose_name=u'作废字段')
    operator = models.CharField(max_length=32, blank=True, verbose_name=u'打单员')
    scanner = models.CharField(max_length=64, blank=True, verbose_name=u'扫描员')
    weighter = models.CharField(max_length=64, blank=True, verbose_name=u'称重员')
    is_locked = models.BooleanField(default=False, verbose_name=u'锁定')
    is_charged = models.BooleanField(default=False, verbose_name=u'揽件')
    is_picking_print = models.BooleanField(default=False, verbose_name=u'发货单')
    is_express_print = models.BooleanField(default=False, verbose_name=u'物流单')
    is_send_sms = models.BooleanField(default=False, verbose_name=u'发货通知')
    has_refund = models.BooleanField(default=False, verbose_name=u'待退款')

    created = models.DateTimeField(null=True, blank=True, auto_now_add=True, verbose_name=u'生成日期')
    modified = models.DateTimeField(null=True, blank=True, auto_now=True, verbose_name=u'修改日期')
    can_send_time = models.DateTimeField(db_column="merged", null=True, blank=True, verbose_name=u'可发货时间')
    send_time = models.DateTimeField(null=True, blank=True, verbose_name=u'发货日期')
    weight_time = models.DateTimeField(db_index=True, null=True, blank=True, verbose_name=u'称重日期')
    charge_time = models.DateTimeField(null=True, blank=True, verbose_name=u'揽件日期')
    remind_time = models.DateTimeField(null=True, blank=True, verbose_name=u'提醒日期')
    consign_time = models.DateTimeField(null=True, blank=True, verbose_name=u'发货日期')
    reason_code = models.CharField(max_length=100, blank=True, verbose_name=u'问题编号')  # 1,2,3 问题单原因编码集合
    redo_sign = models.BooleanField(default=False, verbose_name=u'重做标志')
    # 重做标志，表示该单要进行了一次废弃的打单验货
    merge_trade_id = models.BigIntegerField(null=True, blank=True, verbose_name=u'对应的MergeTrade')
    shipping_type = 'express'

    # 作废
    type = models.CharField(max_length=32, choices=TRADE_TYPE, db_index=True, default=pcfg.SALE_TYPE,
                            blank=True, verbose_name=u'订单类型')
    class Meta:
        db_table = 'flashsale_package'
        app_label = 'trades'
        verbose_name = u'包裹单'
        verbose_name_plural = u'包裹列表'

    def is_sent(self):
        return self.sys_status in [PackageOrder.FINISHED_STATUS, PackageOrder.WAIT_CUSTOMER_RECEIVE]

    @property
    def type(self):
        return u'小鹿特卖'

    @property
    def receiver_address_detail(self):
        return str(self.receiver_state) + str(self.receiver_city) + str(self.receiver_district) + str(
            self.receiver_address)

    @property
    def receiver_address_detail_wb(self):
        return str(self.receiver_state) + ' ' + str(self.receiver_city) + ' ' \
               + str(self.receiver_district) + ' ' + str(self.receiver_address)

    def copy_order_info(self, sale_trade):
        """从package_order或者sale_trade复制信息"""
        attrs = ['tid', 'receiver_name', 'receiver_state', 'receiver_city', 'receiver_district',
                 'receiver_address', 'receiver_zip', 'receiver_mobile', 'receiver_phone', 'buyer_nick']
        for attr in attrs:
            v = getattr(sale_trade, attr)
            setattr(self, attr, v)
        self.seller_id = sale_trade.seller.id

    def set_out_sid(self, out_sid, logistics_company_id):
        if not self.out_sid:
            self.out_sid = out_sid
            self.logistics_company_id = logistics_company_id
            self.save()

    def finish_scan_weight(self):
        from flashsale.pay.models import SaleOrder
        self.sys_status = PackageOrder.WAIT_CUSTOMER_RECEIVE
        self.weight_time = datetime.datetime.now()
        self.status = pcfg.WAIT_BUYER_CONFIRM_GOODS
        self.save()
        package_sku_items = PackageSkuItem.objects.filter(package_order_id=self.id,
                                                          assign_status=PackageSkuItem.ASSIGNED)
        for sku_item in package_sku_items:
            sku_item.out_sid = self.out_sid
            sku_item.logistics_company_name = self.logistics_company.name
            sku_item.logistics_company_code = self.logistics_company.code
            # sku_item.set_status_sent()
            sku_item.assign_status = PackageSkuItem.FINISHED
            sku_item.status = PSI_STATUS.SENT
            sku_item.set_assign_status_time()
            sku_item.save()
            sale_order = sku_item.sale_order
            sale_order.status = SaleOrder.WAIT_BUYER_CONFIRM_GOODS
            sale_order.consign_time = datetime.datetime.now()
            sale_order.save()
            psku = ProductSku.objects.get(id=sku_item.sku_id)
            psku.update_quantity(sku_item.num, dec_update=True)
            psku.update_wait_post_num(sku_item.num, dec_update=True)
        from shopback.trades.tasks import task_packageorder_send_check_packageorder
        task_packageorder_send_check_packageorder.delay()

    def finish_third_package(self, out_sid, logistics_company):
        self.out_sid = out_sid
        self.logistics_company_id = logistics_company.id
        self.sys_status = PackageOrder.WAIT_CUSTOMER_RECEIVE
        self.weight_time = datetime.datetime.now()
        self.status = pcfg.WAIT_BUYER_CONFIRM_GOODS
        self.save()
        # 为了承接过去的package_sku_item的数据, assign_status__in还要考虑 PackageSkuItem.ASSIGNED的情况
        package_sku_items = PackageSkuItem.objects.filter(package_order_id=self.id,
                                                          assign_status__in=[PackageSkuItem.ASSIGNED,
                                                                             PackageSkuItem.VIRTUAL_ASSIGNED])
        for sku_item in package_sku_items:
            sku_item.finish_third_send(self.out_sid, self.logistics_company)
            sale_order = sku_item.sale_order
            sale_order.status = SaleOrder.WAIT_BUYER_CONFIRM_GOODS
            sale_order.consign_time = datetime.datetime.now()
            sale_order.save()
            psku = ProductSku.objects.get(id=sku_item.sku_id)
            psku.update_quantity(sku_item.num, dec_update=True)
            psku.update_wait_post_num(sku_item.num, dec_update=True)

    def is_ready_completion(self):
        if self.sku_num == self.order_sku_num:
            self.ready_completion = True
            return True
        else:
            return False

    @property
    def buyer(self):
        if not hasattr(self, '_buyer_'):
            from flashsale.pay.models import Customer
            self._buyer_ = Customer.objects.get(id=self.buyer_id)
        return self._buyer_

    @property
    def pstat_id(self):
        return str(self.buyer_id) + '-' + str(self.user_address_id) + '-' + str(self.ware_by)

    @property
    def can_merge(self):
        '''
            是否能向包裹中加入sku订单
        '''
        return self.sys_status not in [PackageOrder.WAIT_CUSTOMER_RECEIVE, PackageOrder.FINISHED_STATUS,
                                       PackageOrder.DELETE]

    @property
    def sale_orders(self):
        if not hasattr(self, '_sale_orders_'):
            from flashsale.pay.models import SaleOrder
            sale_order_ids = list(
                PackageSkuItem.objects.filter(package_order_id=self.id).values_list('sale_order_id', flat=True))
            self._sale_orders_ = SaleOrder.objects.filter(id__in=sale_order_ids)
        return self._sale_orders_

    # @property
    def payment(self):
        return sum([p.payment for p in self.package_sku_items])

    payment.short_description = u'付款额'

    @property
    def package_sku_items(self):
        return PackageSkuItem.objects.filter(package_order_id=self.id)

    @property
    def first_package_sku_item(self):
        if not hasattr(self, '_first_package_sku_item_'):
            if self.package_sku_items.exclude(assign_status=PackageSkuItem.CANCELED).exists():
                self._first_package_sku_item_ = self.package_sku_items.exclude(
                    assign_status=PackageSkuItem.CANCELED).first()
            else:
                self._first_package_sku_item_ = self.package_sku_items.first()
        return self._first_package_sku_item_

    @property
    def seller(self):
        if not hasattr(self, '_seller_'):
            self._seller_ = User.objects.get(id=self.seller_id)
        return self._seller_

    @staticmethod
    def get_ids_by_sale_trade(sale_trade_tid):
        return [item['package_order_pid'] for item in
                PackageSkuItem.objects.filter(sale_trade_id=sale_trade_tid).exclude(package_order_pid=None).values(
                    'package_order_pid')]

    def set_redo_sign(self, action='', save_data=True):
        """
            在打过单以后
            重设状态到待发货准备
            指定重打发货单/物流单
        :param action:
        :param save_data:
        :return:
        """
        if self.sys_status not in [PackageOrder.WAIT_PREPARE_SEND_STATUS,
                                   PackageOrder.PKG_NEW_CREATED] and self.is_picking_print:
            if self.sys_status == PackageOrder.WAIT_SCAN_WEIGHT_STATUS:
                self.sys_status = PackageOrder.WAIT_CHECK_BARCODE_STATUS
            self.redo_sign = True
            if action == 'reset_picking_print':
                self.is_picking_print = False
            elif action == 'reset_express_print':
                self.is_express_print = False
        if self.sys_status == PackageOrder.PKG_NEW_CREATED:
            self.sys_status = PackageOrder.WAIT_PREPARE_SEND_STATUS
        if save_data:
            self.save()

    def reset_to_new_create(self):
        from flashsale.pay.models import FLASH_SELLER_ID
        new_p = PackageOrder()
        need_attrs = ['pid', 'id', 'buyer_id', 'user_address_id', 'ware_by', 'tid', 'receiver_name', 'receiver_state',
                      'receiver_city', 'receiver_district', 'receiver_address', 'receiver_zip', 'receiver_mobile',
                      'receiver_phone', 'buyer_nick', 'logistics_company_id', 'merged']
        # all_attrs = PackageOrder.get_deferred_fields()
        all_attrs = [i.column for i in PackageOrder._meta.fields]
        for attr in all_attrs:
            if attr not in need_attrs:
                val = getattr(new_p, attr)
                setattr(self, attr, val)
        self.can_send_time = None
        self.seller_id = User.objects.get(uid=FLASH_SELLER_ID).id
        self.sku_num = 0
        self.save()

    def reset_package_address(self):
        item = self.package_sku_items.filter(assign_status=PackageSkuItem.ASSIGNED).order_by('-id').first()
        if item and item.sale_trade_id:
            st = SaleTrade.objects.filter(tid=item.sale_trade_id).first()
            self.buyer_id = st.buyer_id
            self.receiver_name = st.receiver_name
            self.receiver_state = st.receiver_state
            self.receiver_city = st.receiver_city
            self.receiver_district = st.receiver_district
            self.receiver_address = st.receiver_address
            self.receiver_zip = st.receiver_zip
            self.receiver_phone = st.receiver_phone
            self.receiver_mobile = st.receiver_mobile

    def set_package_address(self):
        item = self.package_sku_items.filter(assign_status=PackageSkuItem.ASSIGNED).order_by('-id').first()
        if item and item.sale_trade_id:
            st = SaleTrade.objects.filter(tid=item.sale_trade_id).first()
            if not st:
                return self
            self.buyer_id = st.buyer_id
            self.receiver_name = st.receiver_name
            self.receiver_state = st.receiver_state
            self.receiver_city = st.receiver_city
            self.receiver_district = st.receiver_district
            self.receiver_address = st.receiver_address
            self.receiver_zip = st.receiver_zip
            self.receiver_phone = st.receiver_phone
            self.receiver_mobile = st.receiver_mobile
            self.save()
            return self

    def set_logistics_company(self):
        """
            如果已经有物流单号，设置公司和重打
            如果没有物流单号，直接改上sale_trade的物流公司
            如果sale_trade里没有指定，那自己设
        :return:
        """
        old_logistics_company_id = None
        if self.logistics_company_id:
            old_logistics_company_id = self.logistics_company_id
        package_sku_item = self.package_sku_items.order_by('-id').first()
        if not package_sku_item:
            return
        if package_sku_item.sale_trade.logistics_company:
            self.logistics_company_id = package_sku_item.sale_trade.logistics_company.id
            if old_logistics_company_id != self.logistics_company_id:
                if self.is_express_print:
                    self.is_express_print = False
                    self.redo_sign = True
                    self.save(update_fields=['logistics_company_id', 'is_express_print', 'redo_sign'])
                else:
                    self.save(update_fields=['logistics_company_id'])
        elif not old_logistics_company_id:
            from shopback.logistics.models import LogisticsCompanyProcessor
            from shopback.warehouse import WARE_GZ
            try:
                if self.ware_by == WARE_GZ:
                    self.logistics_company_id = LogisticsCompanyProcessor.getGZLogisticCompany(
                        self.receiver_state, self.receiver_city, self.receiver_district,
                        self.shipping_type, self.receiver_address).id
                else:
                    self.logistics_company_id = LogisticsCompanyProcessor.getSHLogisticCompany(
                        self.receiver_state, self.receiver_city, self.receiver_district,
                        self.shipping_type, self.receiver_address).id
            except:
                from shopback.logistics.models import LogisticsCompany
                self.logistics_company_id = LogisticsCompany.objects.get_or_create(code='YUNDA_QR')[0].id
            self.save(update_fields=['logistics_company_id'])

    def update_relase_package_sku_item(self):
        if not self.is_sent():
            if PackageSkuItem.objects.filter(package_order_id=self.id, assign_status=PackageSkuItem.ASSIGNED) \
                    .exists():
                self.set_redo_sign(save_data=False)
                self.reset_sku_item_num()
                self.save()
            else:
                self.reset_to_new_create()

    def reset_sku_item_num(self):
        if self.is_sent():
            sku_num = PackageSkuItem.objects.filter(package_order_id=self.id,
                                                    assign_status=PackageSkuItem.FINISHED).count()
            change = self.sku_num != sku_num
            self.sku_num = sku_num
            return change
        else:
            sku_items = PackageSkuItem.objects.filter(package_order_id=self.id,
                                                      assign_status=PackageSkuItem.ASSIGNED)
            sku_num = sku_items.count()
            order_sku_num = PackageSkuItem.unsend_orders_cnt(self.buyer_id)
            if order_sku_num > 0:
                ready_completion = sku_num == order_sku_num
            else:
                ready_completion = 0
            change = self.sku_num != sku_num or self.order_sku_num != order_sku_num or ready_completion != self.ready_completion
            self.sku_num = sku_num
            self.order_sku_num = order_sku_num
            self.ready_completion = ready_completion
            return change

    def refresh(self):
        """
            刷新包裹，重新从sale_trade里取一次数据
        :return:
        """
        if not self.is_sent():
            if self.package_sku_items.filter(assign_status=PackageSkuItem.ASSIGNED).exists():
                self.set_redo_sign(save_data=False, action='is_picking_print')
                self.reset_sku_item_num()
                self.set_package_address()
                self.set_logistics_company()
            else:
                self.reset_to_new_create()

    @staticmethod
    @transaction.atomic
    def create(id, sale_trade, sys_status='WAIT_PREPARE_SEND_STATUS', psi=None):
        package_order = PackageOrder(id=id)
        buyer_id, address_id, ware_by_id, order = id.split('-')
        package_order.buyer_id = int(buyer_id)
        package_order.user_address_id = int(address_id)
        package_order.ware_by = int(ware_by_id)
        package_order.copy_order_info(sale_trade)
        package_order.can_send_time = datetime.datetime.now()
        if sys_status:
            package_order.sys_status = sys_status
        package_order.sku_num = 1
        package_order.order_sku_num = PackageSkuItem.unsend_orders_cnt(int(buyer_id))
        package_order.ready_completion = package_order.order_sku_num == 1
        package_order.save()
        if psi:
            PackageSkuItem.objects.filter(id=psi.id).update(package_order_id=package_order.id,
                                                            package_order_pid=package_order.pid)
        return package_order

    @staticmethod
    def get_or_create(id, sale_trade):
        if not PackageOrder.objects.filter(id=id).exists():
            package_order = PackageOrder(id=id)
            buyer_id, address_id, ware_by_id, order = id.split('-')
            package_order.buyer_id = int(buyer_id)
            package_order.address_id = int(address_id)
            package_order.ware_by_id = int(ware_by_id)
            package_order.copy_order_info(sale_trade)
            package_order.save()
            new_create = True
        else:
            package_order = PackageOrder.objects.get(id=id)
            new_create = False
        return package_order, new_create

    def get_merge_trade(self, sync=True):
        from shopback.trades.models import MergeTrade
        if self.merge_trade_id:
            return MergeTrade.objects.get(id=self.merge_trade_id)
        if not sync:
            if MergeTrade.objects.filter(tid=self.tid).exists():
                return MergeTrade.objects.filter(tid=self.tid).order_by('-sys_status').first()
        return None

    @staticmethod
    def gen_new_package_id(buyer_id, address_id, ware_by_id):
        id = str(buyer_id) + '-' + str(address_id) + '-' + str(ware_by_id)
        if ware_by_id == WARE_THIRD:
            now_num = PackageStat.get_package_num(id) + 1
        else:
            now_num = PackageStat.get_sended_package_num(id) + 1
        # pstat = PackageStat.objects.get_or_create(id=id)[0]
        # now_num = pstat.num + 1
        res = id + '-' + str(now_num)

        while True:
            if PackageOrder.objects.filter(id=res, sys_status__in=
            [PackageOrder.FINISHED_STATUS, PackageOrder.WAIT_CUSTOMER_RECEIVE]).exists():
                logger.error('gen_new_package_id error: sku order smaller than count:' + str(res))
                now_num += 1
                res = id + '-' + str(now_num)
            else:
                break
        return res


def check_package_order_status(sender, instance, created, **kwargs):
    from shopback.logistics.tasks import task_get_logistics_company
    if instance.sys_status == PackageOrder.WAIT_PREPARE_SEND_STATUS and not instance.logistics_company:
        # task_get_logistics_company.delay(instance)
        task_get_logistics_company.apply_async(args=[instance.id], countdown=3)


post_save.connect(check_package_order_status, sender=PackageOrder)


def is_merge_trade_package_order_diff(package):
    merge_trade = package.get_merge_trade()
    # package_sku_items = package.package_sku_items
    # sale_order_ids = set([i.sale_order_id for i in package_sku_items])
    sale_order_ids = set([p.sale_order_id for p in PackageSkuItem.objects.filter(package_order_id=package.id)])
    sale_order_ids2 = set([mo.sale_order.id for mo in merge_trade.normal_orders])
    return sale_order_ids == sale_order_ids2


class PackageStat(models.Model):
    id = models.CharField(max_length=95, verbose_name=u'收货处', primary_key=True)
    num = models.IntegerField(default=0, verbose_name=u'已发数')

    class Meta:
        db_table = 'flashsale_package_stat'
        app_label = 'trades'
        verbose_name = u'包裹发送计数'
        verbose_name_plural = u'包裹发送计数列表'

    @staticmethod
    def get_package_num(package_stat_id):
        return PackageOrder.objects.filter(id__contains=package_stat_id + '-') \
            .exclude(sys_status__in=[PackageOrder.PKG_NEW_CREATED]).count()

    @staticmethod
    def get_sended_package_num(package_stat_id):
        return PackageOrder.objects.filter(id__startswith=package_stat_id + '-',
                                           sys_status__in=[PackageOrder.WAIT_CUSTOMER_RECEIVE,
                                                           PackageOrder.FINISHED_STATUS,
                                                           PackageOrder.DELETE]).count()


def update_package_stat_num(sender, instance, created, **kwargs):
    from shopback.trades.tasks import task_update_package_stat_num
    task_update_package_stat_num.delay(instance)


post_save.connect(update_package_stat_num, sender=PackageStat, dispatch_uid='post_update_package_stat_num')

from core.models import BaseModel


class PackageSkuItem(BaseModel):
    NOT_ASSIGNED = 0
    ASSIGNED = 1
    FINISHED = 2
    CANCELED = 3
    VIRTUAL_ASSIGNED = 4
    ASSIGN_STATUS = (
        (NOT_ASSIGNED, u'未备货'),
        (ASSIGNED, u'已备货'),
        (FINISHED, u'已出货'),
        (VIRTUAL_ASSIGNED, u'厂家备货中'),
        (CANCELED, u'已取消')
    )
    sale_order_id = models.IntegerField(unique=True, verbose_name=u'SKU订单编码')
    oid = models.CharField(max_length=40, null=True, db_index=True, verbose_name=u'SKU交易单号')
    sale_trade_id = models.CharField(max_length=40, null=True, db_index=True, verbose_name=u'交易单号')  # tid

    sku_id = models.CharField(max_length=20, blank=True, db_index=True, verbose_name=u'SKUID')
    outer_id = models.CharField(max_length=20, blank=True, verbose_name=u'商品编码')
    outer_sku_id = models.CharField(max_length=20, blank=True, verbose_name=u'规格ID')

    num = models.IntegerField(default=0, verbose_name=u'数量')
    status = models.CharField(max_length=32, choices=PSI_STATUS.CHOICES, db_index=True, default=PSI_STATUS.PAID, blank=True, verbose_name=u'订单状态')
    assign_status = models.IntegerField(choices=ASSIGN_STATUS, default=NOT_ASSIGNED, db_index=True, verbose_name=u'状态')
    sys_status = models.CharField(max_length=32, choices=SYS_ORDER_STATUS, blank=True, default=IN_EFFECT,
                                  verbose_name=u'系统状态')

    package_order_id = models.CharField(max_length=100, blank=True, db_index=True, null=True, verbose_name=u'包裹码')
    package_order_pid = models.IntegerField(db_index=True, null=True, verbose_name=u'包裹单号')
    ware_by = models.IntegerField(default=WARE_SH, choices=WARE_CHOICES, db_index=True, verbose_name=u'所属仓库')
    refund_status = models.IntegerField(choices=pay.REFUND_STATUS, default=pay.NO_REFUND,
                                        blank=True, verbose_name=u'退款状态')
    cid = models.BigIntegerField(null=True, verbose_name=u'商品分类')  # 合单时，不同商品的分类决定包裹能否进行合并操作
    title = models.CharField(max_length=128, blank=True, verbose_name=u'商品标题')
    sku_properties_name = models.CharField(max_length=256, blank=True, verbose_name=u'购买规格')
    pic_path = models.CharField(max_length=512, blank=True, verbose_name=u'商品图片')

    pay_time = models.DateTimeField(db_index=True, verbose_name=u'付款时间')
    book_time = models.DateTimeField(db_index=True, null=True, verbose_name=u'准备订货时间')
    booked_time = models.DateTimeField(db_index=True, null=True, verbose_name=u'订下货时间')
    ready_time = models.DateTimeField(db_index=True, null=True, verbose_name=u'分配时间')
    assign_time = models.DateTimeField(db_index=True, null=True, verbose_name=u'分配SKU时间')
    merge_time = models.DateTimeField(db_index=True, null=True, verbose_name=u'合单时间')
    merge_time = models.DateTimeField(db_index=True, null=True, verbose_name=u'合单时间')
    scan_time = models.DateTimeField(db_index=True, null=True, verbose_name=u'扫描时间')
    weight_time = models.DateTimeField(db_index=True, null=True, verbose_name=u'称重时间')
    finish_time = models.DateTimeField(db_index=True, null=True, verbose_name=u'完成时间')
    cancel_time = models.DateTimeField(db_index=True, null=True, verbose_name=u'取消时间')

    receiver_mobile = models.CharField(max_length=11, db_index=True, blank=True, verbose_name=u'收货手机')
    out_sid = models.CharField(max_length=64, db_index=True, blank=True, verbose_name=u'物流编号')
    logistics_company_name = models.CharField(max_length=16, blank=True, verbose_name=u'物流公司')
    logistics_company_code = models.CharField(max_length=16, blank=True, verbose_name=u'物流公司代码')
    failed_retrieve_time = models.DateTimeField(null=True, default=None, verbose_name=u'快递查询失败时间')

    purchase_order_unikey = models.CharField(max_length=32, db_index=True, blank=True, verbose_name=u'订货单唯一ID')
    sys_note = models.CharField(max_length=32, blank=True, verbose_name=u'系统备注')
    # 待废弃
    price = models.FloatField(default=0.0, verbose_name=u'单价')
    total_fee = models.FloatField(default=0.0, verbose_name=u'总费用')
    payment = models.FloatField(default=0.0, verbose_name=u'实付款')
    discount_fee = models.FloatField(default=0.0, verbose_name=u'折扣')
    adjust_fee = models.FloatField(default=0.0, verbose_name=u'调整费用')

    # 作废
    REAL_ORDER_GIT_TYPE = 0  # 实付
    CS_PERMI_GIT_TYPE = 1  # 赠送
    OVER_PAYMENT_GIT_TYPE = 2  # 满就送
    COMBOSE_SPLIT_GIT_TYPE = 3  # 拆分
    RETURN_GOODS_GIT_TYPE = 4  # 退货
    CHANGE_GOODS_GIT_TYPE = 5  # 换货
    ITEM_GIFT_TYPE = 6  # 买就送
    GIFT_TYPE = (
        (pcfg.REAL_ORDER_GIT_TYPE, u'实付'),
        (pcfg.CS_PERMI_GIT_TYPE, u'赠送'),
        (pcfg.OVER_PAYMENT_GIT_TYPE, u'满就送'),
        (pcfg.COMBOSE_SPLIT_GIT_TYPE, u'拆分'),
        (pcfg.RETURN_GOODS_GIT_TYPE, u'退货'),
        (pcfg.CHANGE_GOODS_GIT_TYPE, u'换货'),
        (pcfg.ITEM_GIFT_TYPE, u'买就送'),
    )
    gift_type = models.IntegerField(choices=GIFT_TYPE, default=REAL_ORDER_GIT_TYPE, verbose_name=u'类型')
    _objects = Manager()
    objects = Manager()
    class Meta:
        db_table = 'flashsale_package_sku_item'
        app_label = 'trades'
        verbose_name = u'包裹商品'
        verbose_name_plural = u'包裹商品列表'

    def set_failed_time(self):
        now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        PackageSkuItem.objects.filter(out_sid=self.out_sid).update(failed_retrieve_time=now_time)

    def cancel_failed_time(self):
        if self.failed_retrieve_time:
            PackageSkuItem.objects.filter(out_sid=self.out_sid).update(failed_retrieve_time=None)

    @staticmethod
    def get_failed_express():
        ps = PackageSkuItem.objects.exclude(failed_retrieve_time=None)
        return ps

    @staticmethod
    def get_failed_oneday():
        expire_time = datetime.datetime.now() - datetime.timedelta(days=1)
        return [i for i in PackageSkuItem.get_failed_express() if i.failed_retrieve_time < expire_time]

    @staticmethod
    def get_by_oid(oid):
        return PackageSkuItem.objects.filter(oid=oid).first()

    @staticmethod
    def get_by_tid(tid):
        return PackageSkuItem.objects.filter(sale_trade_id=tid)

    def get_supplier_product_info(self):
        """
        获取供应商的商品信息
        """
        from supplychain.supplier.models.product import SaleProduct

        product_sku = self.product_sku
        product = product_sku.product
        sale_product = SaleProduct.objects.filter(id=product.sale_product).first()
        sale_supplier = sale_product.sale_supplier

        return {
            'supplier': sale_supplier,
            'supplier_sku_code': product_sku.supplier_skucode,
            'supplier_sku_sale_price': sale_product.sale_price,
            'sale_product': sale_product,
            'product': product,
            'product_sku': product_sku
        }

    @property
    def sale_order(self):
        if not hasattr(self, '_sale_order_'):
            from flashsale.pay.models import SaleOrder
            self._sale_order_ = SaleOrder.objects.get(id=self.sale_order_id)
        return self._sale_order_

    @property
    def sale_trade(self):
        if not hasattr(self, '_sale_trade_'):
            self._sale_trade_ = self.sale_order.sale_trade
        return self._sale_trade_

    @property
    def order_list(self):
        from flashsale.dinghuo.models import OrderList
        if not hasattr(self, '_order_list_'):
            self._order_list_ = OrderList.objects.filter(purchase_order_unikey=self.purchase_order_unikey).first()
        return self._order_list_

    @property
    def product_sku(self):
        if not hasattr(self, '_product_sku_'):
            self._product_sku_ = ProductSku.objects.get(id=self.sku_id)
        return self._product_sku_

    @property
    def package_order(self):
        if self.package_order_id:
            if not hasattr(self, '_package_order_'):
                self._package_order_ = PackageOrder.objects.get(id=self.package_order_id)
            return self._package_order_
        else:
            return None

    @property
    def process_time(self):
        res_time = None

        if self.assign_status == PackageSkuItem.FINISHED:
            res_time = self.finish_time
        elif self.assign_status == PackageSkuItem.ASSIGNED:
            res_time = self.assign_time
        elif self.assign_status == PackageSkuItem.CANCELED:
            res_time = self.cancel_time
        if res_time:
            return res_time

        return self.created

    @property
    def package_group_key(self):
        book_sign = 0
        if self.purchase_order_unikey:
            book_sign = 1
        return '%s-%s-%s-%s' % (self.assign_status, self.ware_by, book_sign, self.out_sid)

    @property
    def ware_by_display(self):
        return '%s号仓' % self.ware_by

    @property
    def assign_status_display(self):
        if self.assign_status == PackageSkuItem.ASSIGNED:
            return '质检打包完毕'
        if self.assign_status == PackageSkuItem.FINISHED:
            return '已发货'
        if self.assign_status == PackageSkuItem.CANCELED:
            return '已取消'
        if self.assign_status == PackageSkuItem.NOT_ASSIGNED:
            if self.purchase_order_unikey:
                return '订单已送达工厂订货'
        if self.assign_status == PackageSkuItem.NOT_ASSIGNED:
            if self.purchase_order_unikey:
                return '订单已送达工厂订货'
        return '订单已确认'

    @property
    def num_of_purchase_try(self):
        return 1

    @property
    def return_ware_by(self):
        if self.ware_by == WARE_THIRD:
            return self.product_sku.product.get_supplier().return_ware_by
        return self.ware_by

    @property
    def note(self):
        if self.assign_status == PackageSkuItem.VIRTUAL_ASSIGNED and self.purchase_order_unikey:
            return '亲，订单信息已送达厂家，厂家正发货，暂时不可取消。若要退款，请收货后选择七天无理由退货。客服电话400-823-5355。'
        if self.assign_status == PackageSkuItem.NOT_ASSIGNED and self.purchase_order_unikey:
            return '亲，订单信息已送达厂家，厂家正发货，暂时不可取消。若要退款，请收货后选择七天无理由退货。客服电话400-823-5355。'
        if self.assign_status == PackageSkuItem.FINISHED or self.assign_status == PackageSkuItem.CANCELED:
            return '亲，申请退货后请注意退货流程，记得填写快递单号哦～'
        return ''

    def get_purchase_arrangement(self):
        from flashsale.dinghuo.models_purchase import PurchaseArrangement
        return PurchaseArrangement.objects.filter(oid=self.oid).first()

    # ---------------------------------------供应链核心方法--------------------------------------------------------------
    @staticmethod
    def create(sale_order):
        ware_by = ProductSku.objects.get(id=sale_order.sku_id).ware_by
        sku_item = PackageSkuItem(sale_order_id=sale_order.id, ware_by=ware_by)
        attrs = ['num', 'oid', 'package_order_id', 'title', 'price', 'sku_id',
                 'total_fee', 'payment', 'discount_fee', 'refund_status',
                 'pay_time', 'status', 'pic_path']
        for attr in attrs:
            if hasattr(sale_order, attr):
                val = getattr(sale_order, attr)
                setattr(sku_item, attr, val)
        sku_item.outer_sku_id = sku_item.product_sku.outer_id
        sku_item.outer_id = sku_item.product_sku.product.outer_id
        sku_item.receiver_mobile = sale_order.sale_trade.receiver_mobile
        sku_item.sale_trade_id = sale_order.sale_trade.tid
        sku_item.sku_properties_name = sale_order.sku_name
        sku_stock = SkuStock.get_by_sku(sale_order.sku_id)
        assigned = sku_stock.can_assign(sku_item)
        if assigned:
            sku_item.set_status_assigned()
        else:
            sku_item.set_status_paid()
        sku_item.save()
        if not assigned:
            sku_item.gen_arrangement()
        return sku_item

    @property
    def sku_stock(self):
        return SkuStock.get_by_sku(self.sku_id)

    def gen_arrangement(self):
        from flashsale.dinghuo.models_purchase import PurchaseArrangement
        return PurchaseArrangement.create(self)

    def set_status_paid(self):
        self.status = PSI_STATUS.PAID
        self.assign_status = 0
        self.save()
        SkuStock.set_psi_init_paid(self.sku_id, self.num)

    def set_status_prepare_book(self):
        self.status = PSI_STATUS.PREPARE_BOOK
        self.book_time = datetime.datetime.now()
        self.save()
        SkuStock.set_psi_prepare_book(self.sku_id, self.num)

    def set_status_booked(self, save=False):
        self.status = PSI_STATUS.BOOKED
        self.book_time = datetime.datetime.now()
        if save:
            self.save()
            SkuStock.set_psi_paid_prepare_book(self.sku_id, self.num)

    def set_status_ready(self):
        ori_status = self.status
        self.status = PSI_STATUS.READY
        self.assign_status = 1
        self.ready_time = datetime.datetime.now()
        self.save()
        if not ori_status:
            SkuStock.set_psi_init_ready(self.sku_id, self.num)
        else:
            SkuStock.set_psi_booked_to_ready(self.sku_id, self.num)

    def set_status_assigned(self, save=False):
        self.status = PSI_STATUS.ASSIGNED
        self.assign_status = 1
        self.assign_time = datetime.datetime.now()
        if save:
            self.save()
            SkuStock.set_psi_assigned(self.sku_id, self.num)
        pa = self.get_purchase_arrangement()
        if pa:
            pa.cancel()

    def set_status_not_assigned(self, save=True):
        self.status = PSI_STATUS.PAID
        self.assign_status = 0
        self.assign_time = datetime.datetime.now()
        if save:
            SkuStock.set_psi_not_assigned(self.sku_id, self.num ,stat=True)
            self.save()

    def merge(self):
        self.status = PSI_STATUS.MERGED
        self.merge_time = datetime.datetime.now()
        package_order_id = PackageOrder.gen_new_package_id(self)
        po = PackageOrder.objects.filter(id=package_order_id).first()
        if po:
            self.package_order_id = po.id
            self.package_order_pid = po.pid
            po.add_package_sku_item(po)
        else:
            PackageOrder.create(id, po.sale_trade)
        self.save()
        SkuStock.set_psi_merged(self.sku_id, self.num)

    def set_status_waitscan(self):
        self.status = PSI_STATUS.WAITSCAN
        self.scan_time = datetime.datetime.now()
        self.save()
        SkuStock.set_psi_waitscan(self.sku_id, self.num)

    def set_status_waitpost(self):
        self.status = PSI_STATUS.WAITPOST
        self.assign_status = 1
        self.scan_time = datetime.datetime.now()
        self.save()
        SkuStock.set_psi_waitpost(self.sku_id, self.num)

    def set_status_sent(self):
        self.status = PSI_STATUS.SENT
        self.assign_status = 2
        self.save()
        SkuStock.set_psi_sent(self.sku_id, self.num)

    def set_status_finish(self):
        self.status = PSI_STATUS.FINISH
        self.assign_status = 2
        self.save()
        SkuStock.set_psi_finish(self.sku_id, self.num)

    def set_status_cancel(self):
        """
            已产生Pa但未审核　直接取消并关pa
        """
        if self.assign_status == 3:
            raise Exception(u'已取消的包裹商品不能再次取消:%s' % self.id)
        pa = self.get_purchase_arrangement()
        if pa and not pa.initial_book:
            pa.cancel()
        ori_status = self.status
        self.status = PSI_STATUS.CANCEL
        self.assign_status = 3
        self.save()
        SkuStock.set_psi_cancel(self.sku_id, self.num, ori_status)
    # -----------------------------------

    def reset_status(self):
        """
            依据当前订单信息，设置status
        """
        from flashsale.pay.models import SaleOrder
        if self.assign_status == PackageSkuItem.CANCELED:
            self.status = PSI_STATUS.CANCEL
        elif self.sale_order.status == SaleOrder.TRADE_BUYER_SIGNED:
            self.status = PSI_STATUS.FINISH
        elif self.assign_status == PackageSkuItem.FINISHED:
            self.status = PSI_STATUS.SENT
        elif self.assign_status == PackageSkuItem.VIRTUAL_ASSIGNED:
            self.status = PSI_STATUS.THIRD_SEND
        elif self.assign_status == PackageSkuItem.ASSIGNED:
            if self.package_order:
                if self.package_order.sys_status == PO_STATUS.WAIT_SCAN_WEIGHT_STATUS:
                    self.status = PSI_STATUS.WAITPOST
                elif self.package_order.sys_status == PO_STATUS.WAIT_CHECK_BARCODE_STATUS:
                    self.status = PSI_STATUS.WAITSCAN
                else:
                    self.status = PSI_STATUS.MERGED
            elif not self.package_order:
                self.status = PSI_STATUS.READY
        elif self.assign_status == PackageSkuItem.NOT_ASSIGNED:
            if self.purchase_order_unikey and self.order_list.can_receive():
                self.status = PSI_STATUS.BOOKED
            elif self.purchase_order_unikey:
                self.status = PSI_STATUS.PREPARE_BOOK
        else:
            self.status = PSI_STATUS.PAID
            
    @staticmethod
    def unsend_orders_cnt(buyer_id):
        payed_counts = SaleOrder.objects.filter(buyer_id=buyer_id, status=SaleOrder.WAIT_SELLER_SEND_GOODS).count()
        payed_saleorder = SaleOrder.objects.filter(buyer_id=buyer_id, status=SaleOrder.WAIT_SELLER_SEND_GOODS)
        oids = [o.oid for o in payed_saleorder]
        unuse_cnt = PackageSkuItem.objects.filter(oid__in=oids, assign_status__in=[PackageSkuItem.CANCELED,
                                                                                   PackageSkuItem.FINISHED]).count()
        payed_counts -= unuse_cnt
        return payed_counts

    @transaction.atomic
    def finish_third_send(self, out_sid, logistics_company):
        """
            执行完此方法后应该执行OrderList的set_by_package_sku_item方法。以确保订货数准确。
        """
        if self.assign_status in [PackageSkuItem.VIRTUAL_ASSIGNED, PackageSkuItem.ASSIGNED]:
            PackageSkuItem.objects.filter(id=self.id).update(assign_status=PackageSkuItem.FINISHED,
                                                             status=PSI_STATUS.SENT,
                                                             out_sid=out_sid,
                                                             logistics_company_name=logistics_company.name,
                                                             logistics_company_code=logistics_company.code,
                                                             finish_time=datetime.datetime.now())
            SkuStock.objects.filter(sku_id=self.sku_id).update(post_num=F('post_num') + self.num)

    def gen_package(self):
        sale_trade = self.sale_trade
        if not (sale_trade.buyer_id and sale_trade.user_address_id and self.product_sku.ware_by):
            raise Exception('packagize_sku_item error: sale_trade loss some info:' + str(sale_trade.id))
        package_order_id = PackageOrder.gen_new_package_id(sale_trade.buyer_id, sale_trade.user_address_id,
                                                           self.product_sku.ware_by)
        package_order = PackageOrder.objects.filter(id=package_order_id).first()
        if not package_order:
            PackageOrder.create(package_order_id, sale_trade, PackageOrder.WAIT_PREPARE_SEND_STATUS, self)
        else:
            PackageSkuItem.objects.filter(id=self.id).update(package_order_id=package_order_id,
                                                             package_order_pid=package_order.pid)
            package_order.set_redo_sign(save_data=False)
            package_order.reset_package_address()
            package_order.reset_sku_item_num()
            package_order.save()

    def get_purchase_uni_key(self):
        """为了和历史上的purchase_record unikey保持一致"""
        return self.oid + '-1'

    def is_canceled(self):
        return self.assign_status == PackageSkuItem.CANCELED

    def is_booking_needed(self):
        return self.assign_status == PackageSkuItem.NOT_ASSIGNED

    def is_booking_assigned(self):
        # self.assigned_purchase_order_id
        if self.assign_status == PackageSkuItem.ASSIGNED or self.assign_status == PackageSkuItem.FINISHED:
            return True
        return False

    def is_booked(self):
        """
        Return True means that this sku is already booked.
        """
        if self.purchase_order_unikey:
            return True
        return False

    def clear_order_info(self):
        if self.assign_status == 2:
            return
        self.package_order_id = None
        self.package_order_pid = None
        self.logistics_company_code = ''
        self.logistics_company_name = ''
        self.out_sid = ''
        self.save()

    def set_assign_status_time(self):
        if self.assign_status == PackageSkuItem.FINISHED:
            self.finish_time = datetime.datetime.now()
        elif self.assign_status == PackageSkuItem.ASSIGNED:
            self.assign_time = datetime.datetime.now()
        elif self.assign_status == PackageSkuItem.CANCELED:
            self.cancel_time == datetime.datetime.now()

    def reset_assign_status(self):
        package_order = self.package_order
        self.package_order_id = None
        self.package_order_pid = None
        self.assign_status = PackageSkuItem.NOT_ASSIGNED
        self.save()
        if package_order:
            package_order.update_relase_package_sku_item()

    def reset_assign_package(self):
        if self.assign_status in [PackageSkuItem.NOT_ASSIGNED, PackageSkuItem.ASSIGNED]:
            self.receiver_mobile = self.sale_trade.receiver_phone
            self.clear_order_info()

    @staticmethod
    def reset_trade_package(sale_trade_tid):
        for item in PackageSkuItem.objects.filter(sale_trade_id=sale_trade_tid):
            item.reset_assign_package()

    @staticmethod
    def get_not_assign_num(sku_id):
        return PackageSkuItem.objects.filter(sku_id=sku_id, assign_status=PackageSkuItem.NOT_ASSIGNED).aggregate(
            total=Sum('num')).get('total') or 0

    @staticmethod
    def get_need_purchase(condition_add={}):
        condition = {
            'purchase_order_unikey':'',
            'assign_status':PackageSkuItem.NOT_ASSIGNED
        }
        condition.update(condition_add)
        return PackageSkuItem.objects.filter(**condition).order_by('created')

    def is_finished(self):
        return self.assign_status == PackageSkuItem.FINISHED


def update_productskustats(sender, instance, created, **kwargs):
    """
    Whenever PackageSkuItem changes, PackageSkuItemStats has to change accordingly.
    """
    from shopback.items.tasks_stats import task_packageskuitem_update_productskustats
    logger = logging.getLogger('service')
    logger.info({
        'action': 'skustat.pstat.update_productskustats',
        'instance': instance.sku_id,
        'psi_id': instance.id,
        'assign_status': instance.assign_status,
    })
    task_packageskuitem_update_productskustats(instance.sku_id)
    # task_packageskuitem_update_productskustats.delay(instance.sku_id)


# if not settings.CLOSE_CELERY:
#     post_save.connect(update_productskustats, sender=PackageSkuItem, dispatch_uid='post_save_update_productskustats')


def update_productsku_salestats_num(sender, instance, created, **kwargs):
    from shopback.trades.tasks import task_packageskuitem_update_productskusalestats_num
    transaction.on_commit(lambda: task_packageskuitem_update_productskusalestats_num(instance.sku_id, instance.pay_time))


post_save.connect(update_productsku_salestats_num, sender=PackageSkuItem,
                  dispatch_uid='post_save_update_productsku_salestats_num')


def update_package_order(sender, instance, created, **kwargs):
    from shopback.trades.tasks import task_update_package_order
    transaction.on_commit(lambda: task_update_package_order.delay(instance.id))


post_save.connect(update_package_order, sender=PackageSkuItem,
                  dispatch_uid='post_save_update_package_order')


def update_purchase_arrangement(sender, instance, created, **kwargs):
    from flashsale.dinghuo.tasks import task_packageskuitem_update_purchase_arrangement
    task_packageskuitem_update_purchase_arrangement.delay(instance)

#
# if not settings.CLOSE_CELERY:
#     post_save.connect(update_purchase_arrangement, sender=PackageSkuItem,
#                   dispatch_uid='post_save_update_purchase_record')


def check_saleorder_sync(sender, instance, created, **kwargs):
    if created:
        from shopback.trades.tasks import task_saleorder_check_packageskuitem
        task_saleorder_check_packageskuitem.delay()

#
# post_save.connect(check_saleorder_sync, sender=PackageSkuItem,
#                   dispatch_uid='post_save_check_saleorder_sync')


def get_package_address_dict(package_order):
    res = {}
    attrs = ['buyer_id', 'receiver_name', 'receiver_state', 'receiver_city', 'receiver_district', 'receiver_address',
             'receiver_zip', 'receiver_mobile']
    for attr in attrs:
        res[attr] = getattr(package_order, attr)
    return res


def get_user_address_dict(ua):
    res = {}
    attrs = ['receiver_name', 'receiver_state', 'receiver_city', 'receiver_district', 'receiver_address',
             'receiver_zip', 'receiver_mobile']
    for attr in attrs:
        res[attr] = getattr(ua, attr)
    res['buyer_id'] = ua.cus_uid
    return res


def get_sale_trade_address_dict(sale_trade):
    res = {}
    attrs = ['buyer_id', 'receiver_name', 'receiver_state', 'receiver_city', 'receiver_district', 'receiver_address',
             'receiver_zip', 'receiver_mobile']
    for attr in attrs:
        res[attr] = getattr(sale_trade, attr)
    return res
