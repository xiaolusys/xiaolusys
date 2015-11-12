#-*- coding:utf-8 -*-
from django.db import models
from shopback.base.fields import BigIntegerAutoField
import logging
from django.db.models.signals import post_delete, post_save
class District(models.Model):
    
    FIRST_STAGE  = 1
    SECOND_STAGE = 2
    THIRD_STAGE  = 3
    FOURTH_STAGE = 4
    
    STAGE_CHOICES = ((FIRST_STAGE,u'1'),
                     (SECOND_STAGE,u'2'),
                     (THIRD_STAGE,u'3'),
                     (FOURTH_STAGE,u'4'),)
    
    id     = models.AutoField(primary_key=True,verbose_name=u'ID')
    parent_id = models.IntegerField(null=False,default=0,db_index=True,verbose_name=u'父ID')
    name    = models.CharField(max_length=32,blank=True,verbose_name=u'地址名')
    
    grade   = models.IntegerField(default=0,choices=STAGE_CHOICES,verbose_name=u'等级')
    sort_order = models.IntegerField(default=0,verbose_name=u'优先级')
    
    class Meta:
        db_table = 'flashsale_district' 
        verbose_name = u'省市/区划'
        verbose_name_plural = u'省市/区划列表'
        
    def __unicode__(self):
        return '%s,%s'%(self.id,self.name)
    
    @property
    def full_name(self):
        
        if self.parent_id and self.parent_id != 0:

            try:
                dist = self.__class__.objects.get(id=self.parent_id)
            except:
                return '[父ID未找到]-%s'%self.name
            else:
                return '%s,%s'%(dist.full_name,self.name)
        return self.name
    
    
from .managers import UserAddressManager

class UserAddress(models.Model):
    
    NORMAL = 'normal'
    DELETE = 'delete'
    
    STATUS_CHOICES = ((NORMAL,u'正常'),
                      (DELETE,u'删除'))
    
    cus_uid          =  models.BigIntegerField(db_index=True,verbose_name=u'客户ID')
    
    receiver_name    =  models.CharField(max_length=25,
                                         blank=True,verbose_name=u'收货人姓名')
    receiver_state   =  models.CharField(max_length=16,blank=True,verbose_name=u'省')
    receiver_city    =  models.CharField(max_length=16,blank=True,verbose_name=u'市')
    receiver_district  =  models.CharField(max_length=16,blank=True,verbose_name=u'区')
    
    receiver_address   =  models.CharField(max_length=128,blank=True,verbose_name=u'详细地址')
    receiver_zip       =  models.CharField(max_length=10,blank=True,verbose_name=u'邮编')
    receiver_mobile    =  models.CharField(max_length=11,db_index=True,blank=True,verbose_name=u'手机')
    receiver_phone     =  models.CharField(max_length=20,blank=True,verbose_name=u'电话')
    
    default         = models.BooleanField(default=False,verbose_name=u'默认地址')
    
    status          = models.CharField(max_length=8,blank=True,db_index=True,default=NORMAL,
                                       choices=STATUS_CHOICES,verbose_name=u'状态')
    
    created     = models.DateTimeField(auto_now_add=True,verbose_name=u'创建日期')
    modified   = models.DateTimeField(auto_now=True,verbose_name=u'修改日期')
    
    objects     = models.Manager()
    normal_objects = UserAddressManager()
    
    class Meta:
        db_table = 'flashsale_address' 
        verbose_name = u'特卖用户/地址'
        verbose_name_plural = u'特卖用户/地址列表'
        
    def __unicode__(self):
        
        return '<%s,%s>'%(self.id,self.cus_uid)
    
def set_only_one_default(sender, instance, *args, **kwargs):
    """ 新建一个地址后更新只有一个默认地址
        如果正常状态并且是默认地址，则更新所有的其他地址为非默认
        删除状态的则检查其他的是否有默认，并且有其他地址，满足条件则将第一个置为默认
    """
    user = instance.cus_uid
    normal_address = UserAddress.normal_objects.filter(cus_uid=user)
    if instance.status == UserAddress.NORMAL and instance.default:
        UserAddress.normal_objects.filter(cus_uid=user).exclude(id=instance.id).update(default=False)
    else:
        if not normal_address.filter(default=True) and normal_address.count() > 0:
            first_address = UserAddress.normal_objects.filter(cus_uid=user)[0]
            first_address.default = True
            first_address.save()

post_save.connect(set_only_one_default, sender=UserAddress, dispatch_uid='set_only_one')