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
        (PAY, u'付款'),
        (DELETE, u'作废'),
        (RECEIVE, u'收款')
    )
    STATUS_DELAY = -1
    STATUS_PENDING = 0
    STATUS_DEALED = 1
    STATUS_COMPLETED = 2
    STATUS_CHOICES = (
        (STATUS_DELAY, u"延期处理"),
        (STATUS_PENDING, u'待处理'),
        (STATUS_DEALED, u'已处理'),
        (STATUS_COMPLETED, u'已完成')
    )

    type = models.IntegerField(choices=TYPE_CHOICES, verbose_name=u'账单类型')
    status = models.IntegerField(choices=STATUS_CHOICES, verbose_name=u'账单状态')
    creater = models.ForeignKey(User, verbose_name=u'创建人')
    PC_COD_TYPE = 11  # 货到付款
    PC_PREPAID_TYPE = 12  # 预付款
    PC_POD_TYPE = 13  # 付款提货
    PC_OTHER_TYPE = 14  # 其它
    TAOBAO_PAY = 1
    TRANSFER_PAY = 2
    SELF_PAY = 3
    RECEIVE_DIRECT = 4
    RECEIVE_DEDUCTIBLE = 5
    ALI_PAY = 6
    PURCHASE_PAYMENT_TYPE = (
        (PC_COD_TYPE, u'货到付款'),
        (PC_PREPAID_TYPE, u'预付款'),
        (PC_POD_TYPE, u'付款提货'),
        (PC_OTHER_TYPE, u'其它'),
    )
    plan_amount = models.FloatField(verbose_name=u'计划款额')
    amount = models.FloatField(default=0, verbose_name=u'实收款额')
    PAY_CHOICES = ((TAOBAO_PAY, u'支付宝'), (ALI_PAY, u'代付'), (TRANSFER_PAY, u'转款'), (SELF_PAY, u"自付"),
                   (RECEIVE_DIRECT, u'直退'), (RECEIVE_DEDUCTIBLE, u'余额抵扣'))
    pay_method = models.IntegerField(choices=PAY_CHOICES, verbose_name=u'支付方式')
    pay_taobao_link = models.TextField(null=True, blank=True, verbose_name=u'淘宝链接')
    # receive_method = models.IntegerField(choices=((1, u'直退'), (2, u'余额抵扣')), verbose_name=u'收款方式')
    receive_account = models.CharField(max_length=50, null=True, blank=True, verbose_name=u'收款账号')
    receive_name = models.CharField(max_length=16, null=True, blank=True, verbose_name=u'收款人姓名')
    pay_account = models.TextField(null=True, blank=True, verbose_name=u'付款账号')
    transcation_no = models.CharField(max_length=100, null=True, blank=True, verbose_name=u'交易单号')
    attachment = models.CharField(max_length=128, blank=True, verbose_name=u'附件')
    delete_reason = models.CharField(max_length=100, null=True, blank=True, verbose_name=u'作废理由')
    note = models.CharField(max_length=100, blank=True, verbose_name=u'备注')
    # -----------冗余备查询字段--------------
    supplier = models.ForeignKey(SaleSupplier, null=True, verbose_name=u'供应商')

    class Meta:
        db_table = 'finance_bill'
        app_label = 'finance'
        verbose_name = u'账单记录'
        verbose_name_plural = u'账单列表'

    @staticmethod
    def create(relations, type, status, pay_method, plan_amount, amount,supplier, user_id, receive_account='', receive_name='',
               pay_taobao_link='',transcation_no='', note=''):
        bill = Bill(type=type,
                    status=status,
                    plan_amount=plan_amount,
                    amount=amount,
                    pay_method=pay_method,
                    supplier=supplier,
                    creater_id=user_id,
                    receive_account=receive_account,
                    receive_name=receive_name,
                    pay_taobao_link=pay_taobao_link,
                    transcation_no=transcation_no,
                    note=note)
        bill.save()
        bill.relate_to(relations)
        return bill

    @staticmethod
    def check_merge(bills):
        if Bill.DELETE in {b.type for b in bills}:
            raise Exception(u"不能合并已经作废的账单")
        supplier_ids = {b.supplier_id for b in bills}
        if len(supplier_ids) > 1:
            raise Exception(u"不能合并不同供应商的账单")
        if Bill.STATUS_COMPLETED in {b.status for b in bills}:
            raise Exception(u"不能合并已经完成的账单")
        pay_method_set = {b.pay_method for b in bills}
        if Bill.SELF_PAY in pay_method_set:
            raise Exception(u"有自付不能合单")

    @staticmethod
    def merge(bills, creater):
        receive_account = bills[0].receive_account
        plan_amount = sum([b.plan_amount*b.type for b in bills])
        type_ = plan_amount / abs(plan_amount) if plan_amount else 0
        status_set = {b.status for b in bills}
        if Bill.STATUS_PENDING in status_set or Bill.STATUS_DELAY in status_set:
            status = Bill.STATUS_PENDING
        else:
            status = Bill.STATUS_DEALED
        merged_bill = Bill(
            receive_name=bills[0].receive_name,
            receive_account=receive_account,
            type=type_,
            pay_method=Bill.TRANSFER_PAY,
            plan_amount=abs(plan_amount),
            note='\r\n'.join([b.note for b in bills]),
            supplier_id=bills[0].supplier_id,
            attachment=bills[0].attachment,
            creater=creater,
            status=status
        )
        merged_bill.save()
        for bill in bills:
            bill.merge_to(merged_bill)

    def merge_to(self, bill):
        for bill_relation in self.billrelation_set.all():
            BillRelation.objects.get_or_create(
                bill=bill,
                content_type=bill_relation.content_type,
                object_id=bill_relation.object_id,
                type=bill_relation.type
            )
        self.type = Bill.DELETE
        self.save()

    def split(self, amount):
        new_b = Bill()
        all_attrs = [i.column for i in Bill._meta.fields]
        for attr in all_attrs:
            val = getattr(self, attr)
            setattr(new_b, attr, val)
        new_b.id = None
        new_b.amount = amount
        new_b.note += u"自账单%d拆分而得" % (self.id,)
        new_b.save()
        self.note += u"账单原额%d,拆分得到新账单%d" % (new_b.amount ,new_b.id)
        self.amount -= amount
        self.save()
        # self.billrelation_set.update()

    def relate_to(self, relations, lack_dict={}):
        from flashsale.dinghuo.models import ReturnGoods, OrderList
        for r in relations:
            rtype = lack_dict.get(r.id)
            ctype = None
            if type(r) == ReturnGoods:
                ctype = ContentType.objects.get(app_label='dinghuo',model='returngoods')
                if not rtype:
                    rtype = 3
            elif type(r) == OrderList:
                ctype = ContentType.objects.get(app_label='dinghuo',model='orderlist')
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
        objects = {}
        for bill_relation in self.billrelation_set.order_by('id'):
            if bill_relation.get_type_display() not in objects:
                objects[bill_relation.get_type_display()] = []
            zf_plan_amount = BillRelation.objects.filter(content_type=bill_relation.content_type, type=bill_relation.type,
                                              object_id=bill_relation.object_id).first().bill.plan_amount
            bill_relation.zf_plan_amount=zf_plan_amount
            objects[bill_relation.get_type_display()].append(bill_relation)
            print bill_relation.zf_plan_amount
        print objects
        return objects

    def get_orderlist(self):
        return self.billrelation_set.first().get_based_object()

    def get_merged_parent_bill(self):
        if self.type == Bill.DELETE:
            my_object_id = self.billrelation_set.all().first().object_id
            my_content_type = self.billrelation_set.all().first().content_type
            my_billrelation_id = self.billrelation_set.all().first().id
            merged_bill = BillRelation.objects.filter(object_id=my_object_id, content_type=my_content_type).exclude(id=my_billrelation_id).first().bill
            return merged_bill
            # merged_bill_id = merged_bill.id
            # return merged_bill_id
        else:
            return self.id




    def is_merged(self):
        return self.billrelation_set.count() > 1

    def is_finished(self):
        return self.status == Bill.STATUS_COMPLETED

    def set_orderlist_stage(self):
        for relation in self.billrelation_set.all():
            orderlist = relation.get_based_object()
            # if

    def finish(self):
        """
            货到付款:结算时生成新账单计算金额，账单完成时将订货单设置为完成。
            其它：更新OrderList状态ReturnGoods状态。
        """
        from flashsale.dinghuo.models import OrderList, ReturnGoods
        self.status = Bill.STATUS_COMPLETED
        self.save()
        brs = self.billrelation_set.filter(bill_id=self.id)
        for br in brs:
            obj = br.get_based_object()
            if type(obj) == OrderList:
                obj.update_stage()
            elif type(obj) == ReturnGoods:
                obj.confirm()

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

    def object_url(self):
        tyc = {
            1:'/sale/dinghuo/changedetail/%s/' %(self.object_id),
            3:'/admin/dinghuo/returngoods/%s/' %(self.object_id),
            2:'/sale/dinghuo/changedetail/%s/' %(self.object_id),
        }
        return tyc[self.type]

    def set_orderlist_stage(self):
        from flashsale.dinghuo.models import OrderList
        ol = self.get_based_object()
        if self.type == BillRelation.TYPE_DINGHUO_RECEIVE:   #退货回款 订货单状态直接完成
            ol.set_stage_complete()
        elif self.type == BillRelation.TYPE_DINGHUO_PAY and ol.bill_method == OrderList.PC_COD_TYPE: #在货到付款情况下，订单状态完成
            if not ol.third_package:
                ol.set_stage_complete()
        elif self.type == BillRelation.TYPE_DINGHUO_PAY and ol.bill_method == OrderList.PC_POD_TYPE: #在付款提货状态下，订单状态为收货
            ol.set_stage_receive(OrderList.PC_POD_TYPE)
        ol.save()
