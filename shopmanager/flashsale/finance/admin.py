# coding: utf-8

from django.contrib import admin
from django.http import HttpResponseRedirect
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

import common.utils
from core.filters import DateFieldListFilter
from flashsale.finance.models import Bill, BillRelation


class BillAdmin(admin.ModelAdmin):
    list_display = (
        'show_id', 'supplier', 'type', 'show_relation_objects', 'plan_amount', 'amount', 'show_creater', 'pay_method',
        'created', 'status', 'note')
    search_fields = ['id', "transcation_no", "supplier__id", "supplier__supplier_name"]
    list_filter = ["type", "status", "pay_method", ('created', DateFieldListFilter)]
    readonly_fields = ('creater', 'supplier')
    list_select_related = True
    list_per_page = 25

    def show_id(self, obj):
        return '<a href="/sale/finance/bill/%d/" target="_blank">%d</a>' % (obj.id, obj.id)

    show_id.allow_tags = True
    show_id.short_description = 'ID'

    def show_creater(self, obj):
        return common.utils.get_admin_name(obj.creater)

    show_creater.short_description = '创建人'

    def show_relation_objects(self, obj):
        relation_objects_dict = {}
        for bill_relation in obj.billrelation_set.all():
            relation_object = bill_relation.get_based_object()
            if hasattr(relation_object, 'bill_relation_dict'):
                relation_objects_dict.setdefault(bill_relation.type, []).append(relation_object.bill_relation_dict)
        relation_objects = []
        for k in sorted(relation_objects_dict.keys()):
            relation_objects.append({
                'name': dict(BillRelation.TYPE_CHOICES)[k],
                'items': sorted(relation_objects_dict[k], key=lambda x: x['object_id'])
            })
        return render_to_string('finance/bill_relation_objects.html', {'relation_objects': relation_objects})

    show_relation_objects.allow_tag = True
    show_relation_objects.short_description = '关联信息'

    def action_merge(self, request, queryset):
        attachment_set = set()
        supplier_ids = set()
        bill_ids = []
        is_wrong_pay_method = False
        is_wrong_status = False
        is_wrong_type = False
        bill_notes = []

        plan_amount = .0
        for bill in queryset:
            if bill.type == Bill.PAY:
                plan_amount += bill.plan_amount
            elif bill.type == Bill.RECEIVE:
                plan_amount -= bill.plan_amount
            if bill.status in [Bill.STATUS_COMPLETED]:
                is_wrong_status = True
            if bill.type == Bill.DELETE:
                is_wrong_type = True
            if bill.attachment:
                attachment_set.add(bill.attachment)
            supplier_ids.add(bill.supplier_id)
            if bill.pay_method not in [Bill.TRANSFER_PAY, Bill.RECEIVE_DIRECT, Bill.RECEIVE_DEDUCTIBLE]:
                is_wrong_pay_method = True
            if bill.note:
                bill_notes.append(bill.note)

        redirect_url = '/admin/finance/bill/?id__in=%s' % ','.join([str(x) for x in sorted(bill_ids)])
        if is_wrong_type:
            self.message_user(request, u'不能合并已作废的账单')
            return HttpResponseRedirect(redirect_url)
        if is_wrong_status:
            self.message_user(request, u'只能合并待处理的账单')
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
        type_ = Bill.RECEIVE if plan_amount < 0 else Bill.PAY

        merged_bill = Bill(
            type=type_,
            pay_method=Bill.TRANSFER_PAY,
            plan_amount=abs(plan_amount),
            note='\r\n'.join(bill_notes),
            supplier_id=supplier_id,
            attachment=attachment,
            creater=request.user,
            status=0
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

    actions = ['action_merge']

    def get_actions(self, request):
        actions = super(BillAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions


admin.site.register(Bill, BillAdmin)
