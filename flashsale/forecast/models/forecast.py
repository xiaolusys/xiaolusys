# coding=utf-8
import re
import datetime
import random
from django.db import models, transaction
from django.db.models import Q, F
from django.db.models.signals import post_save, pre_save

from core.models import BaseModel
from core.utils.unikey import uniqid
from core.utils import update_model_fields
from flashsale.dinghuo.models import OrderList, OrderDetail, InBound, OrderDetailInBoundDetail
from .. import constants
import logging

logger = logging.getLogger(__name__)


def default_forecast_inbound_no(identify_id=None):
    identify_id = identify_id or uniqid()
    return 'fid' + datetime.datetime.now().strftime('%Y%m%d') + identify_id


def gen_subforecast_inbound_no(parent_id):
    forecast_id = parent_id.split('-')[0]
    forecast = ForecastInbound.objects.filter(forecast_no__startswith=forecast_id) \
        .order_by('-forecast_no').first()
    if forecast:
        forecast_id_list = forecast.forecast_no.split('-')
        if len(forecast_id_list) > 1 and forecast_id_list[1].isdigit():
            return '%s-%d' % (forecast_id, int(forecast_id_list[1]) + 1)
    return '%s-1' % forecast_id


class ForecastInbound(BaseModel):
    ST_DRAFT = 'draft'
    ST_APPROVED = 'approved'
    ST_ARRIVED = 'arrived'
    ST_TIMEOUT = 'timeout'
    ST_FINISHED = 'finished'
    ST_CLOSED = 'close'
    ST_CANCELED = 'canceled'

    STATUS_CHOICES = (
        (ST_DRAFT, u'草稿'),
        (ST_APPROVED, u'审核'),
        (ST_ARRIVED, u'到货'),
        (ST_FINISHED, u'已完成'),
        (ST_TIMEOUT, u'超时关闭'),
        (ST_CLOSED, u'缺货关闭'),
        (ST_CANCELED, u'取消'),
    )

    STAING_STATUS = [ST_DRAFT, ST_APPROVED, ST_ARRIVED]

    forecast_no = models.CharField(max_length=32, default=default_forecast_inbound_no,
                                   unique=True, verbose_name=u'入库批次')
    supplier = models.ForeignKey('supplier.SaleSupplier',
                                 null=True,
                                 blank=True,
                                 related_name='forecast_inbound_manager',
                                 verbose_name=u'供应商')

    relate_order_set = models.ManyToManyField('dinghuo.OrderList',
                                              related_name='forecase_inbounds', verbose_name=u'关联订货单')
    ware_house = models.IntegerField(default=constants.WARE_NONE,
                                     choices=constants.WARE_CHOICES, verbose_name=u'所属仓库')

    express_code = models.CharField(max_length=32, choices=constants.EXPRESS_CONPANYS,
                                    blank=True, verbose_name=u'预填快递公司')
    express_no = models.CharField(max_length=32, blank=True, db_index=True, verbose_name=u'预填运单号')
    forecast_arrive_time = models.DateTimeField(blank=True, null=True, verbose_name=u'预测到货时间')

    total_forecast_num = models.IntegerField(default=0, verbose_name=u'总预测数')
    total_arrival_num = models.IntegerField(default=0, verbose_name=u'总到货数')

    purchaser = models.CharField(max_length=30, blank=True, db_index=True, verbose_name=u'采购员')

    status = models.CharField(max_length=8, db_index=True, default=ST_DRAFT,
                              choices=STATUS_CHOICES, verbose_name=u'状态')
    memo = models.TextField(max_length=1000, blank=True, verbose_name=u'备注')

    delivery_time = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name=u'发货时间')
    arrival_time = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name=u'到货时间')

    is_unrecordlogistic = models.BooleanField(default=False, verbose_name=u'未及时催货')
    has_lack = models.BooleanField(default=False, db_index=True, verbose_name=u'缺货')
    has_defact = models.BooleanField(default=False, db_index=True, verbose_name=u'次品')
    has_overhead = models.BooleanField(default=False, db_index=True, verbose_name=u'多到')
    has_wrong = models.BooleanField(default=False, db_index=True, verbose_name=u'错发')

    class Meta:
        db_table = 'forecast_inbound'
        app_label = 'forecast'
        verbose_name = u'预测到货单'
        verbose_name_plural = u'预测到货单列表'

    def __unicode__(self):
        return '<%s,%s>' % (self.id, self.supplier and self.supplier.supplier_name or u'未知供应商')

    def delete(self, using=None):
        self.status = self.ST_CANCELED
        self.save()

    def clean(self):
        for field in self._meta.fields:
            if isinstance(field, (models.CharField, models.TextField)):
                setattr(self, field.name, getattr(self, field.name).strip())

    @property
    def status_name(self):
        return self.get_status_display()

    @property
    def total_detail_num(self):
        forecast_nums = self.normal_details.values_list('forecast_arrive_num', flat=True)
        return forecast_nums and sum(forecast_nums) or 0

    @property
    def real_arrive_num(self):
        from .inbound import RealInbound, RealInboundDetail
        relate_inbound_ids = list(RealInbound.objects.filter(forecast_inbound=self).values_list('id', flat=True))
        arrival_quantitys = RealInboundDetail.objects.filter(inbound_id__in=relate_inbound_ids,
                                                             status=RealInboundDetail.NORMAL) \
            .values_list('arrival_quantity', flat=True)
        return arrival_quantitys and sum(arrival_quantitys) or 0

    def get_ware_house_name(self):
        return dict(constants.WARE_CHOICES).get(self.ware_house)

    @property
    def normal_details(self):
        return self.details_manager.filter(status=ForecastInboundDetail.NORMAL)

    def is_unrecord_logistic(self):
        return self.status in (self.ST_DRAFT, self.ST_APPROVED) and self.express_code == '' and self.express_no == ''

    def is_inthedelivery(self):
        """ 是否发货中 """
        return self.status in (self.ST_DRAFT, self.ST_APPROVED)

    def is_arrival_except(self):
        """ 是否到货异常 """
        return self.has_lack or self.has_defact or self.has_overhead or self.has_wrong

    def is_arrival_timeout(self):
        """ 到货超时 """
        tnow = datetime.datetime.now()
        if self.status in (self.ST_APPROVED, self.ST_DRAFT) and \
                (not self.forecast_arrive_time or self.forecast_arrive_time < tnow):
            return True
        if self.status == self.ST_TIMEOUT:
            return True
        return False

    def inbound_arrive_update_status(self, arrival_time=None):
        if self.is_unrecord_logistic():
            self.is_unrecordlogistic = True
        if not self.arrival_time:
            self.arrival_time = arrival_time or datetime.datetime.now()
        if not self.delivery_time:
            self.delivery_time = self.created + datetime.timedelta(days=1)
            if self.delivery_time > self.arrival_time:
                self.delivery_time = self.arrival_time
        self.status = self.ST_ARRIVED

    def inbound_arrive_confirm_finish(self):
        if self.status != self.ST_ARRIVED:
            raise Exception(u'预测单非到货状态，无法完成')
        self.status = ForecastInbound.ST_FINISHED

    def unarrive_close_update_status(self):
        self.status = self.ST_CANCELED

    def lackgood_close_update_status(self):
        self.status = self.ST_CLOSED

    @staticmethod
    def get_by_express_no_order_list(express_no, orderlist_id):
        order_list = OrderList.objects.filter(Q(id=orderlist_id) | Q(express_no=express_no)).first()
        forecast_inbounds = ForecastInbound.objects.filter(
            Q(relate_order_set__id=orderlist_id) | Q(express_no=express_no),
            status__in=(ForecastInbound.ST_APPROVED, ForecastInbound.ST_DRAFT))
        if not order_list:
            return forecast_inbounds
        res = list(forecast_inbounds)
        excludes = [i.id for i in forecast_inbounds]
        res2 = ForecastInbound.objects.filter(supplier_id=order_list.supplier_id,
                                       status__in=(ForecastInbound.ST_APPROVED, ForecastInbound.ST_DRAFT)).\
            exclude(id__in=excludes)
        res2 = list(res2)
        return res + res2

    @staticmethod
    @transaction.atomic
    def reset_forecast(order_list_id):
        """
            重设预测：从以前的预测单中删除本订货单的关联，利用此订货单重新建立预测
        """
        forcasts = ForecastInbound.objects.filter(relate_order_set__id=order_list_id)
        order_list_ids = [order_list_id]
        for forcast in forcasts:
            for ol in forcast.relate_order_set.all():
                order_list_ids.append(ol.id)
        order_list_ids = list(set(order_list_ids))
        res = []
        forcasts.filter(status__in=[ForecastInbound.ST_DRAFT, ForecastInbound.ST_APPROVED]).update(status=ForecastInbound.ST_CANCELED)
        for order_list_id in order_list_ids:
            ol = OrderList.objects.get(id=order_list_id)
            if ol.stage in [OrderList.STAGE_CHECKED, OrderList.STAGE_PAY, OrderList.STAGE_RECEIVE] and not ol.third_package:
                res.append(ForecastInbound._generate([order_list_id]))
        return res

    @staticmethod
    def update_forecast(inbound_id):
        """
            入库分配时更新预测单：
            如预测单不包含入仓单分配到的所有订货单，则合并相关预测单
            否则，剥离出未完成的预测单，生成新一轮预测单，将老预测单打上入仓标记并关闭
            当订货单进入结算时，从预测单剔除已完成的订货单
        :param inbound:
        :return:
        """
        inbound = InBound.objects.get(id=inbound_id)
        order_list_ids = inbound.order_list_ids
        forecasts = ForecastInbound.objects.filter(relate_order_set__id__in=order_list_ids,
                                       status__in=[ForecastInbound.ST_DRAFT, ForecastInbound.ST_APPROVED])
        if forecasts.count() > 1:
            for forecast in forecasts:
                for ol in forecast.relate_order_set.all():
                    order_list_ids.append(ol.id)
            order_list_ids = list(set(order_list_ids))
            forecast = ForecastInbound.merge(order_list_ids)
        else:
            forecast = forecasts.first()
        if forecast:
            forecast.forecast_no = 'inbound-%s' % (inbound.id, )
            forecast.status = ForecastInbound.ST_ARRIVED
            forecast.save()
        return ForecastInbound._generate(order_list_ids)

    @staticmethod
    def merge(orderlist_ids):
        """
            合并预测单（依据预测单关联的orderlist进行预测单重算，而非直接预测单相加，以减少错误）
        :param orderlist_ids:
        :param forecast_arrive_time:
        :return:
        """
        forcasts = ForecastInbound.objects.filter(relate_order_set__in=orderlist_ids,
                                                  status__in=['draft', 'approved'])
        supplier = forcasts.first().supplier
        forecast_ib = ForecastInbound(supplier=supplier)
        forecast_ib.ware_house = supplier.ware_by
        forecast_ib.purchaser = forcasts.first().purchaser
        forecast_ib.forecast_arrive_time = datetime.datetime.now() + datetime.timedelta(days=supplier.get_delta_arrive_days())
        forecast_ib.save()
        details = {}
        res = {}
        for forcast in forcasts:
            for fd in forcast.details_manager.all():
                if fd.sku_id not in details:
                    forecast_detail = ForecastInboundDetail(forecast_inbound=forecast_ib,
                                                                sku_id=fd.sku_id,
                                                                product_id=fd.product_id,
                                                            product_name=fd.product_name,
                                                            product_img=fd.product_img)
                    details[forecast_detail.sku_id] = forecast_detail
                res[forecast_detail.sku_id] = res.get(forecast_detail.sku_id, 0) + fd.forecast_arrive_num
        forcasts.update(status=ForecastInbound.ST_CANCELED)
        for sku_id in details:
            details[sku_id].forecast_arrive_num = res[sku_id]
            details[sku_id].save()
        return forecast_ib

    @staticmethod
    def merge_bak(orderlist_ids):
        """
            合并预测单（依据预测单关联的orderlist进行预测单重算，而非直接预测单相加，以减少错误）
        :param orderlist_ids:
        :param forecast_arrive_time:
        :return:
        """
        order_lists = OrderList.objects.filter(id__in=orderlist_ids, stage=OrderList.STAGE_RECEIVE)
        if order_lists.count() == 0:
            return
        orderlist_ids = [ol.id for ol in order_lists]
        forcasts = ForecastInbound.objects.filter(relate_order_set__in=orderlist_ids,
                                                  status__in=['draft', 'approved'])
        forcasts.update(status=ForecastInbound.ST_ARRIVED)
        olids = [ol.id for ol in forcasts.relate_order_set.filter(stage=OrderList.STAGE_RECEIVE)]
        return ForecastInbound._generate(olids)

    @staticmethod
    def _generate(orderlist_ids):
        order_lists = OrderList.objects.filter(id__in=orderlist_ids, stage=OrderList.STAGE_RECEIVE)
        if order_lists.count() == 0:
            return
        order_list = order_lists.first()
        supplier = order_list.supplier
        # orderlist_ids = [ol.id for ol in order_lists]
        forecast_ib = ForecastInbound(supplier=supplier)
        forecast_ib.ware_house = supplier.ware_by
        forecast_ib.purchaser = order_list.buyer and order_list.buyer.username or order_list.buyer_name
        forecast_ib.forecast_arrive_time = datetime.datetime.now() + datetime.timedelta(days=supplier.get_delta_arrive_days())
        forecast_ib.save()
        for order_list in order_lists:
            forecast_ib.relate_order_set.add(order_list)
        details = {}
        sku_buy_nums = {}
        sku_got_nums = {}
        for od in OrderDetail.objects.filter(orderlist_id__in=orderlist_ids):
            sku_buy_nums[od.chichu_id] = sku_buy_nums.get(od.chichu_id, 0) + od.buy_quantity
            if not details.get(od.chichu_id):
                forecast_detail = ForecastInboundDetail(forecast_inbound=forecast_ib,
                                                        sku_id=od.chichu_id,
                                                        product_id=od.product.id)
                forecast_detail.forecast_inbound = forecast_ib
                forecast_detail.product_name = '%s:%s' % (od.product.name, od.sku.name)
                forecast_detail.product_img = od.product.pic_path
                details[od.chichu_id] = forecast_detail
        for odd in OrderDetailInBoundDetail.objects.filter(orderdetail__orderlist_id__in=orderlist_ids,
                                                    inbounddetail__inbound__status__in=[InBound.PENDING, InBound.WAIT_CHECK, InBound.COMPLETED,
                                                                                        InBound.COMPLETE_RETURN]):
            od = odd.orderdetail
            sku_got_nums[od.chichu_id] = sku_got_nums.get(od.chichu_id, 0) + odd.arrival_quantity
        sku_need_nums = {key:sku_buy_nums[key] - sku_got_nums.get(key, 0) for key in sku_buy_nums}
        for sku in sku_need_nums:
            forecast_detail = details[sku]
            forecast_detail.forecast_arrive_num = sku_need_nums[sku]
        for forecast_detail in details.values():
            if forecast_detail.forecast_arrive_num > 0:
                forecast_detail.save()
        return forecast_ib

# def pre_save_update_forecastinbound_data(sender, instance, raw, *args, **kwargs):
#     logger.info('forecast pre_save:%s, %s' % (raw, instance))
#     from .inbound import RealInbound
#     detail_list_num = instance.normal_details.values_list('forecast_arrive_num', flat=True)
#     arrival_list_num = instance.real_inbound_manager.exclude(status=RealInbound.CANCELED) \
#         .values_list('total_inbound_num', flat=True)
#     instance.total_forecast_num = sum(detail_list_num)
#     instance.total_arrival_num = sum(arrival_list_num)
#     instance.express_no = re.sub(r'\W', '', instance.express_no)
#
#
# pre_save.connect(
#     pre_save_update_forecastinbound_data,
#     sender=ForecastInbound,
#     dispatch_uid='pre_save_update_forecastinbound_data')


# def modify_forecastinbound_data(sender, instance, created, *args, **kwargs):
#     logger.info('forecast post_save:%s, %s' % (created, instance))
#     if (instance.express_no and
#             not instance.delivery_time and
#                 instance.status == ForecastInbound.ST_APPROVED):
#         instance.delivery_time = datetime.datetime.now()
#         ForecastInbound.objects.filter(id=instance.id).update(delivery_time=instance.delivery_time)
#
#     if instance.express_no:
#         for order in instance.relate_order_set.filter(Q(express_no='/') | Q(express_no='')):
#             order.express_company = instance.express_code
#             order.express_no = instance.express_no
#             update_model_fields(order, update_fields=['express_company', 'express_no'])
#
#     # refresh forecast stats
#     from .. import tasks
#     tasks.task_forecast_update_stats_data.delay(instance.id)
#
#     # 更新orderlist order_group_key
#     inbound_order_set = list(instance.relate_order_set.values_list('id', flat=True))
#     from flashsale.dinghuo.tasks import task_update_order_group_key
#     task_update_order_group_key.delay(inbound_order_set)
#
#
# post_save.connect(
#     modify_forecastinbound_data,
#     sender=ForecastInbound,
#     dispatch_uid='post_save_modify_forecastinbound_data')


class ForecastInboundDetail(BaseModel):
    NORMAL = 0
    DELETE = 1

    STATUS_CHOICES = (
        (NORMAL, u'普通'),
        (DELETE, u'删除'),
    )

    forecast_inbound = models.ForeignKey(ForecastInbound, related_name='details_manager', verbose_name=u'关联预测单')
    # orderlist = models.ForeignKey(OrderList, related_name='orderlist', verbose_name=u'订货单')
    product_id = models.IntegerField(db_index=True, verbose_name=u'商品ID')
    sku_id = models.IntegerField(verbose_name=u'规格ID')
    forecast_arrive_num = models.IntegerField(default=0, verbose_name='预测到货数量')

    product_name = models.CharField(max_length=128, blank=True, verbose_name=u'商品全称')
    product_img = models.CharField(max_length=256, blank=True, verbose_name=u'商品图片')

    status = models.IntegerField(default=NORMAL, db_index=True, choices=STATUS_CHOICES, verbose_name=u'状态')

    class Meta:
        db_table = 'forecast_inbound_detail'
        unique_together = ('sku_id', 'forecast_inbound')
        app_label = 'forecast'
        verbose_name = u'预测到货明细'
        verbose_name_plural = u'预测到货明细列表'

    def __unicode__(self):
        return '<%s,%s,%s>' % (self.id, self.product_name, self.forecast_arrive_num)

    def get_productsku(self):
        if not hasattr(self, '__productsku__'):
            from shopback.items.models import ProductSku
            product_sku = ProductSku.objects.filter(id=self.sku_id).first()
            self.__productsku__ = product_sku
        return self.__productsku__

    product_sku = property(get_productsku)

    def get_product(self):
        product_sku = self.get_productsku()
        if product_sku:
            return product_sku.product
        return None

    product = property(get_product)

    @property
    def product_pic(self):
        return self.product.pic_path + '?imageMogr2/strip/format/jpg/quality/90/interlace/1/thumbnail/80/'


# def update_forecastinbound_data(sender, instance, created, **kwargs):
#     pass
#
#
# post_save.connect(
#     update_forecastinbound_data,
#     sender=ForecastInboundDetail,
#     dispatch_uid='post_save_update_forecastinbound_data')
