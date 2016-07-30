# -*- coding: utf-8 -*-
__author__ = 'huazi'

from django.contrib import admin
from django.template.loader import render_to_string
from django.http import HttpResponse
import common.utils
from core.filters import DateFieldListFilter
from flashsale.workorder.models import WorkOrder
import datetime

class WorkOrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'problem_title','problem_type','problem_desc','status','is_valid','problem_back',
        'created_time','modified_time','creater',"dealer"
    )
    search_fields = ['id']
    list_filter = [('created_time',DateFieldListFilter)]
    actions = ['start_deal','confirm_finished']

    readonly_fields = ['modified_time']

    def confirm_finished(self, request, queryset):
        for p in queryset:
            if p.status != WorkOrder.STATUS_FINISHED:
                p.status = WorkOrder.STATUS_FINISHED
                p.dealer = request.user.username
                p.modified_time = datetime.datetime.now()
                p.save()

    confirm_finished.short_description = u'处理完成'


    def start_deal(self, request, queryset):
        for p in queryset:
            if p.status == WorkOrder.STATUS_PENDING:
                p.status = WorkOrder.STATUS_DEALING
                p.modified_time = datetime.datetime.now()
                p.dealer = request.user.username
                p.save()

    start_deal.short_description = u'开始处理'


    # def selfactions(self, obj):
    #     if obj.status != WorkOrder.STATUS_FINISHED:
    #         return '''<button type="button" id="orderwork_{orderwork_id}" class="respond">确认处理完成</button>'''.format(
    #             orderwork_id=obj.id)
    #     return ''

    # selfactions.allow_tags = True
    # selfactions.short_description = u'操作'


admin.site.register(WorkOrder, WorkOrderAdmin)