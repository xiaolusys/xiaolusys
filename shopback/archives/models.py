# -*- coding:utf8 -*-
from __future__ import unicode_literals

from django.db import models
import re


class Deposite(models.Model):
    """ 货位 """

    deposite_name = models.CharField(max_length=32, blank=True, verbose_name='仓库名')
    location = models.CharField(max_length=32, blank=True, verbose_name='仓库位置')

    in_use = models.BooleanField(default=True, verbose_name='使用')
    extra_info = models.TextField(blank=True, verbose_name='备注')

    class Meta:
        db_table = 'shop_archives_deposite'
        app_label = 'archives'
        verbose_name = u'货位'
        verbose_name_plural = u'货位列表'

    def __unicode__(self):
        return self.deposite_name


class DepositeDistrict(models.Model):
    """ 仓库库位 """
    DISTRICT_REGEX = '^(?P<parent_no>[a-zA-Z0-9=]+)-(?P<district_no>[a-zA-Z0-9]+)?$'
    district_no = models.CharField(max_length=32, blank=True, verbose_name='货位号')
    parent_no = models.CharField(max_length=32, blank=True, verbose_name='父货位号')
    location = models.CharField(max_length=64, blank=True, verbose_name='货位名')
    in_use = models.BooleanField(default=True, verbose_name='使用')
    extra_info = models.TextField(blank=True, verbose_name='备注')

    class Meta:
        db_table = 'shop_archives_depositedistrict'
        unique_together = ("parent_no", "district_no")
        app_label = 'archives'
        verbose_name = u'仓库货位'
        verbose_name_plural = u'仓库货位列表'

    @classmethod
    def match_district_name(cls, district):
        r = re.compile(cls.DISTRICT_REGEX)
        m = r.match(district)
        if not m:
            raise Exception(u'库位名称不合规则')
        return True

    @classmethod
    def get_by_name(self, district):
        r = re.compile(DepositeDistrict.DISTRICT_REGEX)
        m = r.match(district)
        if m:
            return DepositeDistrict.objects.filter(**m.groupdict()).first()

    def __unicode__(self):
        return '%s-%s' % (self.parent_no, self.district_no)


class SupplierType(models.Model):
    type_name = models.CharField(max_length=32, blank=True, verbose_name='类型名称')
    extra_info = models.TextField(blank=True, verbose_name='备注')

    class Meta:
        db_table = 'shop_archives_suppliertype'
        app_label = 'archives'
        verbose_name = u'供应商类型'
        verbose_name_plural = u'供应商类型列表'

    def __unicode__(self):
        return self.type_name


class Supplier(models.Model):
    supply_type = models.ForeignKey(SupplierType, null=True, related_name='suppliers', verbose_name='供应商类型')

    supplier_name = models.CharField(max_length=32, blank=True, verbose_name='供应商名称')
    contact = models.CharField(max_length=32, blank=True, verbose_name='联系方式')
    phone = models.CharField(max_length=32, blank=True, verbose_name='电话')
    mobile = models.CharField(max_length=16, blank=True, verbose_name='手机')
    fax = models.CharField(max_length=16, blank=True, verbose_name='传真')
    zip_code = models.CharField(max_length=16, blank=True, verbose_name='邮编')
    email = models.CharField(max_length=64, blank=True, verbose_name='邮箱')

    address = models.CharField(max_length=64, blank=True, verbose_name='地址')
    account_bank = models.CharField(max_length=32, blank=True, verbose_name='汇款银行')
    account_no = models.CharField(max_length=32, blank=True, verbose_name='汇款帐号')
    main_page = models.CharField(max_length=256, blank=True, verbose_name='供应商主页')

    in_use = models.BooleanField(default=True, verbose_name='使用')
    extra_info = models.TextField(blank=True, verbose_name='备注')

    class Meta:
        db_table = 'shop_archives_supplier'
        app_label = 'archives'
        verbose_name = u'供应商'
        verbose_name_plural = u'供应商列表'

    def __unicode__(self):
        return self.supplier_name


class PurchaseType(models.Model):
    """ 采购类型 """

    type_name = models.CharField(max_length=32, blank=True, verbose_name='采购类型')
    in_use = models.BooleanField(default=True, verbose_name='使用')

    extra_info = models.TextField(blank=True, verbose_name='备注')

    class Meta:
        db_table = 'shop_archives_purchasetype'
        app_label = 'archives'
        verbose_name = u'采购类型'
        verbose_name_plural = u'采购类型列表'

    def __unicode__(self):
        return self.type_name
