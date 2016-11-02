# -*- coding: utf-8 -*-
from django.contrib import admin
from .models import BatchNumberGroup, BatchNumberOid


class ExamAdmin(admin.ModelAdmin):
    list_display = ('batch_number', 'group', 'created',)


admin.site.register(BatchNumberGroup, ExamAdmin)


class ExamPaperAdmin(admin.ModelAdmin):
    list_display = ('batch_number', 'out_sid', 'number', 'group', 'created', 'status',)


admin.site.register(BatchNumberOid, ExamPaperAdmin)
