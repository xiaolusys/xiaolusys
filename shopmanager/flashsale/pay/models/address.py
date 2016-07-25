# -*- coding:utf-8 -*-
from django.db import models
from django.db.models.signals import post_save
import logging
from .base import PayBaseModel, BaseModel
from .. import managers

logger = logging.getLogger('django.request')
class District(PayBaseModel):
    FIRST_STAGE = 1
    SECOND_STAGE = 2
    THIRD_STAGE = 3
    FOURTH_STAGE = 4

    STAGE_CHOICES = (
        (FIRST_STAGE, u'省'),
        (SECOND_STAGE, u'市'),
        (THIRD_STAGE, u'区/县'),
        (FOURTH_STAGE, u'街道'),
    )

    id = models.AutoField(primary_key=True, verbose_name=u'ID')
    parent_id = models.IntegerField(null=False, default=0, db_index=True, verbose_name=u'父ID')
    name = models.CharField(max_length=32, blank=True, verbose_name=u'地址名')

    zipcode = models.CharField(max_length=16, blank=True, verbose_name=u'邮政编码')
    grade = models.IntegerField(default=0, choices=STAGE_CHOICES, verbose_name=u'等级')
    sort_order = models.IntegerField(default=0, verbose_name=u'优先级')
    is_valid   = models.BooleanField(default=True, verbose_name=u'有效')
    class Meta:
        db_table = 'flashsale_district'
        app_label = 'pay'
        verbose_name = u'省市/区划'
        verbose_name_plural = u'省市/区划列表'

    def __unicode__(self):
        return '%s,%s' % (self.id, self.name)

    @property
    def full_name(self):

        if self.parent_id and self.parent_id != 0:

            try:
                dist = self.__class__.objects.get(id=self.parent_id)
            except:
                return '[父ID未找到]-%s' % self.name
            else:
                return '%s,%s' % (dist.full_name, self.name)
        return self.name

    @classmethod
    def latest_version(cls):
        # TODO 此处需要使用cache并考虑invalidate
        version = DistrictVersion.get_latest_version_district()
        if version:
            return {'version':version.version,
                    'download_url':version.download_url,
                    'hash': version.hash256}
        return {}


class DistrictVersion(PayBaseModel):

    version = models.CharField(max_length=32, unique=True, verbose_name=u'版本号')
    download_url = models.CharField(max_length=256, blank=True, verbose_name=u'下载链接')
    hash256 = models.CharField(max_length='128', blank=True, verbose_name=u'sha1值')
    memo = models.TextField(blank=True, verbose_name=u'备注')
    status = models.BooleanField(default=False, verbose_name=u'生效')

    class Meta:
        db_table = 'flashsale_district_version'
        app_label = 'pay'
        verbose_name = u'地址/区划版本'
        verbose_name_plural = u'地址/区划版本更新列表'

    def __unicode__(self):
        return '<%s, %s>' % (self.id, self.version)

    def gen_filepath(self):
        return 'district/xiaolumm-district-%s.json'%self.version

    @classmethod
    def get_latest_version_district(cls):
        latest_version = cls.objects.filter(status=True).order_by('-created').first()
        return latest_version


class UserAddress(BaseModel):
    NORMAL = 'normal'
    DELETE = 'delete'

    STATUS_CHOICES = ((NORMAL, u'正常'),
                      (DELETE, u'删除'))

    cus_uid = models.BigIntegerField(db_index=True, verbose_name=u'客户ID')

    receiver_name = models.CharField(max_length=25,
                                     blank=True, verbose_name=u'收货人姓名')
    receiver_state = models.CharField(max_length=16, blank=True, verbose_name=u'省')
    receiver_city = models.CharField(max_length=16, blank=True, verbose_name=u'市')
    receiver_district = models.CharField(max_length=16, blank=True, verbose_name=u'区')

    receiver_address = models.CharField(max_length=128, blank=True, verbose_name=u'详细地址')
    receiver_zip = models.CharField(max_length=10, blank=True, verbose_name=u'邮编')
    receiver_mobile = models.CharField(max_length=11, db_index=True, blank=True, verbose_name=u'手机')
    receiver_phone = models.CharField(max_length=20, blank=True, verbose_name=u'电话')

    default = models.BooleanField(default=False, verbose_name=u'默认地址')
    logistic_company_code = models.CharField(max_length=16, blank=True, verbose_name=u'优先快递编码')

    status = models.CharField(max_length=8, blank=True, db_index=True, default=NORMAL,
                              choices=STATUS_CHOICES, verbose_name=u'状态')

    objects = models.Manager()
    normal_objects = managers.NormalUserAddressManager()

    class Meta:
        db_table = 'flashsale_address'
        app_label = 'pay'
        verbose_name = u'特卖用户/地址'
        verbose_name_plural = u'特卖用户/地址列表'

    def __unicode__(self):
        return '<%s,%s>' % (self.id, self.cus_uid)

    def set_default_address(self):
        """ 设置默认地址 """
        current_address = self.__class__.objects.filter(cus_uid=self.cus_uid)  # 当前用户的地址
        current_address.update(default=False)  # 全部更新为非默认
        self.default = True
        self.save()  # 保存当前的为默认地址
        return True

    def set_logistic_company(self, company_code):
        """ 设置物流公司 """
        self.logistic_company_code = company_code
        self.save(update_fields=['logistic_company_code'])
        return True

    def clean_strip(self):
        changed = False
        for attr in ['receiver_name', 'receiver_phone', 'receiver_state', 'receiver_city', 'receiver_district',
                     'receiver_address']:
            val = getattr(self, attr)
            if val.strip() != val:
                changed = True
                setattr(self, attr, val.strip())
        return changed

class UserSingleAddress(BaseModel):
    receiver_state = models.CharField(max_length=16, blank=True,verbose_name=u'省')
    receiver_city = models.CharField(max_length=16, blank=True,verbose_name=u'市')
    receiver_district = models.CharField(max_length=16, blank=True, verbose_name=u'区')
    receiver_address = models.CharField(max_length=128, blank=True, verbose_name=u'详细地址')
    receiver_zip = models.CharField(max_length=10, blank=True, verbose_name=u'邮编')
    uni_key = models.CharField(max_length=64, unique=True, verbose_name=u'完整地址唯一KEY')
    address_hash = models.CharField(max_length=128, blank=True, db_index=True, verbose_name=u'地址哈希')
    note_id = models.IntegerField(default=0, verbose_name=u'完整地址ID')

    class Meta:
        db_table = 'flashsale_single_address'
        app_label = 'pay'
        verbose_name=u'特卖用户/唯一地址'
        verbose_name_plural = u'特卖用户/唯一地址列表'



class UserAddressChange(BaseModel):
    new_id = models.IntegerField(verbose_name=u'新地址ID', db_index=True)
    sale_trade = models.ForeignKey('SaleTrade', db_index=True)
    status = models.IntegerField(choices=((0, u'初始'), (1, u'完成'), (2, u'失败')), default=0, verbose_name=u'状态')
    cus_uid = models.BigIntegerField(db_index=True, verbose_name=u'客户ID')
    old_id = models.IntegerField(verbose_name=u'老地址ID', db_index=True)
    # 原始信息
    receiver_name = models.CharField(max_length=25,
                                     blank=True, verbose_name=u'收货人姓名')
    receiver_state = models.CharField(max_length=16, blank=True, verbose_name=u'省')
    receiver_city = models.CharField(max_length=16, blank=True, verbose_name=u'市')
    receiver_district = models.CharField(max_length=16, blank=True, verbose_name=u'区')
    receiver_address = models.CharField(max_length=128, blank=True, verbose_name=u'详细地址')
    receiver_zip = models.CharField(max_length=10, blank=True, verbose_name=u'邮编')
    receiver_mobile = models.CharField(max_length=11, db_index=True, blank=True, verbose_name=u'手机')
    receiver_phone = models.CharField(max_length=20, blank=True, verbose_name=u'电话')
    logistic_company_code = models.CharField(max_length=16, blank=True, verbose_name=u'优先快递编码')
    package_order_ids = models.CharField(max_length=100, blank=True, verbose_name=u'原包裹id')

    class Meta:
        # db_table = 'flashsale_address_change'
        app_label = 'pay'
        verbose_name = u'用户修改地址'
        verbose_name_plural = u'用户修改地址历史'

    @property
    def new_address(self):
        return UserAddress.objects.get(id=self.new_id)

    @property
    def old_address(self):
        return UserAddress.objects.get(id=self.old_id)

    @staticmethod
    def add(sale_trade, new_address):
        from shopback.trades.models import PackageOrder
        old_address = UserAddress.objects.get(id=sale_trade.user_address_id)
        u = UserAddressChange(sale_trade=sale_trade, cus_uid=sale_trade.buyer_id, old_id=old_address.id, new_id=new_address.id)
        update_fields = ['receiver_name', 'receiver_state', 'receiver_city',
                         'receiver_district', 'receiver_address', 'receiver_mobile',
                         'receiver_phone']
        for field in update_fields:
            val = getattr(sale_trade, field)
            setattr(u, field, val)
            if sale_trade.logistics_company:
                u.logistic_company_code = sale_trade.logistics_company.code
            pids = PackageOrder.get_ids_by_sale_trade(sale_trade.tid)
            u.package_order_ids = ','.join([str(i) for i in pids])
        u.save()
        return u

    def excute(self):
        if self.status == 0:
            from shopback.trades.models import PackageSkuItem, PackageOrder
            new_address = self.new_address
            update_fields = ['receiver_name', 'receiver_state', 'receiver_city',
                             'receiver_district', 'receiver_address', 'receiver_mobile',
                             'receiver_phone']
            strade = self.sale_trade
            for attrname in update_fields:
                setattr(strade, attrname, getattr(new_address, attrname))
            try:
                if new_address.logistic_company_code:
                    from shopback.logistics.models import LogisticsCompany
                    logistics_company = LogisticsCompany.objects.get(code=new_address.logistic_company_code)
                    strade.logistics_company = logistics_company
                strade.user_address_id = new_address.id
                strade.save(update_fields=update_fields + ['user_address_id', 'logistics_company'])
                if self.old_id != self.new_id:
                    PackageSkuItem.reset_trade_package(strade.tid)
                for pid in self.package_order_ids.split(','):
                    if pid:
                        package = PackageOrder.objects.get(pid=int(pid))
                        package.refresh()
                self.status = 1
            except Exception, ex:
                logger.error(str(u'用户修改地址出错:') + str(ex))
                self.status = 2
            self.save(update_fields=['status'])
