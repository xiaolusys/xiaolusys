# -*- coding:utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from core.models import BaseModel
from django.contrib.contenttypes.models import ContentType
from supplychain.supplier.models import SaleSupplier


class Bill(BaseModel):
    PAY = -1
    DELETE = 0
    RECEIVE = 1


    TYPE_CHOICES = (
        (PAY, '付款'),
        (DELETE, '作废'),
        (RECEIVE, '收款')
    )

    STATUS_PENDING = 0
    STATUS_DEALED = 1
    STATUS_COMPLETED = 2
    STATUS_CHOICES = (
        (STATUS_PENDING, '待处理'),
        (STATUS_DEALED, '已处理'),
        (STATUS_COMPLETED, '已完成')
    )

    type = models.IntegerField(choices=TYPE_CHOICES, verbose_name=u'账单类型')
    status = models.IntegerField(choices=STATUS_CHOICES, verbose_name=u'账单状态')
    creater = models.ForeignKey(User, verbose_name=u'创建人')
    PC_COD_TYPE = 11  # 货到付款
    PC_PREPAID_TYPE = 12  # 预付款
    PC_POD_TYPE = 13  # 付款提货
    PC_OTHER_TYPE = 14  # 其它
    RECEIVE_DIRECT = 4
    RECEIVE_DEDUCTIBLE = 5
    PURCHASE_PAYMENT_TYPE = (
        (PC_COD_TYPE, u'货到付款'),
        (PC_PREPAID_TYPE, u'预付款'),
        (PC_POD_TYPE, u'付款提货'),
        (PC_OTHER_TYPE, u'其它'),
    )
    bill_method = models.IntegerField(choices=PURCHASE_PAYMENT_TYPE, default=PC_COD_TYPE, verbose_name=u'付款类型')
    plan_amount = models.FloatField(verbose_name=u'计划款额')
    amount = models.FloatField(default=0, verbose_name=u'实收款额')
    PAY_CHOICES = ((1, u'淘宝代付'), (2, u'转款'), (3, u"自付"),
                   (RECEIVE_DIRECT, u'直退'),
                   (RECEIVE_DEDUCTIBLE, u'余额抵扣'))
    pay_method = models.IntegerField(choices=PAY_CHOICES, verbose_name=u'支付方式')
    pay_taobao_link = models.TextField(null=True, verbose_name=u'淘宝链接')
    # receive_method = models.IntegerField(choices=((1, u'直退'), (2, u'余额抵扣')), verbose_name=u'收款方式')
    receive_account = models.CharField(max_length=50, null=True, verbose_name=u'收款账号')
    receive_name = models.CharField(max_length=16, null=True, verbose_name=u'收款账号')
    pay_account = models.TextField(null=True, verbose_name=u'付款账号')
    transcation_no = models.CharField(max_length=100, null=True, verbose_name=u'交易单号')
    attachment = models.CharField(max_length=128, blank=True, verbose_name=u'附件')
    delete_reason = models.CharField(max_length=100, null=True, verbose_name=u'作废理由')
    note = models.CharField(max_length=100, verbose_name=u'备注')
    # -----------冗余备查询字段--------------
    supplier = models.ForeignKey(SaleSupplier, null=True, verbose_name=u'供应商')

    class Meta:
        db_table = 'finance_bill'
        app_label = 'finance'
        verbose_name = u'账单记录'
        verbose_name_plural = u'账单列表'

    @staticmethod
    def create(relations, num, plan_amount, amount):
        return

    def relate_to(self, relations, lack_dict={}):
        from flashsale.dinghuo.models import ReturnGoods, OrderDetail
        for r in relations:
            rtype = lack_dict.get(r.id)
            ctype = None
            if type(r) == ReturnGoods:
                ctype = ContentType.objects.get(app_label='dinghuo',model='returngoods')
                if not rtype:
                    rtype = 3
            elif type(r) == OrderDetail:
                ctype = ContentType.objects.get(app_label='dinghuo',model='orderdetail')
                if not rtype:
                    rtype = 1
            else:
                raise Exception(u'暂未支持其它类型')
            BillRelation(bill_id=self.id,
                         content_type=ctype,
                         object_id=r.id,
                         type=rtype).save()
    @property
    def relation_objects(self):
        objects = []
        for bill_relation in self.billrelation_set.order_by('id'):
            object_dict = {
                'type': dict(BillRelation.TYPE_CHOICES)[bill_relation.type],
                'object_id': bill_relation.object_id
            }
            content_object = bill_relation.get_based_object()
            if hasattr(content_object, 'bill_relation_dict'):
                object_dict.update(content_object.bill_relation_dict)
            objects.append(object_dict)
        return objects

class BillRelation(BaseModel):
    TYPE_DINGHUO_PAY = 1
    TYPE_DINGHUO_RECEIVE = 2
    TYPE_RETURNGOODS_RECEIVE = 3

    TYPE_CHOICES = (
        (TYPE_DINGHUO_PAY, u'订货付款'),
        (TYPE_DINGHUO_RECEIVE, u'订货回款'),
        (TYPE_RETURNGOODS_RECEIVE, u'退货收款')
    )

    class Meta:
        db_table = 'finance_billrelation'
        app_label = 'finance'
        verbose_name = u'账单记录关联'
        verbose_name_plural = u'账单记录关联列表'
    bill = models.ForeignKey(Bill)
    content_type = models.ForeignKey(ContentType, verbose_name=u'对象类型', db_index=True, blank=True, null=True)
    object_id = models.TextField(verbose_name=u'对象id', blank=True, null=True)
    type = models.IntegerField(choices=TYPE_CHOICES)

    def get_based_object(self):
        """
            returns the edited object represented by this log entry
        """
        return self.content_type.get_object_for_this_type(pk=self.object_id)
