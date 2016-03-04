# -*- coding: utf-8 -*-
from django.db.models import Count
from django.contrib import admin

from .managers import ApproxCountQuerySet

class BaseAdmin(admin.ModelAdmin):
    
    list_display   = ('id',)
    search_fields  =('id')
    date_hierarchy = None
    save_on_top    = True
    readonly_fields =()
    
    def save_model(self, request, obj, form, change):
        if hasattr(obj,'creator') and not getattr(obj,'creator'):
            obj.creator = request.user.username
        obj.save()
        
        
class ApproxAdmin(BaseAdmin):

    def queryset(self, request):
        qs = super(ApproxAdmin, self).queryset(request)
        return qs._clone(klass=ApproxCountQuerySet)
    
      