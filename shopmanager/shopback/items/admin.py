#-*- coding:utf8 -*-
import json
import datetime,time
import cStringIO as StringIO
from django.contrib import admin
from django.http import HttpResponse,HttpResponseRedirect
from django.db import models
from django.db import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.forms import TextInput, Textarea
from django.contrib.auth.models import Group

from shopback.items.models import (Item,Product,
                                   ProductSku,
                                   ProductLocation,
                                   ItemNumTaskLog,
                                   SkuProperty,
                                   ProductDaySale,
                                   ProductScanStorage)
from shopback.trades.models import MergeTrade,MergeOrder
from shopback.users.models import User
from shopback.categorys.models import ProductCategory
from shopback.purchases import getProductWaitReceiveNum
from shopback import paramconfig as pcfg
from shopback.base import log_action, ADDITION, CHANGE
from shopback.items import permissions as perms
from shopback.items.forms import ProductModelForm
from shopback.base.options import DateFieldListFilter
from shopback.items.filters import ChargerFilter,DateScheduleFilter
from common.utils import gen_cvs_tuple,CSVUnicodeWriter
from flashsale.pay.models import Productdetail
import logging 

logger =  logging.getLogger('django.request')

class ProductSkuInline(admin.TabularInline):
    
    model = ProductSku
    fields = ('outer_id','properties_name','properties_alias','quantity','warn_num','remain_num','wait_post_num','reduce_num','cost'
              ,'std_sale_price','agent_price','sync_stock','is_assign','is_split','is_match','post_check','barcode','status','buyer_prompt')
    
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'10'})},
        models.FloatField: {'widget': TextInput(attrs={'size':'8'})},
        models.TextField: {'widget': Textarea(attrs={'rows':2, 'cols':20})},
    }
    
    def get_readonly_fields(self, request, obj=None):
        if not perms.has_change_product_skunum_permission(request.user):
            return self.readonly_fields + ('quantity','warn_num','wait_post_num','is_split')
        return self.readonly_fields
    
class ProductdetailInline(admin.TabularInline):
    
    model = Productdetail
    fields = ('head_img',
              ('ct_img1','ct_img2'),
              ('ct_img3','ct_img4'))
    
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'50'})},
    }
    


class ItemAdmin(admin.ModelAdmin):
    list_display = ('num_iid','user','outer_id','type','category','title','price','has_showcase','sync_stock',
                    'with_hold_quantity','delivery_time','list_time','last_num_updated','approve_status','status')
    list_display_links = ('num_iid', 'title')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'last_num_updated'
    #ordering = ['created_at']

    list_filter = ('user','has_showcase','sync_stock','approve_status','category')
    search_fields = ['num_iid', 'outer_id', 'title']


admin.site.register(Item, ItemAdmin)


class ProductAdmin(admin.ModelAdmin):
    
    category_list = []
    storage_chargers = []
    
    form = ProductModelForm
    list_per_page = 25
    list_display = ('id','outer_id','pic_link','collect_num','category_select',
                    'warn_num','remain_num','wait_post_num','cost' ,'std_sale_price','agent_price'
                   ,'sync_stock','is_match','is_split','sale_time','sale_charger','charger_select','district_link','status')
    list_display_links = ('id',)
    #list_editable = ('name',)
    
    date_hierarchy = 'sale_time'
    #ordering = ['created_at']
    
    def pic_link(self, obj):
        abs_pic_url = obj.pic_path or '%s%s'%(settings.MEDIA_URL,settings.NO_PIC_PATH)
        return (u'<a href="/items/product/%d/" target="_blank"><img src="%s" width="100px" '
                +' height="80px" title="%s"/></a><p><span>%s</span></p>')%(obj.id,abs_pic_url,obj.name,obj.name or u'--')
    
    pic_link.allow_tags = True
    pic_link.short_description = "商品图片"
    
    def district_link(self, obj):
        return u'<a href="/items/product/district/%d/" target="_blank" style="display: block;">查看 &gt;&gt;</a>' \
            %(obj.id, )
    district_link.allow_tags = True
    district_link.short_description = u"货位" 
    
    def wait_receive_num(self, obj):
        wrNum = getProductWaitReceiveNum(obj.id)
        if not wrNum:
            return '0'
        return u'<div style="color:blue;background-color:red;">%d</div>'%wrNum
    
    wait_receive_num.allow_tags = True
    wait_receive_num.short_description = u"在途数" 
    
        
    def category_select(self, obj):

        categorys = self.category_list

        cat_list = ["<select class='category_select' pid='%s'>"%obj.id]
        cat_list.append("<option value=''>-------------------</option>")
        for cat in categorys:

            if obj.category and obj.category == cat:
                cat_list.append("<option value='%s' selected>%s</option>"%(cat.cid,cat))
                continue

            cat_list.append("<option value='%s'>%s</option>"%(cat.cid,cat))
        cat_list.append("</select>")

        return "".join(cat_list)

    category_select.allow_tags = True
    category_select.short_description = u"所属类目"
    
    
    def charger_select(self, obj):

        categorys = self.storage_chargers

        if len(categorys) > 0:
            cat_list = ["<select class='charger_select' cid='%s'>"%obj.id]
            cat_list.append("<option value=''>---------------</option>")
            for cat in categorys:
    
                if obj and obj.storage_charger == cat.username:
                    cat_list.append("<option value='%s' selected>%s</option>"%(cat.id,cat.username))
                    continue
    
                cat_list.append("<option value='%s'>%s</option>"%(cat.id,cat.username))
            
            cat_list.append("</select>")
            
            return "".join(cat_list)
        else:
            return obj.storage_charger and '[%s]'%[obj.storage_charger] or '[-]'
        
        
    charger_select.allow_tags = True
    charger_select.short_description = u"所属仓管员"
    
    inlines = [ProductdetailInline,ProductSkuInline]
    
    list_filter = (ChargerFilter,'status',('sale_time',DateScheduleFilter)
                   ,'sync_stock','is_split','is_match','is_assign'
                   ,'post_check',('created',DateFieldListFilter),'category')

    search_fields = ['id','outer_id', 'name' , 'barcode','sale_charger','storage_charger']
    
    #--------设置页面布局----------------
    fieldsets =(('商品基本信息:', {
                    'classes': ('expand',),
                    'fields': (('outer_id','category','status')
                               ,('name','pic_path')
                               ,('collect_num','warn_num','remain_num','wait_post_num','reduce_num')
                               ,('std_purchase_price','staff_price','sale_time')
                               ,('cost','std_sale_price','agent_price'))
                }),
                ('商品系统设置:', {
                    'classes': ('collapse',),
                    'fields': (('weight','sync_stock','is_assign','is_split','is_match','post_check')
                               ,('barcode','match_reason')
                               ,('sale_charger','storage_charger')
                               ,('buyer_prompt','memo')
                               )
                }),)
    
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':64, 'maxlength': '256',})},
        models.FloatField: {'widget': TextInput(attrs={'size':24})},
        models.TextField: {'widget': Textarea(attrs={'rows':4, 'cols':40})},
    }
    
    class Media:
        css = {"all": ("admin/css/forms.css","css/admin/dialog.css","css/admin/common.css", "jquery/jquery-ui-1.10.1.css")}
        js = ("js/admin/adminpopup.js","js/item_change_list.js")
    
    def get_readonly_fields(self, request, obj=None):
        
        if not perms.has_change_product_skunum_permission(request.user):
            return self.readonly_fields + ('collect_num','warn_num','wait_post_num','sale_charger','storage_charger')
        return self.readonly_fields
    
    def response_add(self, request, obj, post_url_continue='../%s/'):
        
        if not obj.sale_charger:
            obj.sale_charger = request.user.username
            obj.save()

        return super(ProductAdmin,self).response_add(request, obj, post_url_continue=post_url_continue)
    
    def get_changelist(self, request, **kwargs):
        """
        Returns the ChangeList class for use on the changelist page.
        """
        if perms.has_change_product_skunum_permission(request.user):
            groups = Group.objects.filter(name=u'仓管员')
            if groups.count() > 0:
                self.storage_chargers = groups[0].user_set.filter(is_staff=True)
        self.category_list = ProductCategory.objects.filter(is_parent=False)
   
        return super(ProductAdmin,self).get_changelist(request, **kwargs)
    
    def queryset(self, request):
        """
        Returns a QuerySet of all model instances that can be edited by the
        admin site. This is used by changelist_view.
        """
        qs = self.model._default_manager.get_query_set()
        # TODO: this should be handled by some parameter to the ChangeList.
        if not request.user.is_superuser:
            qs = qs.exclude(status=pcfg.DELETE)
        
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs
    
    #更新用户线上商品入库
    def sync_items_stock(self,request,queryset):
        
        from shopback.items.tasks import updateUserProductSkuTask,updateItemNum
        users = User.objects.filter(status=pcfg.NORMAL)
        dt   =   datetime.datetime.now()
        sync_items = []
        for prod in queryset:
            pull_dict = {'outer_id':prod.outer_id,'name':prod.name}
            try:
                items = Item.objects.filter(outer_id=prod.outer_id)
                #更新商品信息
                for item in items:
                    Item.get_or_create(item.user.visitor_id,item.num_iid,force_update=True)
                    
                items = items.filter(approve_status=pcfg.ONSALE_STATUS)
                if items.count() < 1:
                    raise Exception(u'请确保商品在售')
                
                for u in users:
                    #更新商品线上SKU状态
                    updateUserProductSkuTask(user_id=u.visitor_id,outer_ids=[i.outer_id for i in items if i.outer_id ])
                #更新商品及SKU库存
                for item in items:
                    updateItemNum(item.user.visitor_id,item.num_iid)
            except Exception,exc:
                logger.error(exc.message,exc_info=True)
                pull_dict['success']=False
                pull_dict['errmsg']=exc.message or '%s'%exc  
            else:
                pull_dict['success']=True
            sync_items.append(pull_dict)
       
        return render_to_response('items/product_action.html',{'prods':sync_items,'action_name':u'更新线上库存'},
                                  context_instance=RequestContext(request),mimetype="text/html")
    
    sync_items_stock.short_description = u"同步淘宝线上库存"
    
    
    #作废商品
    def invalid_product_action(self,request,queryset):
         
        for p in queryset:
            cnt = 0
            success = False
            invalid_outerid = p.outer_id 
            while cnt < 10:
                invalid_outerid += '_del'
                products = Product.objects.filter(outer_id=invalid_outerid)
                if products.count() == 0:
                    success = True
                    break
                cnt += 1
                
            if not success:
                continue
            
            p.outer_id = invalid_outerid
            p.status = pcfg.DELETE
            p.save()
            
            log_action(request.user.id,p,CHANGE,u'商品作废')
        
        self.message_user(request,u"已成功作废%s个商品!"%queryset.filter(status=pcfg.DELETE).count())
        
        return HttpResponseRedirect(request.get_full_path())
        
    invalid_product_action.short_description = u"作废库存商品（批量 ）"
    
    #更新用户线上商品入库
    def sync_purchase_items_stock(self,request,queryset):
        
        from shopback.items.tasks import updatePurchaseItemNum
        from shopback.fenxiao.models import FenxiaoProduct
        
        sync_items = []
        for prod in queryset:
            pull_dict = {'outer_id':prod.outer_id,'name':prod.name}
            try:
                items = FenxiaoProduct.objects.filter(outer_id=prod.outer_id,
                                                         status=pcfg.UP_STATUS)
                
                if items.count() < 1:
                    raise Exception(u'请确保商品在售')
                
                #更新商品及SKU库存
                for item in items:
                    FenxiaoProduct.get_or_create(item.user.visitor_id,item.pid,force_update=True)
                    
                    updatePurchaseItemNum(item.user.visitor_id,item.pid)
            except Exception,exc:
                logger.error(exc.message,exc_info=True)
                pull_dict['success']=False
                pull_dict['errmsg']=exc.message or '%s'%exc  
            else:
                pull_dict['success']=True
            sync_items.append(pull_dict)
       
        return render_to_response('items/product_action.html',{'prods':sync_items,'action_name':u'更新分销线上库存'},
                                  context_instance=RequestContext(request),mimetype="text/html")
    
    sync_purchase_items_stock.short_description = u"同步分销商品库存"
    
#     #根据线上商品SKU 更新系统商品SKU
#     def update_items_sku(self,request,queryset):
#         
#         from shopback.items.tasks import updateUserProductSkuTask
#         users = User.objects.filter(status=pcfg.NORMAL,is_primary=True)
#         sync_items = []
#         for prod in queryset:
#             pull_dict = {'outer_id':prod.outer_id,'name':prod.name}
#             try:
#                 items = Item.objects.filter(outer_id=prod.outer_id)
#                 for item in items:
#                     Item.get_or_create(item.user.visitor_id,item.num_iid,force_update=True)    
#                 
#                 for u in users:
#                     updateUserProductSkuTask(user_id=u.visitor_id,outer_ids=[prod.outer_id])
#                     
#                 item_sku_outer_ids = set()
#                 items = Item.objects.filter(outer_id=prod.outer_id)
#                 for item in items:
#                     sku_dict = json.loads(item.skus or '{}')
#                     if sku_dict:
#                         sku_list = sku_dict.get('sku')
#                         item_sku_outer_ids.update([ sku.get('outer_id','') for sku in sku_list])
#                 prod.prod_skus.exclude(outer_id__in=item_sku_outer_ids).update(status=pcfg.REMAIN)
#             except Exception,exc:
#                 pull_dict['success']=False
#                 pull_dict['errmsg']=exc.message or '%s'%exc  
#             else:
#                 pull_dict['success']=True
#             sync_items.append(pull_dict)
#        
#         return render_to_response('items/product_action.html',{'prods':sync_items,'action_name':u'更新商品SKU'},
#                                   context_instance=RequestContext(request),mimetype="text/html")
#     
#     update_items_sku.short_description = u"更新系统商品SKU"    
    
    #取消该商品缺货订单
    def cancle_orders_out_stock(self,request,queryset):
        
        sync_items = []
        for prod in queryset:
            pull_dict = {'outer_id':prod.outer_id,'name':prod.name}
            try:
                orders = MergeOrder.objects.filter(outer_id=prod.outer_id,out_stock=True)
                for order in orders:
                    order.out_stock = False
                    order.save()
                    log_action(request.user.id,order.merge_trade,CHANGE,u'取消子订单（%d）缺货'%order.id)
            except Exception,exc:
                pull_dict['success']=False
                pull_dict['errmsg']=exc.message or '%s'%exc  
            else:
                pull_dict['success']=True
            sync_items.append(pull_dict)
       
        return render_to_response('items/product_action.html',
                                  {'prods':sync_items,'action_name':u'取消商品对应订单缺货状态'},
                                  context_instance=RequestContext(request),mimetype="text/html")
        
    cancle_orders_out_stock.short_description = u"取消订单商品缺货"
    
    #取消商品库存同步（批量）
    def active_syncstock_action(self,request,queryset):
         
        for p in queryset:
            p.sync_stock = True
            p.save()
        
        self.message_user(request,u"已成功设置%s个商品库存同步!"%queryset.count())
        
        return HttpResponseRedirect(request.get_full_path())
        
    active_syncstock_action.short_description = u"设置商品库存同步"
    
    #取消商品库存同步（批量）
    def cancel_syncstock_action(self,request,queryset):
         
        count = queryset.count
        for p in queryset:
            p.sync_stock = False
            p.save()
        
        self.message_user(request,u"已成功取消%s个商品库存同步!"%(count - queryset.count()))
        
        return HttpResponseRedirect(request.get_full_path())
        
    cancel_syncstock_action.short_description = u"取消商品库存同步"
    
    #取消订单匹配标记状态（批量）
    def regular_saleorder_action(self,request,queryset):
         
        remind_time = datetime.datetime.now() + datetime.timedelta(days=7)
        outer_ids = [p.outer_id for p in queryset]
        mos = MergeOrder.objects.filter(outer_id__in=outer_ids,
                                    merge_trade__sys_status__in=("WAIT_PREPARE_SEND","WAIT_AUDIT"))
        
        merge_trades = set([o.merge_trade for o in mos])
        effect_num = 0
        for t in merge_trades:
            if (t.status == pcfg.WAIT_SELLER_SEND_GOODS
                and not t.out_sid):
                t.sys_status="REGULAR_REMAIN"
                t.remind_time=remind_time
                t.save()
                effect_num += 1
                log_action(request.user.id,t,CHANGE,u'定时(%s)提醒'%remind_time)
            
        self.message_user(request,u"已成功设置%s个订单定时提醒!"%effect_num)
        
        return HttpResponseRedirect(request.get_full_path())
        
    regular_saleorder_action.short_description = u"定时商品订单七日"
    
    #取消订单匹配标记状态（批量）
    def deliver_saleorder_action(self,request,queryset):
         
        outer_ids = [p.outer_id for p in queryset]
        mos = MergeOrder.objects.filter(outer_id__in=outer_ids,
                                    merge_trade__sys_status="REGULAR_REMAIN")
    
        merge_trades = set([o.merge_trade for o in mos])
    
        for t in merge_trades:

            if (t.inuse_orders.count() > 1 or 
                not t.logistics_company or 
                t.reason_code ):
                t.sys_status="WAIT_AUDIT"
            else:
                t.sys_status="WAIT_PREPARE_SEND"
            t.save()
        
        self.message_user(request,u"已成功取消%s个订单定时提醒!"%len(merge_trades))
        
        return HttpResponseRedirect(request.get_full_path())
        
    deliver_saleorder_action.short_description = u"释放商品定时订单"
    
    #商品库存
    def weixin_product_action(self,request,queryset):
        
        if queryset.count() > 10:
            self.message_user(request,u"*********选择更新的商品数不能超过10个************")
            return HttpResponseRedirect(request.get_full_path())
         
        product_ids = ','.join([str(p.id) for p in queryset])
        
        return HttpResponseRedirect(reverse('weixin_product_modify')
                                    +'?format=html&product_ids=%s'%product_ids)
        
    weixin_product_action.short_description = u"更新微信商品库存信息"
    
    #导出商品规格信息
    def export_prodsku_info_action(self,request,queryset):
        """ 导出商品及规格信息 """

        is_windows = request.META['HTTP_USER_AGENT'].lower().find('windows') >-1 
        pcsv =[]
        pcsv.append((u'商品编码',u'商品名',u'规格编码',u'规格名',u'库存数',u'昨日销量',u'预留库位'
                     ,u'待发数',u'日出库',u'成本',u'吊牌价',u'库位',u'条码'))
        for prod in queryset:
            skus = prod.pskus.exclude(is_split=True)
            if skus.count() > 0:
                for sku in skus:
                    pcsv.append((prod.outer_id,prod.name,sku.outer_id,sku.name,str(sku.quantity),str(sku.warn_num),\
                                 str(sku.remain_num),str(sku.wait_post_num),str(sku.sale_num),str(sku.cost),\
                                 str(sku.std_sale_price),sku.get_districts_code(),sku.barcode))
            else:
                pcsv.append((prod.outer_id,prod.name,'','',str(prod.collect_num),str(prod.warn_num),\
                                 str(prod.remain_num),str(prod.wait_post_num),str(sku.sale_num),str(prod.cost),\
                                 str(prod.std_sale_price),prod.get_districts_code(),prod.barcode))
            pcsv.append(['','','','','','','','','','','',''])
        
        tmpfile = StringIO.StringIO()
        writer  = CSVUnicodeWriter(tmpfile,encoding= is_windows and "gbk" or 'utf8')
        writer.writerows(pcsv)
            
        response = HttpResponse(tmpfile.getvalue(), mimetype='application/octet-stream')
        tmpfile.close()
        response['Content-Disposition'] = 'attachment; filename=product-sku-info-%s.csv'%str(int(time.time()))
        
        return response
        
    export_prodsku_info_action.short_description = u"导出商品及规格信息"
    
    actions = ['sync_items_stock',
               'invalid_product_action',
               'sync_purchase_items_stock',
               'weixin_product_action',
               'cancle_orders_out_stock',
               'active_syncstock_action',
               'cancel_syncstock_action',
               'regular_saleorder_action',
               'deliver_saleorder_action',
               'export_prodsku_info_action']

admin.site.register(Product, ProductAdmin)


class ProductSkuAdmin(admin.ModelAdmin):
    list_display = ('id','outer_id','product','properties_name','properties_alias','quantity','warn_num',
                    'remain_num','wait_post_num','cost','std_sale_price','sync_stock','is_assign',
                    'is_split','is_match','post_check','district_link','status')
    list_display_links = ('outer_id',)
    list_editable = ('quantity',)

    date_hierarchy = 'modified'
    #ordering = ['created_at']

    list_filter = ('status','sync_stock','is_split','is_match','is_assign','post_check')
    search_fields = ['outer_id','product__outer_id','properties_name','properties_alias']
    
    def district_link(self, obj):
        return u'<a href="%d/" onclick="return showTradePopup(this);">%s</a>' %(obj.id,obj.districts or u'--' )
    district_link.allow_tags = True
    district_link.short_description = "库位"
    
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'16'})},
        models.FloatField: {'widget': TextInput(attrs={'size':'16'})},
        models.TextField: {'widget': Textarea(attrs={'rows':2, 'cols':25})},
    }
    
        #--------设置页面布局----------------
    fieldsets =(('商品基本信息:', {
                    'classes': ('expand',),
                    'fields': (('outer_id','properties_name','properties_alias','status')
                               ,('quantity','warn_num','remain_num','wait_post_num','weight')
                               ,('cost','std_purchase_price','std_sale_price','agent_price','staff_price')
                               ,('sync_stock','is_assign','is_split','is_match','memo','buyer_prompt'))
                }),)
    
    #取消该商品缺货订单
    def cancle_items_out_stock(self,request,queryset):
        
        sync_items = []
        for prod in queryset:
            pull_dict = {'outer_id':prod.outer_id,'name':prod.properties_name}
            try:
                orders = MergeOrder.objects.filter(outer_id=prod.product.outer_id,outer_sku_id=prod.outer_id,out_stock=True)
                for order in orders:
                    order.out_stock = False
                    order.save()
                    log_action(request.user.id,order.merge_trade,CHANGE,u'取消子订单（%d）缺货'%order.id)
            except Exception,exc:
                pull_dict['success']=False
                pull_dict['errmsg']=exc.message or '%s'%exc  
            else:
                pull_dict['success']=True
            sync_items.append(pull_dict)
       
        return render_to_response('items/product_action.html',{'prods':sync_items,
                                                               'action_name':u'取消规格对应订单缺货状态'},
                                  context_instance=RequestContext(request),mimetype="text/html")
        
    cancle_items_out_stock.short_description = u"取消规格订单缺货"
    
    actions = ['cancle_items_out_stock']


admin.site.register(ProductSku, ProductSkuAdmin)
  
  
class SkuPropertyAdmin(admin.ModelAdmin):
    list_display = ('num_iid','sku_id','outer_id','properties_name','price','quantity',
                    'with_hold_quantity','sku_delivery_time','created','modified','status')
    list_display_links = ('sku_id', 'outer_id')
    #list_editable = ('update_time','task_type' ,'is_success','status')
    
    list_filter = ('status',)
    search_fields = ['outer_id','sku_id','num_iid','properties_name']


admin.site.register(SkuProperty, SkuPropertyAdmin)


class ProductLocationAdmin(admin.ModelAdmin):
    list_display = ('product_id','sku_id','outer_id','name','outer_sku_id','properties_name','district')
    list_display_links = ('outer_id', 'outer_sku_id')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    search_fields = ['product_id','sku_id','outer_id','outer_sku_id','district__parent_no']


admin.site.register(ProductLocation, ProductLocationAdmin)


class ItemNumTaskLogAdmin(admin.ModelAdmin):
    list_display = ('id','user_id','outer_id', 'sku_outer_id', 'num', 'start_at', 'end_at')
    list_display_links = ('outer_id', 'sku_outer_id')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'end_at'

    list_filter = ('user_id',('end_at',DateFieldListFilter))
    search_fields = ['id','outer_id','sku_outer_id']
    

admin.site.register(ItemNumTaskLog, ItemNumTaskLogAdmin)


class ProductDaySaleAdmin(admin.ModelAdmin):
    list_display = ('day_date','user_id','product_id', 'sku_id', 'sale_num',
                     'sale_payment','confirm_num','confirm_payment', 'sale_refund')
    list_display_links = ('day_date', 'user_id','product_id')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    #date_hierarchy = 'day_date'

    list_filter = ('user_id',('day_date',DateFieldListFilter))
    search_fields = ['id','user_id','product_id','sku_id']
    

admin.site.register(ProductDaySale, ProductDaySaleAdmin)

class ProductScanStorageAdmin(admin.ModelAdmin):
    list_display = ('wave_no','product_id','qc_code','sku_code',
                    'product_name','barcode', 'scan_num','created', 'status')
    list_display_links = ('product_id', 'barcode')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    #date_hierarchy = 'day_date'

    list_filter = ('status',('created',DateFieldListFilter))
    search_fields = ['product_id','qc_code','barcode','wave_no']
    
    def get_actions(self, request):
        
        user = request.user
        actions = super(ProductScanStorageAdmin, self).get_actions(request)

        if not user.has_perm('items.has_delete_permission') and 'delete_selected' in actions:
            del actions['delete_selected']

        return actions
    
    def queryset(self, request):
        """
        Returns a QuerySet of all model instances that can be edited by the
        admin site. This is used by changelist_view.
        """
        qs = self.model._default_manager.get_query_set()
        # TODO: this should be handled by some parameter to the ChangeList.
        if not request.user.is_superuser:
            qs = qs.exclude(status=ProductScanStorage.DELETE)
        
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs
    
    #取消该商品缺货订单
    def confirm_scan_action(self,request,queryset):
        
        queryset = queryset.filter(status=ProductScanStorage.WAIT)
        try:
            for prod in queryset:
                
                if prod.sku_id:
                    product_sku = ProductSku.objects.get(id=prod.sku_id,product=prod.product_id)
                    
                    product_sku.update_quantity(prod.scan_num)
                    
                    product = product_sku.product
                else:
                    product = Product.objects.get(id=prod.product_id)
                    
                    product.update_collect_num(prod.scan_num)
                    
                prod.status = ProductScanStorage.PASS
                
                prod.save()
                
                log_action(request.user.id,prod,CHANGE,
                          u'确认入库：%s'%prod.scan_num)
                
                log_action(request.user.id,product,CHANGE,
                          u'扫描确认入库数：%s'%prod.scan_num)
                    
        except Exception,exc:
            messages.add_message(request,messages.ERROR,u'XXXXXXXXXXXXXXXXX确认入库异常:%sXXXXXXXXXXXX'%exc)
        else:
            messages.add_message(request,messages.INFO,u'==================操作成功==================')
            
        return HttpResponseRedirect('./')
        
    confirm_scan_action.short_description = u"确认入库"
    
    #取消该商品缺货订单
    def delete_scan_action(self,request,queryset):
        
        queryset = queryset.filter(status=ProductScanStorage.WAIT)
        try:
            for prod in queryset:
                
                prod.scan_num = 0
                prod.status = ProductScanStorage.DELETE
                
                prod.save()
                
                log_action(request.user.id,prod,CHANGE, u'作废')
                
        except Exception,exc:
            messages.add_message(request,messages.ERROR,
                                 u'XXXXXXXXXXXXXXXXX作废失败:%sXXXXXXXXXXXX'%exc)
        else:
            messages.add_message(request,messages.INFO,
                                 u'==================已作废==================')
            
        return HttpResponseRedirect('./')
        
    delete_scan_action.short_description = u"作废扫描记录"
    
    #取消该商品缺货订单
    def export_scan_action(self,request,queryset):
        
        """ 导出商品及规格信息 """

        is_windows = request.META['HTTP_USER_AGENT'].lower().find('windows') >-1 
        
        pcsv = gen_cvs_tuple(queryset,
                             fields=['barcode','product_id','sku_id'
                                     ,'product_name','sku_name','scan_num','created','wave_no'],
                             title=[u'商品条码',u'商品ID',u'规格ID'
                                    ,u'商品名称',u'规格名',u'扫描数量',u'扫描时间',u'批次号'])
        
        pcsv[0].insert(1,u'库位')
        pcsv[0].insert(2,u'商品编码')
        pcsv[0].insert(3,u'规格编码')

        for i in range(1,len(pcsv)):
            item = pcsv[i]
            product_id,sku_id = item[1].strip(),item[2].strip()
            
            product_loc = ''
            try:
                product = Product.objects.get(id=product_id)
            except:
                product = None
            product_sku = None
            if sku_id and sku_id != 'None' and sku_id != '-':
                product_sku = ProductSku.objects.get(id=sku_id)
            
            item.insert(1,product_sku and product_sku.get_districts_code() or (product and product.get_districts_code() or ''))
            item.insert(2,product and product.outer_id or u'商品未找到!!!')
            item.insert(3,product_sku and product_sku.outer_id or '')
        
        tmpfile = StringIO.StringIO()
        writer  = CSVUnicodeWriter(tmpfile,encoding= is_windows and "gbk" or 'utf8')
        writer.writerows(pcsv)
            
        response = HttpResponse(tmpfile.getvalue(), mimetype='application/octet-stream')
        tmpfile.close()
        response['Content-Disposition'] = 'attachment; filename=product-scan-%s.csv'%str(int(time.time()))
        
        return response
        
        
    export_scan_action.short_description = u"导出扫描商品数"
    
    actions = ['confirm_scan_action','delete_scan_action','export_scan_action']
    
    

admin.site.register(ProductScanStorage, ProductScanStorageAdmin)
