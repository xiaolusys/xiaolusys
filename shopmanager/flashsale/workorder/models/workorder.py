# -*- coding:utf-8 -*-
__author__ = 'huazi'
from django.db import models
from django.contrib.auth.models import User
import datetime

class WorkOrder(models.Model):

    STATUS_PENDING = 0
    STATUS_DEALING = 1
    STATUS_DEALED = 2
    STATUS_FINISHED = 3

    STATUS_CHOICES = (
        (STATUS_PENDING,u'待处理'),
        (STATUS_DEALING,u'处理中'),
        (STATUS_DEALED,u'已处理'),
        (STATUS_FINISHED,u'已完成')
    )



    YES = 1
    NO = 0

    VALID_CHOICES = (
        (YES,u'有效'),
        (NO,u'无效')
    )


    SERIOUS = 1
    COMMON = 2
    SMALL = 3

    LEVEL = (
        (SERIOUS,u'严重'),
        (COMMON,u'普通'),
        (SMALL,u'轻微')
    )

    IOS=1
    ANDRIOD = 2
    WEIXIN = 3
    FINANCE = 4
    PURCHASE = 5
    SUPPLYCHAIN = 6
    WARHOUSE = 7

    PRBM_TYPE=(
        (IOS,u'苹果'),
        (ANDRIOD,u'安卓'),
        (WEIXIN,u'微信商城'),
        (FINANCE,u'财务'),
        (PURCHASE,u'采购'),
        (SUPPLYCHAIN,u'供应链'),
        (WARHOUSE,u'仓库')
    )
    id = models.AutoField(verbose_name=u'工单编号',primary_key=True)
    problem_title = models.TextField(max_length=32, blank=True, verbose_name=u'问题标题')
    problem_type = models.IntegerField(choices=PRBM_TYPE,blank=True, verbose_name=u'问题类型')
    problem_desc = models.TextField(max_length=1024, blank=True, verbose_name=u'问题描述')
    status = models.IntegerField(choices=STATUS_CHOICES, default=STATUS_PENDING,verbose_name=u'工单处理状态')
    is_valid = models.IntegerField(choices=VALID_CHOICES, default=YES,verbose_name=u'工单状态')
    level = models.IntegerField(choices=LEVEL,blank=False, default=COMMON,verbose_name=u'工单等级')
    problem_back = models.TextField(max_length=1024, blank=True, verbose_name=u'问题反馈')
    creater = models.CharField(max_length=32, db_index=True, blank=True, verbose_name=u'创建人')
    dealer = models.CharField(max_length=32, db_index=True, blank=True, verbose_name=u'处理人')
    created_time = models.DateTimeField(auto_now_add=True, db_index=True,verbose_name=u'提交日期')
    modified_time = models.DateTimeField(null=True,db_index=True, verbose_name=u'处理日期')

    class Meta:
        db_table = 'flashsale_workorder'
        app_label = 'workorder'
        verbose_name = u'工单'
        verbose_name_plural = u'工单列表'

    def __unicode__(self):
        return u"%s,%s" % (self.id,self.problem_title)

    def set_invaild(self):
        """设置工单失效"""
        if self.is_valid == WorkOrder.YES:
            self.is_valid = WorkOrder.NO
            self.save(update_fields=['is_valid'])

    def change_problem_title(self,problem_title):
        """修改工单问题标题"""
        self.problem_title = problem_title
        self.save(update_fields=['problem_title'])

    def change_problem_type(self, problem_type):
        """修改工单问题类型"""
        self.problem_type = problem_type
        self.save(update_fields=['problem_type'])

    def change_problem_desc(self, problem_desc):
        """修改工单问题描述"""
        self.problem_desc = problem_desc
        self.save(update_fields=['problem_desc'])

    def change_problem_back(self, problem_back):
        """修改工单问题反馈"""
        self.problem_back = problem_back
        self.save(update_fields=['problem_back'])

    def set_dealed(self):
        """设置工单为已处理"""
        self.status = WorkOrder.STATUS_DEALED
        self.save(update_fields=['status'])

    def set_finished(self):
        """设置工单为已完成"""
        self.status = WorkOrder.STATUS_FINISHED
        self.save(update_fields=['status'])







