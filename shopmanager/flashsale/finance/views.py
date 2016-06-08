# coding: utf-8

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

import common.utils
from flashsale.finance.models import Bill

from common.decorators import jsonapi
from . import forms


@staff_member_required
def bill_detail(request, bill_id):
    bill = Bill.objects.get(id=bill_id)
    deal = False
    confirm = False

    if bill.type in [Bill.PAY, Bill.RECEIVE]:
        if bill.status == Bill.STATUS_PENDING:
            deal = True
        if bill.status == Bill.STATUS_DEALED:
            confirm = True

    result = {
        'id': bill.id,
        'supplier_name': bill.supplier.supplier_name,
        'type': dict(Bill.TYPE_CHOICES)[bill.type],
        'status': dict(Bill.STATUS_CHOICES)[bill.status],
        'created': bill.created.strftime('%y年%m月%d %H:%M:%S'),
        'pay_method': dict(Bill.PAY_CHOICES)[bill.pay_method],
        'plan_amount': bill.plan_amount,
        'amount': bill.amount,
        'transaction_no': bill.transcation_no,
        'relation_objects': bill.relation_objects,
        'attachment': bill.attachment,
        'confirm': confirm,
        'deal': deal
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
