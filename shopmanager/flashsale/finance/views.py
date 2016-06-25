# coding: utf-8

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

import common.utils
from flashsale.finance.models import Bill,BillRelation
from flashsale.dinghuo.models import OrderList

from common.decorators import jsonapi
from . import forms


@staff_member_required
def bill_detail(request, bill_id):
    bill = Bill.objects.get(id=bill_id)
    deal = False
    confirm = False
    pay_deal = False

    if bill.type in [ Bill.RECEIVE]:
        if bill.status == Bill.STATUS_PENDING:
            deal = True
        if bill.status == Bill.STATUS_DEALED:
            confirm = True

    if bill.type in [Bill.PAY]:
        pay_deal = True
    result = {
        'id': bill.id,
        'supplier_name': bill.supplier.supplier_name,
        'type': dict(Bill.TYPE_CHOICES)[bill.type],
        'status': dict(Bill.STATUS_CHOICES)[bill.status],
        'created': bill.created.strftime('%y年%m月%d %H:%M:%S'),
        'pay_method': dict(Bill.PAY_CHOICES)[bill.pay_method],
        'plan_amount': bill.plan_amount,
        'amount': bill.amount,
        'receive_account':bill.receive_account,
        'receive_name' : bill.receive_name,
        'transaction_no': bill.transcation_no,
        'relation_objects': bill.relation_objects,
        'attachment': bill.attachment,
        'confirm': confirm,
        'note': bill.note,
        'deal': deal,
        "pay_deal": pay_deal,
    }
    return render(request, 'finance/bill_detail.html', result)


@staff_member_required
@jsonapi
def confirm_bill(request):
    form = forms.ConfirmBillForm(request.POST)
    if not form.is_valid():
        raise Exception('参数错误')

    bill = Bill.objects.get(id=form.cleaned_data['bill_id'])
    bill.transcation_no = form.cleaned_data['transaction_no']
    bill.amount = form.cleaned_data['amount']
    bill.status = Bill.STATUS_COMPLETED
    bill.save()

    for bill_relation in bill.billrelation_set.all():
        relation_object = bill_relation.get_based_object()
        if hasattr(relation_object, 'confirm'):
            relation_object.confirm()
    return {'code': 0}


@staff_member_required
@jsonapi
def deal(request):
    form = forms.DealForm(request.POST)
    if not form.is_valid():
        return {'code': 1, 'msg': '参数错误'}

    bill = Bill.objects.get(id=form.cleaned_data['bill_id'])
    for bill_relation in bill.billrelation_set.all():
        relation_object = bill_relation.get_based_object()
        if hasattr(relation_object, 'deal'):
            relation_object.deal(form.cleaned_data['attachment'])

    bill.receive_method = form.cleaned_data['receive_method']
    bill.plan_amount = form.cleaned_data['amount']
    bill.note = '\r\n'.join([x for x in [bill.note, form.cleaned_data['note']]])
    bill.attachment = form.cleaned_data['attachment']
    bill.status = Bill.STATUS_DEALED
    bill.transcation_no = form.cleaned_data['transaction_no']
    bill.save()
    return {'bill_id': bill.id}

@staff_member_required
@jsonapi
def pay_bill(request):
    pay_no = request.REQUEST.get("pay_no", None)
    pay_amount = float(request.REQUEST.get("pay_amount", None))
    bill_id = int(request.REQUEST.get("bill_id", None))
    Bill.objects.filter(id = bill_id).update(transcation_no=pay_no,amount=pay_amount,status=Bill.STATUS_DEALED)
    return {'bill_id':bill_id}

@staff_member_required
@jsonapi
def finish_bill(request):
    bill_id = int(request.REQUEST.get("bill_id", None))
    Bill.objects.filter(id=bill_id).update(status=Bill.STATUS_COMPLETED)
    orderlist = BillRelation.objects.get(bill_id=bill_id).object_id
    OrderList.objects.filter(id=orderlist).update(status=OrderList.BE_PAID)
    return {'bill_id': bill_id}

@staff_member_required
@jsonapi
def change_note(request):
    note = request.REQUEST.get("note",None)
    bill_id = int(request.REQUEST.get("bill_id",None))
    Bill.objects.filter(id = bill_id).update(note = note)
    return {'bill_id':bill_id}
