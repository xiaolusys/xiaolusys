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
    result = {
        'id': bill.id,
        'supplier_name': bill.supplier.supplier_name,
        'type': dict(Bill.TYPE_CHOICES)[bill.type],
        'status': dict(Bill.STATUS_CHOICES)[bill.status],
        'created': bill.created.strftime('%y年%m月%d %H:%M:%S'),
        'bill_method': dict(Bill.PURCHASE_PAYMENT_TYPE)[bill.bill_method],
        'pay_method': dict(Bill.PAY_CHOICES)[bill.pay_method],
        'plan_amount': bill.plan_amount,
        'amount': bill.amount,
        'transaction_no': bill.transcation_no,
        'relation_objects': bill.relation_objects,
        'show_confirm': bill.status == Bill.STATUS_PENDING,
        'attachment': bill.attachment
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
    return {'code': 0}
