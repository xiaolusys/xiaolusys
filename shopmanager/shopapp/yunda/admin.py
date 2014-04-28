#-*- coding:utf8 -*-
from django.contrib import admin
from shopapp.yunda.models import ClassifyZone,BranchZone,LogisticOrder,YundaCustomer,\
    ParentPackageWeight,TodaySmallPackageWeight,TodayParentPackageWeight
from shopback.base.options import DateFieldListFilter
from django.contrib import messages
from common.utils import group_list
from .service import YundaService,WEIGHT_UPLOAD_LIMIT

class ClassifyZoneInline(admin.TabularInline):
    
    model = ClassifyZone
    fields = ('state','city','district')
    


class ClassifyZoneAdmin(admin.ModelAdmin):
    
    list_display = ('state','city','district','branch')
    list_display_links = ('state','city',)

    #date_hierarchy = 'created'
    #ordering = ['created_at']
    
    search_fields = ['state','city','district']


admin.site.register(ClassifyZone,ClassifyZoneAdmin)


class BranchZoneAdmin(admin.ModelAdmin):
    
    list_display = ('code','name','barcode')
    list_display_links = ('code','name',)

    #date_hierarchy = 'created'
    #ordering = ['created_at']
    
    inlines = [ClassifyZoneInline]
    
    search_fields = ['code','name','barcode']


admin.site.register(BranchZone,BranchZoneAdmin)


class YundaCustomerAdmin(admin.ModelAdmin):
    
    list_display = ('cus_id','name','code','company_name','qr_id','lanjian_id','ludan_id','sn_code','device_code',
                    'contacter','mobile','on_qrcode','on_lanjian','on_ludan','on_bpkg','status','memo')
    list_display_links = ('name','company_name',)

    #date_hierarchy = 'created'
    #ordering = ['created_at']
    
    list_filter = ('status',)
    search_fields = ['cus_id','name','code','sync_addr','company_name','contacter']


admin.site.register(YundaCustomer,YundaCustomerAdmin)


class ParentPackageWeightAdmin(admin.ModelAdmin):
    
    list_display = ('parent_package_id','weight','upload_weight','weighted','uploaded'
                    ,'destinate','is_jzhw','is_charged')
    list_display_links = ('parent_package_id',)

    #date_hierarchy = 'created'
    #ordering = ['created_at']
    
    list_filter = ('is_jzhw','is_charged')
    search_fields = ['parent_package_id','destinate']
    


admin.site.register(ParentPackageWeight,ParentPackageWeightAdmin)


class TodaySmallPackageWeightAdmin(admin.ModelAdmin):
    
    list_display = ('package_id','parent_package_id','weight','upload_weight','weighted','is_jzhw')
    list_display_links = ('package_id','parent_package_id',)

    #date_hierarchy = 'created'
    #ordering = ['created_at']
    
    list_filter = ('is_jzhw',)
    search_fields = ['package_id','parent_package_id']
    
    def package_id_link(self, obj):
        if  obj.weight and float(obj.weight) > 3:
            return u'<a href="%s/" style="color:blue;background-color:red;">%s</a>'%\
                (obj.package_id,obj.package_id)
        return u'<a href="%s/">%s</a>'%(obj.package_id,obj.package_id)
    
    package_id_link.allow_tags = True
    package_id_link.short_description = u"运单编号" 
    
    class Media:
        css = {"all": ("admin/css/forms.css","css/admin/dialog.css", "jquery/jquery-ui-1.10.1.css")}
        js = ("script/admin/adminpopup.js","jquery/jquery-ui-1.8.13.min.js",
              "jquery/addons/jquery.upload.js","yunda/js/package.csvfile.upload.js")
    
    
    def calJZHWeightRule(self,weight):
        
        return weight < 0.5 and weight or weight*0.94
            
        
    def calExternalWeightRule(self,weight):
        
        if weight < 0.5:
            return weight
        if weight < 1.0:
            return weight / 2
        if weight < 4.0:
            return weight / 2 + 0.3
        return weight - 1.5
            
    
    def calcSmallPackageWeight(self,package_id):
        
        try:
            spw = LogisticOrder.objects.get(out_sid=package_id)
        except Exception,exc:
            raise Exception(u'小包号:%s,运单信息未入库!'%(package_id))

        if not spw.weight or float(spw.weight) <= 0:
            raise Exception(u'小包号:%s,重量为空!'%package_id)
        
        if spw.is_jzhw:
            return round(spw.weight,2),round(self.calJZHWeightRule(float(spw.weight)),2)
            
        return round(spw.weight,2),round(self.calExternalWeightRule(float(spw.weight)),2)
        
     
    def calcPackageWeightAction(self,request,queryset):
        
        for tspw in queryset:
            try:
                weight_tuple = self.calcSmallPackageWeight(tspw.package_id)
            except Exception,exc:
                messages.warning(request, exc.message)
            else:
                if weight_tuple[0] > 10:
                    message.warning(rquest,u'小包（%s）重量超过10公斤,请核实！'%tspw.package_id)
                    
                tspw.weight = weight_tuple[0]
                tspw.upload_weight = weight_tuple[1]
                tspw.save()
        
    calcPackageWeightAction.short_description = u"计算小包重量" 
    
    def _getPackageWeightDict(self,queryset):
        
        ydo_list = []
        for package in queryset:
            
            ydo_list.append({'valid_code':'',
                             'package_id':package.package_id,
                             'weight':package.weight,
                             'upload_weight':package.upload_weight,
                             'weighted':package.weighted,
                             'is_parent':False})
        return ydo_list
    
    def uploadPackageWeightAction(self,request,queryset):
        
        try:
            yd_service = YundaService(cus_code='QIYUE')
            
            for yd_list in group_list(self._getPackageWeightDict(queryset),WEIGHT_UPLOAD_LIMIT):
                
                yd_service.uploadWeight(yd_list)
                yd_service.flushPackageWeight(yd_list)
                 
        except Exception,exc:
            messages.warning(request, exc.message)
        else:
            messages.info(request, u'上传成功！')    
        
            
    uploadPackageWeightAction.short_description = u"上传小包重量"   
    
    actions = ['calcPackageWeightAction','uploadPackageWeightAction']  
    

admin.site.register(TodaySmallPackageWeight,TodaySmallPackageWeightAdmin)


class TodayParentPackageWeightAdmin(admin.ModelAdmin):
    
    list_display = ('parent_package_id','weight','upload_weight','weighted','is_jzhw')
    list_display_links = ('parent_package_id',)

    #date_hierarchy = 'created'
    #ordering = ['created_at']
    
    list_filter = ('is_jzhw',)
    search_fields = ['parent_package_id',]
    
    class Media:
        css = {"all": ("admin/css/forms.css","css/admin/dialog.css", "jquery/jquery-ui-1.10.1.css")}
        js = ("script/admin/adminpopup.js","jquery/jquery-ui-1.8.13.min.js",
              "jquery/addons/jquery.upload.js","yunda/js/package.csvfile.upload.js")
        
    def calcSmallPackageWeight(self,parent_package_id):
        
        tspws = TodaySmallPackageWeight.objects.filter(
                                parent_package_id=parent_package_id)
        bpkw_weight = 0
        bpkw_upload_weight = 0
        for tspw in tspws:
            if not tspw.weight or not tspw.upload_weight or float(tspw.weight) <= 0:
                raise Exception(u'大包号:%s,小包号:%s,没有重量,请核对!'%
                                (tspw.parent_package_id,tspw.package_id))
                
            bpkw_weight += float(tspw.weight)
            bpkw_upload_weight += float(tspw.upload_weight)
            
        return bpkw_weight,bpkw_upload_weight
        
     #取消该商品缺货订单
    def calcPackageWeightAction(self,request,queryset):
        
        for bpkw in queryset:
            try:
                weight_tuple = self.calcSmallPackageWeight(bpkw.parent_package_id)
            except Exception,exc:
                messages.warning(request, exc.message)
            else:
                if weight_tuple[0] > 50:
                    messages.error(request, u'集包号(%s)重量异常(%s)，请核实。'%
                                   (bpkw.parent_package_id,weight_tuple[0]))
                    continue
                bpkw.weight = weight_tuple[0]
                bpkw.upload_weight = weight_tuple[1]
                bpkw.save()
        
    calcPackageWeightAction.short_description = u"计算大包重量"  
    
    def _getPackageWeightDict(self,queryset):
        
        ydo_list = []
        for package in queryset:
             
            ydo_list.append({'valid_code':'',
                             'package_id':package.parent_package_id,
                             'weight':package.weight,
                             'upload_weight':package.upload_weight,
                             'weighted':package.weighted,
                             'is_parent':True})
        return ydo_list
    
    def uploadPackageWeightAction(self,request,queryset):
        
        try:
            yd_service = YundaService(cus_code='QIYUE')
            
            for yd_list in group_list(self._getPackageWeightDict(queryset),WEIGHT_UPLOAD_LIMIT):
                
                yd_service.uploadWeight(yd_list)
                yd_service.flushPackageWeight(yd_list)
                
        except Exception,exc:
            messages.warning(request, exc.message)
        else:
            messages.info(request, u'上传成功！')
                        
    uploadPackageWeightAction.short_description = u"上传大包重量"   
    
    actions = ['calcPackageWeightAction','uploadPackageWeightAction']  
    


admin.site.register(TodayParentPackageWeight,TodayParentPackageWeightAdmin)


class LogisticOrderAdmin(admin.ModelAdmin):
    
    list_display = ('cus_oid','out_sid','weight','receiver_name','receiver_state','receiver_city',
                    'receiver_mobile','weighted','created','is_charged','sync_addr','status')#,'customer'
    list_display_links = ('out_sid','cus_oid',)

    #date_hierarchy = 'created'
    #ordering = ['created_at']
    
    list_filter = ('status','is_charged','sync_addr',('weighted',DateFieldListFilter),('created',DateFieldListFilter))
    search_fields = ['cus_oid','out_sid','parent_package_id','receiver_mobile']
    
    

admin.site.register(LogisticOrder,LogisticOrderAdmin)



