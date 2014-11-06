#-*- coding:utf-8 -*-
from django.http import HttpResponseRedirect  
from django.contrib import admin
from django.db import models
from django.conf import settings
from django.contrib import messages
from django.forms import TextInput, Textarea
from django.core.urlresolvers import reverse

from shopback.base import log_action,User, ADDITION, CHANGE
from shopback.base.options import DateFieldListFilter
from shopback import paramconfig as pcfg
from .models import InterceptTrade
from common.utils import update_model_fields


class InterceptTradeAdmin(admin.ModelAdmin):
    
    list_display = ('id','buyer_nick','buyer_mobile','serial_no','trade_id','created','modified','status')
    search_fields = ['buyer_nick','buyer_mobile','serial_no']
    
    list_filter = ('status',)
    
    class Media:
        css = {"all": ("admin/css/forms.css","css/admin/dialog.css", "jquery/jquery-ui-1.10.1.css")}
        js = ("script/admin/adminpopup.js","jquery/jquery-ui-1.8.13.min.js",
              "jquery/addons/jquery.upload.js","intercept/js/trade.csvfile.upload.js")
    
    def intercept_trade_action(self,request,queryset):
        
        queryset  = queryset.filter(status=InterceptTrade.UNCOMPLETE)
        
        for itrade in queryset:
            trades = InterceptTrade.objects.getTradeByInterceptInfo(itrade.buyer_nick,
                                                                     itrade.buyer_mobile,
                                                                     itrade.serial_no)

            if not trades or trades.count() == 0:
                messages.warning(request,u'订单[ %s, %s, %s ]拦截失败'%(itrade.buyer_nick,
                                                                    itrade.buyer_mobile,
                                                                    itrade.serial_no))
                continue
            
            for merge_trade in trades:
                merge_trade.append_reason_code(pcfg.NEW_MEMO_CODE)
                merge_trade.sys_memo += u"【订单被拦截】"
                
                update_model_fields(merge_trade,update_fields=['sys_status',
                                                                'sys_memo'])
                
                log_action(request.user.id,merge_trade,CHANGE, u'订单被拦截')
                
            itrade.trade_id = merge_trade.id
            itrade.status   = InterceptTrade.COMPLETE
            itrade.save()
            
        return HttpResponseRedirect(reverse('admin:intercept_intercepttrade_changelist'))
        
    intercept_trade_action.short_description = u"拦截订单"
    
    actions = ['intercept_trade_action',]
    
    
admin.site.register(InterceptTrade, InterceptTradeAdmin) 


