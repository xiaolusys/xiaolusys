#-*- coding:utf8 -*-
from django.contrib import admin
from django.db import models
from django.forms import TextInput, Textarea
from django.http import HttpResponseRedirect
from .models import SaleProduct,SaleSupplier,SaleCategory

class SaleSupplierAdmin(admin.ModelAdmin):
    list_display = ('id','supplier_code','supplier_name','main_page','created','modified')
    list_display_links = ('id','supplier_name')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    #list_filter   = ('can_reuse','is_finish')
    search_fields = ['supplier_name','supplier_code']
    
admin.site.register(SaleSupplier,SaleSupplierAdmin)


class SaleCategoryAdmin(admin.ModelAdmin):
    
    list_display = ('id','name','created','modified')
    
    list_display_links = ('id','name')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    #list_filter   = ('can_reuse','is_finish')
    search_fields = ['name',]
    
admin.site.register(SaleCategory,SaleCategoryAdmin)


class SaleProductAdmin(admin.ModelAdmin):
    
    list_display = ('outer_id','pic_link','title_link','price','supplier_link','platform','hot_value','sale_price','status','modified')
    list_display_links = ('outer_id',)
    #list_editable = ('update_time','task_type' ,'is_success','status')
    
    ordering   = ('-hot_value',)
    list_filter   = ('sale_category','platform','status',)
    search_fields = ['id','title','outer_id','sale_supplier__supplier_name']
    
    def pic_link(self, obj):
#         abs_pic_url = '%s%s'%(settings.MEDIA_URL,obj.pic_url)
        return (u'<a href="%s" target="_blank"><img src="%s" width="120px" height="100px"/></a>'%(obj.product_link,obj.pic_url))
    
    pic_link.allow_tags = True
    pic_link.short_description = u"商品图片"
    
    def title_link(self, obj):
#         abs_pic_url = '%s%s'%(settings.MEDIA_URL,obj.pic_url)
        ignore_style = ''
        ignore_val     = ''
        if obj.status  == SaleProduct.WAIT:
            ignore_style = 'btn-info btn-ignore'
            ignore_val     = u'忽略'
        elif obj.status  == SaleProduct.IGNORED :
            ignore_val     = u'已忽略'
        else:
            ignore_val     = u'处理中'
             
        select_style = ''
        select_val     = ''
        if obj.status  == SaleProduct.WAIT:
            select_style = 'btn-success btn-selecte'
            select_val    = u'入围'
        elif obj.status  in (SaleProduct.SELECTED,SaleProduct.PURCHASE) :
            select_val     = u'已入围'
        else:
            select_val     = u'已淘汰'
        
        return (u'<div style="width:400px;">'
                        +u'<a href="javascript:void(0);" class="btn {0}" pid="{1}" >{2}</a>'
                        +u'<div  class="well well-content">{3}</div>'
                        +u' <a href="javascript:void(0);" class="btn {4}" pid="{5}" >{6}</a></div>')\
                        .format(ignore_style,
                                        obj.id,
                                        ignore_val,
                                        obj.title,
                                        select_style,
                                        obj.id,
                                        select_val)
    
    title_link.allow_tags = True
    title_link.short_description = u"标题"
    
    def supplier_link(self, obj):
#         abs_pic_url = '%s%s'%(settings.MEDIA_URL,obj.pic_url)
        base_link = u'<div  style="width:150px;font-size:20px;"><label>{0}</lable>'.format(obj.sale_supplier.supplier_name)
        if obj.status in (SaleProduct.SELECTED,SaleProduct.PURCHASE):
            base_link += u'<br><br><a href="/flashsale/supplier/product/?status={0}&sale_supplier={1}"  target="_blank" >{2}</a></div>'
            base_link = base_link.format(obj.status ,
                                                                    obj.sale_supplier.id,
                                                                    obj.status==SaleProduct.SELECTED and u'洽谈'  or u'终审' )
 
        return base_link
    
    supplier_link.allow_tags = True
    supplier_link.short_description = u"供应商"
    
    class Media:
        css = {"all": ("admin/css/forms.css","css/admin/dialog.css","css/admin/common.css", "jquery/jquery-ui-1.10.1.css")}
        js = ("script/admin/adminpopup.js","js/supplier_change_list.js")
    
    
admin.site.register(SaleProduct,SaleProductAdmin)


