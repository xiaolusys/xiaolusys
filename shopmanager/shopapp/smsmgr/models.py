#-*- coding:utf8 -*-
import time
import json
import datetime
from django.db import models
from shopback import paramconfig as pcfg
import logging

logger = logging.getLogger('smsmgr.handler')

SMS_NOTIFY_POST     = 'notify'     #发货告知
SMS_NOTIFY_ACTIVITY = 'activity'   #活动宣传
SMS_NOTIFY_PAYCALL  = 'paycall'    #付款提醒
SMS_NOTIFY_TOCITY   = 'tocity'     #同城提醒
SMS_NOTIFY_SIGN     = 'sign'       #签收提醒
SMS_NOTIFY_BIRTH    = 'birth'      #生日祝福

SMS_RECORD_STATUS = (
    (pcfg.SMS_CREATED,'初始创建'),
    (pcfg.SMS_COMMIT,'任务提交'),
    (pcfg.SMS_COMPLETE,'任务完成'),
    (pcfg.SMS_ERROR,'任务出错'), 
    (pcfg.SMS_CANCLE,'任务取消'),                      
)

SMS_NOITFY_TYPE =(
    (SMS_NOTIFY_PAYCALL ,u'付款提醒'), 
    (SMS_NOTIFY_POST    ,u'发货通知'),
    (SMS_NOTIFY_TOCITY  ,u'同城提醒'), 
    (SMS_NOTIFY_SIGN    ,u'签收提醒'),    
    (SMS_NOTIFY_BIRTH   ,u'生日祝福'), 
    (SMS_NOTIFY_ACTIVITY,u'活动宣传'),                
)


class SMSPlatform(models.Model):
    """ 短信服务商 """
    code    = models.CharField(max_length=16,verbose_name='编码')
    name    = models.CharField(max_length=64,verbose_name='服务商名称')
    
    user_id = models.CharField(max_length=32,verbose_name='企业ID')
    account   = models.CharField(max_length=64,verbose_name='帐号')
    password  = models.CharField(max_length=64,verbose_name='密码')
    
    remainums = models.IntegerField(default=0,verbose_name='剩余条数')
    sendnums  = models.IntegerField(default=0,verbose_name='已发条数')
    
    is_default = models.BooleanField(default=False,verbose_name='首选服务商')  
    
    class Meta:
        db_table = 'shop_smsmgr_smsplatform'
        verbose_name=u'短信服务商'
        verbose_name_plural = u'短信服务商列表'
        
    def __unicode__(self):
        return u'<%s>'%(self.code)
    

class SMSRecord(models.Model):
    """ 短信平台发送记录 """
    
    platform  = models.ForeignKey(SMSPlatform,null=True,default=None,related_name='sms_records',verbose_name='短信服务商')
    
    task_type = models.CharField(max_length=10,choices=SMS_NOITFY_TYPE,verbose_name='类型')
    
    task_id   = models.CharField(null=True,blank=True,default='',max_length=128,verbose_name='服务商返回任务ID')
    task_name = models.CharField(null=True,blank=True,default='',max_length=256,verbose_name='任务标题')
    mobiles   = models.TextField(null=True,blank=True,default='',verbose_name='发送号码')
    content   = models.CharField(null=True,blank=True,default='',max_length=1000,verbose_name='发送内容')
    
    sendtime  = models.DateTimeField(null=True,blank=True,verbose_name='定时发送时间')
    #finishtime = models.DateTimeField(null=True,blank=True,verbose_name='完成时间')
    
    countnums  = models.IntegerField(default=0,verbose_name='发送数量')
    mobilenums = models.IntegerField(default=0,verbose_name='手机数量')
    telephnums = models.IntegerField(default=0,verbose_name='固话数量')
    succnums   = models.IntegerField(default=0,verbose_name='成功数量')
    
    retmsg     = models.CharField(max_length=512,blank=True,null=True,verbose_name='任务返回结果')
    
    created    = models.DateTimeField(null=True,blank=True,auto_now_add=True,verbose_name='创建时间')
    modified   = models.DateTimeField(null=True,blank=True,auto_now=True,verbose_name='修改时间')
    
    memo       = models.CharField(max_length=512,blank=True,null=True,verbose_name='备注说明')
    status     = models.IntegerField(default=pcfg.SMS_CREATED,choices=SMS_RECORD_STATUS,verbose_name='任务返回结果')
    
    class Meta:
        db_table = 'shop_smsmgr_smsrecord'
        verbose_name=u'短信记录'
        verbose_name_plural = u'短信记录列表'
        
    def __unicode__(self):
        return '<%s,%s,%d,%d>'%(self.platform,self.task_name,self.countnums,self.succnums)
    
    
class SMSActivity(models.Model):
    """ 活动短信模板 """
    
    sms_type  = models.CharField(max_length=10,choices=SMS_NOITFY_TYPE,verbose_name='类型')
    text_tmpl = models.CharField(max_length=512,blank=True,null=True,verbose_name='内容')
    status    = models.BooleanField(default=True,verbose_name="状态")
    
    class Meta:
        db_table = 'shop_smsmgr_activity'
        verbose_name=u'短信模板'
        verbose_name_plural = u'短信模板列表'
        
    def __unicode__(self):
        return str(self.id)
    
    
