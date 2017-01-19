# coding: utf-8
from rest_framework import generics, permissions, renderers, viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework import exceptions
from django.shortcuts import get_object_or_404
from supplychain.supplier.models import SaleSupplier
from rest_framework import authentication

from .. import forms

from flashsale.finance.models import Bill, BillRelation
from django.contrib.contenttypes.models import ContentType
from ..serializers import BillRelationSerializer, BillSerializer


class BillViewSet(viewsets.GenericViewSet):
    serializer_class = BillSerializer
    renderer_classes = (renderers.JSONRenderer, renderers.TemplateHTMLRenderer)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permissions_classes = (permissions.IsAuthenticated,)

    @list_route(methods=['post'])
    def pre_bill_create(self,request):
        plan_money = request.POST.get("plan_money")
        receiver_name = request.POST.get("receiver_name")
        receiver_account = request.POST.get("receiver_account")
        supplier_id = request.POST.get("supplier_id")
        bill_id = 0
        if not all([plan_money,receiver_name,receiver_account,supplier_id]):
            info = {"reason": "信息不完整", "supplier_id": supplier_id, "bill_id": bill_id}
            return Response(info)
        user = request.user
        sale_supplier = SaleSupplier.objects.filter(id=supplier_id)
        if not sale_supplier or not supplier_id:
            info = {"reason":"供应商不存在","supplier_id":supplier_id,"bill_id":bill_id}
            return Response(info)
        bill_info = {"plan_amount":plan_money,"receive_name":receiver_name,
                     "receive_account":receiver_account,"supplier_id":sale_supplier.first().id,"creater":user,
                     "type":-1,"status":0,"pay_method":6}
        print bill_info
        bill_id = Bill.objects.create(**bill_info)
        info = {"reason": "创建预付款账单成功", "supplier_id": supplier_id, "bill_id": bill_id.id,"supplier_name":bill_id.supplier.supplier_name}
        return Response(info)

    @list_route(methods=['get'])
    def bill_create(self,request):
        return Response(template_name=u"finance/create_bill.html")


    @detail_route(methods=['get'])
    def bill_detail(self, request, pk, format='html'):
        bill = Bill.objects.get(id=pk)
        deal = False
        confirm = False
        pay_deal = False
        bill_status = True

        if bill.type in [Bill.RECEIVE]:
            if bill.status == Bill.STATUS_PENDING:
                deal = True
            if bill.status == Bill.STATUS_DEALED:
                confirm = True

        if bill.type in [Bill.PAY]:
            pay_deal = True

        if bill.status == 2:
            bill_status = False

        ro = [{'name':k, 'items':[{'object_id':br.object_id, 'bill_amount':br.bill.amount, 'object_url':br.object_url()} for br in v]} for k,v in bill.relation_objects.iteritems()]
        # for i in ro:
        #     i['items'] = i['items'][0]
        # ro = {'a':1,'b':2,'c':3}
        result = {
            'id': bill.id,
            'supplier_name': bill.supplier.supplier_name,
            'type': dict(Bill.TYPE_CHOICES)[bill.type],
            'status': dict(Bill.STATUS_CHOICES)[bill.status],
            'created': bill.created.strftime('%y年%m月%d %H:%M:%S'),
            'pay_method': dict(Bill.PAY_CHOICES)[bill.pay_method],
            'plan_amount': bill.plan_amount,
            'amount': bill.amount,
            'receive_account': bill.receive_account,
            'receive_name': bill.receive_name,
            'transaction_no': bill.transcation_no,
            'relation_objects': ro,
            'attachment': bill.attachment,
            'confirm': confirm,
            'note': bill.note,
            'deal': deal,
            'pay_deal': pay_deal,
            'bill_status': bill_status
        }
        return Response(result, template_name=u"finance/bill_detail.html")

    @detail_route(methods=['post'])
    def confirm_bill(self,request, pk):
        form = forms.ConfirmBillForm(request.POST)
        if not form.is_valid():
            return Response({"res": False, "data": [], "desc": "参数错误"})
        bill = get_object_or_404(Bill, id=pk)
        bill.transcation_no = form.cleaned_data['transaction_no']
        bill.amount = form.cleaned_data['amount']
        bill.status = Bill.STATUS_COMPLETED
        bill.save()
        ctype = ContentType.objects.get(app_label='dinghuo', model='orderlist')
        brs = BillRelation.objects.filter(bill_id=pk, content_type_id=ctype.id)  # 获取非退货状态下的orderlist
        if brs.count():
            for br in brs:
                br.set_orderlist_stage()
        for bill_relation in bill.billrelation_set.all():
            relation_object = bill_relation.get_based_object()
            if hasattr(relation_object, 'confirm'):
                relation_object.confirm()
        return Response({"res": True, "data": [], "desc": ""})

    @detail_route(methods=['post'])
    def deal(self, request, pk):
        form = forms.DealForm(request.POST)
        if not form.is_valid():
            raise exceptions.APIException(form.error_message)
        bill = get_object_or_404(Bill, id=pk)
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
        return Response({'bill_id': bill.id})

    @detail_route(methods=['post'])
    def pay_bill(self, request, pk):
        pay_no = request.POST.get("pay_no", None)
        pay_amount = float(request.POST.get("pay_amount", None))
        Bill.objects.filter(id=pk).update(transcation_no=pay_no, amount=pay_amount, status=Bill.STATUS_DEALED)
        return Response({'bill_id': pk})

    @detail_route(methods=['post'])
    def finish_bill(self, request, pk):
        bill = get_object_or_404(Bill, id=pk)
        bill.finish()
        return Response({'bill_id': pk})

    @detail_route(methods=['POST'])
    def change_note(self, request, pk):
        note = request.POST.get("note", None)
        Bill.objects.filter(id=pk).update(note=note)
        return Response({'bill_id': pk})
