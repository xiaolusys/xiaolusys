#-*- coding:utf8 -*-
import datetime
from django.contrib import admin
from django.http import HttpResponse,HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.template import RequestContext
from shopback.users.models import User,Customer
from shopback import paramconfig as pcfg



class UserAdmin(admin.ModelAdmin):
    list_display = ('id','top_session','has_fenxiao','visitor_id','uid','nick','is_primary','sync_stock','percentage','status')
    list_display_links = ('id', 'nick')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    #date_hierarchy = 'modified'
    #ordering = ['created_at']

    list_filter = ('status',)
    search_fields = ['nick','craw_keywords','craw_trade_seller_nicks']
    
    #更新用户待发货订单
    def pull_user_unpost_trades(self,request,queryset):
        
        from shopback.orders.tasks import saveUserDuringOrdersTask
        from shopback.fenxiao.tasks import saveUserPurchaseOrderTask
        
        pull_users = []
        for user in queryset:
            pull_dict = {'uid':user.visitor_id,'nick':user.nick}
            try:
                #更新等待发货商城订单
                saveUserDuringOrdersTask.delay(user.visitor_id,status=pcfg.WAIT_SELLER_SEND_GOODS)
            
                #更新待发货分销订单
                saveUserPurchaseOrderTask.delay(user.visitor_id,status=pcfg.WAIT_SELLER_SEND_GOODS)
            except Exception,exc:
                pull_dict['success']=False
                pull_dict['errmsg']=exc.message or '%s'%exc
            else:
                pull_dict['success']=True
            pull_users.append(pull_dict)
       
        return render_to_response('users/pull_wait_post_trade.html',{'users':pull_users},
                                  context_instance=RequestContext(request),mimetype="text/html")     
        
    pull_user_unpost_trades.short_description = "下载待发货订单".decode('utf8')
    
    #更新用户线上商品入库
    def pull_user_items(self,request,queryset):
        
        from shopback.items.tasks import updateUserItemSkuFenxiaoProductTask
        
        pull_users = []
        for user in queryset:
            pull_dict = {'uid':user.visitor_id,'nick':user.nick}
            try:
                #下载更新用户商品分销商品
                updateUserItemSkuFenxiaoProductTask.delay(user.visitor_id)
            except Exception,exc:
                pull_dict['success']=False
                pull_dict['errmsg']=exc.message or '%s'%exc
                
            else:
                pull_dict['success']=True
            pull_users.append(pull_dict)
        
        return render_to_response('users/pull_online_items.html',{'users':pull_users},
                                  context_instance=RequestContext(request),mimetype="text/html")

    pull_user_items.short_description = "下载线上商品".decode('utf8')
    
    
    #商品上下架
    def autolist_user_items(self,request,queryset):
        
        if queryset.count() != 1:
            return 
        
        user = queryset[0]
       
        return HttpResponseRedirect(reverse('pull_from_taobao')+'?user_id='+str(user.user.id))

    autolist_user_items.short_description = "商品自动上架".decode('utf8')
    
    #线上库存覆盖系统库存
    def sync_online_prodnum_to_offline(self,request,queryset):
        
        if queryset.count() != 1:
            ret_params = {'success':False,'errmsg':'请选择一个主店'}
        user = queryset[0]
        
        try:
            from shopback.items.tasks import updateUserProductSkuTask
            
            updateUserProductSkuTask(user.visitor_id,force_update_num=True)
        except Exception,exc :
            ret_params = {'success':False,'errmsg':exc.message}
        else:
            ret_params = {'success':True}
        return render_to_response('users/sync_online_prodnum_template.html',ret_params,
                                  context_instance=RequestContext(request),mimetype="text/html")     
        
    sync_online_prodnum_to_offline.short_description = "线上库存覆盖系统库存".decode('utf8')
    
    #异步下载近三个月订单
    def async_pull_lastest_trades(self,request,queryset):
        
        from shopapp.asynctask.tasks import AsyncOrderTask
        
        pull_users = []
        for user in queryset:
            pull_dict = {'uid':user.visitor_id,'nick':user.nick}
            try:
                end_dt   = datetime.datetime.now()-datetime.timedelta(1,0,0)
                for i in range(3):
                    s_dt = end_dt - datetime.timedelta((i+1)*30,0,0)
                    e_dt = end_dt - datetime.timedelta(i*30,0,0)
                    #异步批量更新订单
                    AsyncOrderTask.delay(s_dt,e_dt,user.visitor_id)
            except Exception,exc:
                pull_dict['success']=False
                pull_dict['errmsg']=exc.message or '%s'%exc
            else:
                pull_dict['success']=True
            pull_users.append(pull_dict)
        
        return render_to_response('users/async_lastest_trades.html',{'users':pull_users},
                                  context_instance=RequestContext(request),mimetype="text/html")

    async_pull_lastest_trades.short_description = "异步下载近三个月订单".decode('utf8')
       
    actions = ['pull_user_unpost_trades','autolist_user_items','pull_user_items',
               'sync_online_prodnum_to_offline','async_pull_lastest_trades']

admin.site.register(User, UserAdmin)


class CustomerAdmin(admin.ModelAdmin):
    
    list_display = ('id','nick','sex','name','city','state','district','phone','mobile',
                    'last_buy_time','buy_times','avg_payment','is_valid')
    list_display_links = ('id', 'nick')

    ordering = ['-last_buy_time']

    list_filter = ('is_valid',)
    search_fields = ['nick','name']
    
admin.site.register(Customer, CustomerAdmin)
    
    