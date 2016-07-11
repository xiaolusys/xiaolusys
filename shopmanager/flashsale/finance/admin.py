# coding: utf-8

from django.contrib import admin
from django.http import HttpResponseRedirect
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.http import HttpResponse

import common.utils
from core.filters import DateFieldListFilter
from flashsale.finance.models import Bill, BillRelation
import xlsxwriter
from cStringIO import StringIO

class BillAdmin(admin.ModelAdmin):
    list_display = (
        'show_id', 'supplier', 'type', 'show_relation_objects', 'plan_amount', 'amount', 'show_creater', 'pay_method',
        'created', 'status', 'note')
    search_fields = ['id', "transcation_no", "supplier__id", "supplier__supplier_name", "billrelation__object_id"]
    list_filter = ["type", "status", "pay_method", ('created', DateFieldListFilter)]
    readonly_fields = ('creater', 'supplier')
    list_select_related = True
    list_per_page = 25

    def lookup_allowed(self, lookup, value):
        if lookup in ['billrelation__object_id']:
            return True
        return super(BillAdmin, self).lookup_allowed(lookup, value)


    def show_id(self, obj):
        return '<a href="/sale/finance/bill_list/%d/bill_detail" target="_blank">%d</a>' % (obj.id, obj.id)

    show_id.allow_tags = True
    show_id.short_description = 'ID'

    def show_creater(self, obj):
        return common.utils.get_admin_name(obj.creater)

    show_creater.short_description = '创建人'

    def show_relation_objects(self, obj):
        return render_to_string('finance/bill_relation_objects.html', {'relation_objects':
                                   [{'name':k, 'items':v} for k,v in obj.relation_objects.iteritems()]})

    show_relation_objects.allow_tag = True
    show_relation_objects.short_description = '关联信息'

    def action_merge(self, request, queryset):
        attachment_set = set()
        status_set = set()
        supplier_ids = set()
        bill_ids = []
        is_wrong_pay_method = False
        is_wrong_status = False
        is_wrong_type = False
        bill_notes = []
        plan_amount = .0
        receive_acount_set = set()
        receive_name_set = set()
        for bill in queryset:
            if bill.type == Bill.PAY:
                plan_amount += bill.plan_amount
            elif bill.type == Bill.RECEIVE:
                plan_amount -= bill.plan_amount
            if bill.status in [Bill.STATUS_COMPLETED,Bill.STATUS_DELAY]:
                is_wrong_status = True
            status_set.add(bill.status)
            if bill.type == Bill.DELETE:
                is_wrong_type = True
            if bill.attachment:
                attachment_set.add(bill.attachment)
            supplier_ids.add(bill.supplier_id)
            if bill.pay_method not in [Bill.TAOBAO_PAY, Bill.TRANSFER_PAY, Bill.RECEIVE_DIRECT, Bill.RECEIVE_DEDUCTIBLE]:
                is_wrong_pay_method = True
            if bill.note:
                bill_notes.append(bill.note)
            if bill.receive_account:
                receive_acount_set.add(bill.receive_account)
            if bill.receive_name:
                receive_name_set.add(bill.receive_name)

        redirect_url = '/admin/finance/bill_list/?id__in=%s' % ','.join([str(x) for x in sorted(bill_ids)])
        if is_wrong_type:
            self.message_user(request, u'不能合并已作废的账单')
            return HttpResponseRedirect(redirect_url)
        if is_wrong_status:
            self.message_user(request, u'只能合并已完成的账单')
            return HttpResponseRedirect(redirect_url)
        if is_wrong_pay_method:
            self.message_user(request, u'账单包含错误的支付方式')
            return HttpResponseRedirect(redirect_url)
        if len(attachment_set) > 1:
            self.message_user(request, u'附件不一致')
            return HttpResponseRedirect(redirect_url)
        if len(supplier_ids) > 1:
            self.message_user(request, u'供应商不一致')
            return HttpResponseRedirect(redirect_url)

        if not supplier_ids:
            self.message_user(request, u'账单未关联供应商')
            return HttpResponseRedirect(redirect_url)
        else:
            supplier_id = supplier_ids.pop()

        if attachment_set:
            attachment = attachment_set.pop()
        else:
            attachment = ''
        if receive_acount_set:
            receive_acount = receive_acount_set.pop()
        else:
            receive_acount = ''
        if receive_name_set:
            receive_name = receive_name_set.pop()
        else:
            receive_name = ''
        type_ = Bill.RECEIVE if plan_amount < 0 else Bill.PAY

        merged_bill = Bill(
            type=type_,
            pay_method=Bill.TRANSFER_PAY,
            plan_amount=abs(plan_amount),
            note='\r\n'.join(bill_notes),
            supplier_id=supplier_id,
            attachment=attachment,
            creater=request.user,
            status=min(status_set),
            receive_name=receive_name,
            receive_account=receive_acount
        )
        merged_bill.save()

        n = 0
        for bill in queryset:
            n += 1
            bill.merge_to(merged_bill)
            bill.type = Bill.DELETE
            bill.save()

        self.message_user(request, u'本次合并%d个账单' % n)

    action_merge.short_description = u'合并账单'

    def format_billrelation(self,dict={}):
        a = {'订货付款':[],'订货回款':[],'退货收款':[]}
        # a= {}
        pay = ''
        back = ''
        get = ''
        for i,j in dict.iteritems():
            if i=='订货付款':
                pay = '订货付款：'
                for k in j:
                    pay = pay + k.object_id
            elif i=='订货回款':
                back = '订货回款：'
                for k in j:
                    back = back + k.object_id
            #     a['订货回款'].append((k.object_id for k in j))
            elif i=='退货收款':
                get = '退货收款：'
                for k in j:
                    get = get + k.object_id
            #     a['退货收款'].append((k.object_id for k in j))
            # a[i].append(j)
        return  pay+back+get


    def generate_excel(self, request, queryset):
        buff = StringIO()
        workbook = xlsxwriter.Workbook(buff)
        worksheet = workbook.add_worksheet()
        bold_format = workbook.add_format({"bold":True})
        money_format = workbook.add_format({"num_format":'0.00'})
        worksheet.set_column('A:A',18)
        worksheet.set_column('B:B',30)
        worksheet.set_column('C:C',30)
        worksheet.set_column('D:D',30)
        worksheet.set_column('E:E',30)
        worksheet.set_column('F:F',30)
        worksheet.set_column('G:G',30)
        worksheet.set_column('H:H',30)
        worksheet.set_column('I:I',30)
        worksheet.set_column('J:J',30)
        worksheet.set_column('K:K',30)
        worksheet.write('A6','ID',bold_format)
        worksheet.write('B6','供应商',bold_format)
        worksheet.write('C6','账单类型',bold_format)
        worksheet.write('D6','关联信息',bold_format)
        worksheet.write('E6','计划款额',bold_format)
        worksheet.write('F6','实收款额',bold_format)
        worksheet.write('G6','创建人', bold_format)
        worksheet.write('H6','支付方式',bold_format)
        worksheet.write('I6','创建日期',bold_format)
        worksheet.write('J6','账单状态',bold_format)
        worksheet.write('K6','备注',bold_format)
        row = 7
        for bill in queryset:
            worksheet.write(row,0,bill.id)
            worksheet.write(row,1,bill.supplier.supplier_name)
            worksheet.write(row,2,bill.get_type_display())
            worksheet.write(row,3,self.format_billrelation(bill.relation_objects))
            worksheet.write(row,4,bill.plan_amount)
            worksheet.write(row,5,bill.amount)
            worksheet.write(row,6,bill.creater.username)
            worksheet.write(row,7,bill.get_pay_method_display())
            worksheet.write(row,8,bill.created)
            worksheet.write(row,9,bill.get_status_display())
            worksheet.write(row,10,bill.note)
            row += 1
        workbook.close()
        filename = '%s-%s.xlsx' % (queryset[0],queryset[len(queryset)-1])
        response = HttpResponse(
            buff.getvalue(),
            content_type=
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment;filename=%s' % filename
        return response

    generate_excel.short_description = u'导出excel'

    actions = ['generate_excel','action_merge']

    def get_actions(self, request):
        actions = super(BillAdmin, self).get_actions(request)
        actions.pop('delete_selected')
        return actions

admin.site.register(Bill, BillAdmin)
