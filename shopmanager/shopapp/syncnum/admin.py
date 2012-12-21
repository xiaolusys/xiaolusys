#-*- coding:utf8 -*-
import datetime
from django.contrib import admin
from shopback.users.models import User
from shopapp.syncnum.models import ItemNumTaskLog



class ItemNumTaskLogAdmin(admin.ModelAdmin):
    list_display = ('id','user_id','outer_id', 'sku_outer_id', 'num', 'start_at', 'end_at')
    list_display_links = ('outer_id', 'sku_outer_id')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'end_at'

    list_filter = ('user_id',)
    search_fields = ['id','outer_id','sku_outer_id']

    actions = ['cancleExecute']

    def cancleExecute(self, request, queryset):
        queryset.update(status='delete')

    cancleExecute.short_description = "Cancle Task!"
    
    #线上库存同步
    def sync_online_stock(self,request,queryset):
        
        from shopapp.syncnum.tasks import updateUserItemNumTask
        users  = User.objects.all()
        
        dt = datetime.datetime.now()
        pull_users = []
        for user in users:
            pull_dict = {'uid':user.visitor_id,'nick':user.nick}
            try:
                #下载更新用户商品分销商品
                updateUserItemNumTask(user.visitor_id,dt)
            except Exception,exc:
                pull_dict['success']=False
                pull_dict['errmsg']=exc.message or '%s'%exc
                
            else:
                pull_dict['success']=True
            pull_users.append(pull_dict)
       
        return render_to_response('syncnum/sync_taobao_stock.html',{'users':pull_users},
                                  context_instance=RequestContext(request),mimetype="text/html")
    
    sync_online_stock.short_description = "线上库存同步".decode('utf8')
    
    actions = ['sync_online_stock',]


admin.site.register(ItemNumTaskLog, ItemNumTaskLogAdmin)

