# -*- coding:utf8 -*-
from __future__ import unicode_literals

__author__ = 'meixqhi'
import json
import time
import random
import hashlib

from django.db import models
from django.db.models import Sum
from core.models import BaseModel
from django.core.cache import cache

from shopback.users.models import User
from shopback.monitor.models import TradeExtraInfo
from common.utils import parse_datetime
from shopapp.taobao import apis
from shopback.warehouse import constants
import logging
from shopback import paramconfig as pcfg

POST_STATE = (u'甘肃', u'青海', u'陕西', u'广西', u'宁夏', u'贵州', u'内蒙', u'西藏', u'新疆', u'云南')

logger = logging.getLogger('django.request')

LOGISTICS_FINISH_STATUS = ['ACCEPTED_BY_RECEIVER']

AREA_TYPE_CHOICES = (
    (1, 'country/国家'),
    (2, 'province/省/自治区/直辖市'),
    (3, 'city/地区'),
    (4, 'district/县/市/区'),
)


class Area(models.Model):
    id = models.BigIntegerField(primary_key=True, verbose_name='地区编号')
    parent_id = models.BigIntegerField(db_index=True, default=0, verbose_name='父级编号')

    type = models.IntegerField(default=0, choices=AREA_TYPE_CHOICES, verbose_name='区域类型')
    name = models.CharField(max_length=64, blank=True, verbose_name='地域名称')

    zip = models.CharField(max_length=10, blank=True, verbose_name='邮编')

    class Meta:
        db_table = 'shop_logistics_area'
        app_label = 'logistics'
        verbose_name = u'地理区划'
        verbose_name_plural = u'地理区划列表'

    def __unicode__(self):
        return '<%d,%d,%s,%s>' % (self.id, self.type, self.name, self.zip)


class DestCompany(models.Model):
    """ 区域指定快递选择 """
    state = models.CharField(max_length=64, blank=True, verbose_name='省/自治区/直辖市')
    city = models.CharField(max_length=64, blank=True, verbose_name='市')
    district = models.CharField(max_length=64, blank=True, verbose_name='县/市/区')

    company = models.CharField(max_length=10, blank=True, verbose_name='快递编码')

    class Meta:
        db_table = 'shop_logistics_destcompany'
        app_label = 'logistics'
        verbose_name = u'区域快递分配'
        verbose_name_plural = u'区域快递分配'

    def __unicode__(self):
        return '<%s,%s,%s,%s>' % (self.state, self.city, self.district, self.company)

    @classmethod
    def get_destcompany_by_addr(cls, state, city, district):

        companys = None
        if district:
            companys = cls.objects.filter(district__startswith=district)

        if city:
            if companys and companys.count() > 0:
                companys = companys.filter(city__startswith=city)
            else:
                companys = cls.objects.filter(city__startswith=city, district='')

        if state:
            if companys and companys.count() > 0:
                companys = companys.filter(state__startswith=state)
            else:
                companys = cls.objects.filter(state__startswith=state, city='', district='')

        if companys and companys.count() > 0:
            cid = companys[0].company

            logistic = LogisticsCompany.objects.get(code=cid.upper())

            return logistic

        return None


class LogisticsCompany(models.Model):
    NOPOST = 'HANDSALE'

    WARE_SH = constants.WARE_SH
    WARE_GZ = constants.WARE_GZ
    WARE_NONE = constants.WARE_NONE

    id = models.BigIntegerField(primary_key=True, verbose_name='ID')
    code = models.CharField(max_length=64, unique=True, blank=True, verbose_name='快递编码')
    name = models.CharField(max_length=64, blank=True, verbose_name='快递名称')
    reg_mail_no = models.CharField(max_length=500, blank=True, verbose_name='单号匹配规则')
    district = models.TextField(blank=True, verbose_name='服务区域(,号分隔)')
    priority = models.IntegerField(null=True, default=0, verbose_name='优先级')
    status = models.BooleanField(default=True, verbose_name='使用')
    TYPE_CHOICES = ((0, u'普通'), (1, u'发货'))
    type = models.IntegerField(default=0, db_index=True, verbose_name=u'物流公司用途',
                               help_text=u'发货物流公司不仅用于收货还可用于发货')
    express_key = models.CharField(max_length=64, blank=True, verbose_name='快递公司代码')
    kd100_express_key = models.CharField(max_length=64, blank=True, null=True, verbose_name="快递100编码")
    class Meta:
        db_table = 'shop_logistics_company'
        app_label = 'logistics'
        verbose_name = u'物流公司'
        verbose_name_plural = u'物流公司列表'

    def __unicode__(self):
        return '<%s,%s>' % (self.code, self.name)

    @classmethod
    def normal_companys(cls):
        return cls.objects.filter(status=True)

    @classmethod
    def get_logisticscompanys_by_warehouse(cls,ware_by, **kwags):
        # TODO 如过物流记录更新需要更新cache
        cache_key = hashlib.sha1('%s%s-%s'%(__file__,cls.__class__,ware_by)).hexdigest()
        cache_logistics = cache.get(cache_key)
        if not cache_logistics:
            if ware_by == constants.WARE_SH:
                cache_logistics = LogisticsCompany.objects.filter(code__in=('POSTB','STO','YUNDA_QR'))
            elif ware_by == constants.WARE_GZ:
                cache_logistics = LogisticsCompany.objects.filter(code__in=('POSTB', 'YUNDA_QR'))
            else:
                cache_logistics = LogisticsCompany.objects.filter(code__in=('POSTB','STO','YUNDA_QR'))
            cache.set(cache_key,cache_logistics, 24 * 60 * 60)
        return cache_logistics

    @classmethod
    def getNoPostCompany(cls):

        company, state = cls.objects.get_or_create(code=cls.NOPOST)
        if state:
            company.name = u'无需物流'
            company.save()

        return company

    @classmethod
    def get_recommend_express(cls, state, city, district):

        if not state:
            return None
        # 获取指定地区快递
        company = DestCompany.get_destcompany_by_addr(state, city, district)
        if company:
            return company
        # 根据系统规则选择快递
        logistics = cls.objects.filter(status=True).order_by('-priority')
        total_priority = logistics.aggregate(total_priority=Sum('priority')).get('total_priority')
        total_priority = max(total_priority, 1)
        priority_ranges = []
        cur_range = 0
        for logistic in logistics:
            districts = set([lg.strip()[0:2] for lg in logistic.district.split(',') if len(lg) > 1])
            if state[0:2] in districts:
                return logistic

            start_range = total_priority - cur_range - logistic.priority
            end_range = total_priority - cur_range
            priority_range = (start_range, end_range, logistic)
            cur_range += logistic.priority
            priority_ranges.append(priority_range)

        index = random.randint(1, total_priority)
        for rg in priority_ranges:
            if index >= rg[0] and index <= rg[1]:
                return rg[2]
        return None

    @classmethod
    def save_logistics_company_through_dict(cls, user_id, company_dict):
        company, state = cls.objects.get_or_create(id=company_dict['id'])
        for k, v in company_dict.iteritems():
            hasattr(company, k) and setattr(company, k, v)
        company.save()
        return company


class Logistics(models.Model):
    tid = models.BigIntegerField(primary_key=True)
    user = models.ForeignKey(User, null=True, related_name='logistics')

    order_code = models.CharField(max_length=64, blank=True)
    is_quick_cod_order = models.BooleanField(default=True)

    out_sid = models.CharField(max_length=64, blank=True)
    company_name = models.CharField(max_length=30, blank=True)

    seller_id = models.CharField(max_length=64, blank=True)
    seller_nick = models.CharField(max_length=64, blank=True)
    buyer_nick = models.CharField(max_length=64, blank=True)

    item_title = models.CharField(max_length=64, blank=True)

    delivery_start = models.DateTimeField(db_index=True, null=True, blank=True)
    delivery_end = models.DateTimeField(db_index=True, null=True, blank=True)

    receiver_name = models.CharField(max_length=64, blank=True)
    receiver_phone = models.CharField(max_length=20, blank=True)
    receiver_mobile = models.CharField(max_length=20, blank=True)

    location = models.TextField(max_length=500, blank=True)
    type = models.CharField(max_length=7, blank=True)  # free(卖家包邮),post(平邮),express(快递),ems(EMS).

    created = models.DateTimeField(db_index=True, null=True, blank=True)
    modified = models.DateTimeField(db_index=True, null=True, blank=True)

    seller_confirm = models.CharField(max_length=3, default='no')
    company_name = models.CharField(max_length=32, blank=True)

    is_success = models.BooleanField(default=False)
    freight_payer = models.CharField(max_length=6, blank=True)
    status = models.CharField(max_length=32, blank=True)

    class Meta:
        db_table = 'shop_logistics_logistic'
        app_label = 'logistics'
        verbose_name = u'订单物流'
        verbose_name_plural = u'订单物流列表'

    def __unicode__(self):
        return '<%s,%s>' % (self.tid, self.company_name)

    @classmethod
    def get_or_create(cls, user_id, tid):
        logistic, state = cls.objects.get_or_create(tid=tid)
        if not logistic.is_success:
            try:
                response = apis.taobao_logistics_orders_detail_get(tid=tid, tb_user_id=user_id)
                logistic_dict = response['logistics_orders_detail_get_response']['shippings']['shipping'][0]
                logistic = cls.save_logistics_through_dict(user_id, logistic_dict)
            except Exception, exc:
                logger.error('淘宝后台更新交易(tid:%s)物流信息出错'.decode('utf8') % str(tid), exc_info=True)
        return logistic

    @classmethod
    def save_logistics_through_dict(cls, user_id, logistic_dict):

        logistic, state = cls.objects.get_or_create(tid=logistic_dict['tid'])
        logistic.user = User.objects.get(visitor_id=user_id)
        logistic.seller_id = user_id
        for k, v in logistic_dict.iteritems():
            hasattr(logistic, k) and setattr(logistic, k, v)

        location = logistic_dict.get('location', None)
        logistic.location = json.dumps(location)

        logistic.delivery_start = parse_datetime(logistic_dict['delivery_start']) \
            if logistic_dict.get('delivery_start', None) else None
        logistic.delivery_end = parse_datetime(logistic_dict['delivery_end']) \
            if logistic_dict.get('delivery_end', None) else None
        logistic.created = parse_datetime(logistic_dict['created']) \
            if logistic_dict.get('created', None) else None
        logistic.modified = parse_datetime(logistic_dict['modified']) \
            if logistic_dict.get('modified', None) else None
        logistic.save()

        if logistic_dict['status'] in LOGISTICS_FINISH_STATUS:
            trade_extra_info, state = TradeExtraInfo.objects.get_or_create(tid=logistic_dict['tid'])
            trade_extra_info.is_update_logistic = True
            trade_extra_info.save()
        return logistic


class LogisticsCompanyProcessor(object):
    @staticmethod
    def getYundaLGC():
        return LogisticsCompany.objects.get_or_create(code='YUNDA_QR')[0]

    @staticmethod
    def getGZLogisticCompany(state, city, district, shipping_type, receiver_address):
        if not state or not city or not district:
            raise Exception(u"地址不全(请精确到省市区（县）)")
        if shipping_type.upper() == pcfg.EXPRESS_SHIPPING_TYPE.upper():
            # 定制订单快递分配
            if (receiver_address.find(u'镇') >= 0 and receiver_address.find(u'村') >= 0):
                if state.startswith(POST_STATE):
                    return LogisticsCompany.objects.get_or_create(code='POSTB')[0]
            return LogisticsCompanyProcessor.getYundaLGC()
        elif shipping_type.upper() in (pcfg.POST_SHIPPING_TYPE.upper(),
                               pcfg.EMS_SHIPPING_TYPE.upper()):
            return LogisticsCompany.objects.get_or_create(code=shipping_type)[0]

    @staticmethod
    def getSHLogisticCompany(state, city, district, shipping_type, receiver_address):
        if not state or not city or not district:
            raise Exception(u"地址不全(请精确到省市区（县）)")

        if shipping_type.upper() == pcfg.EXPRESS_SHIPPING_TYPE.upper():
            # 定制订单快递分配
            if (receiver_address.find(u'镇') >= 0
                and receiver_address.find(u'村') >= 0):
                if state.startswith(POST_STATE):
                    return LogisticsCompany.objects.get_or_create(code='POSTB')[0]
                return LogisticsCompany.objects.get_or_create(code='YUNDA_QR')[0]

            return LogisticsCompany.get_recommend_express(state, city, district)
        elif shipping_type.upper() in (pcfg.POST_SHIPPING_TYPE.upper(),
                               pcfg.EMS_SHIPPING_TYPE.upper()):
            return LogisticsCompany.objects.get_or_create(code=shipping_type)[0]
