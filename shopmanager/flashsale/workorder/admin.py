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
        'id', 'problem_title','problem_type','problem_desc','status','is_valid','dealed_part','raised_part','problem_back',
        'created_time','start_time','modified_time','closed_time','creater',"dealer","content_imgs"
    )
    search_fields = ['id','creater','dealer','dealed_part','raised_part','status']
    list_filter = [('created_time',DateFieldListFilter)]
    # actions = ['start_deal','confirm_finished']

    list_filter = ["status", "is_valid", ('created_time', DateFieldListFilter),("modified_time",DateFieldListFilter),"raised_part","dealed_part"]

    readonly_fields = ['modified_time','start_time','closed_time']


    # def confirm_finished(self, request, queryset):
    #     for p in queryset:
    #         if p.status != WorkOrder.STATUS_FINISHED:
    #             p.status = WorkOrder.STATUS_FINISHED
    #             p.dealer = request.user.username
    #             p.modified_time = datetime.datetime.now()
    #             p.save()
    #
    # confirm_finished.short_description = u'处理完成'
    #
    #
    # def start_deal(self, request, queryset):
    #     for p in queryset:
    #         if p.status == WorkOrder.STATUS_PENDING:
    #             p.status = WorkOrder.STATUS_DEALING
    #             p.modified_time = datetime.datetime.now()
    #             p.dealer = request.user.username
    #             p.save()
    #
    # start_deal.short_description = u'开始处理'


    # def selfactions(self, obj):
    #     if obj.status != WorkOrder.STATUS_FINISHED:
    #         return '''<button type="button" id="orderwork_{orderwork_id}" class="respond">确认处理完成</button>'''.format(
    #             orderwork_id=obj.id)
    #     return ''

    # selfactions.allow_tags = True
    # selfactions.short_description = u'操作'


admin.site.register(WorkOrder, WorkOrderAdmin)