# -*- coding:utf8 -*-
from django.contrib import admin
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.encoding import force_unicode

from django.db import models
from django.forms import TextInput, Textarea
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse

from shopback.archives.models import SupplierType, Supplier, Deposite, PurchaseType, DepositeDistrict
from shopback.items.models import ProductLocation


class CustomAdmin(admin.ModelAdmin):
    """ 自定义Admin """

    def response_add(self, request, obj, post_url_continue='../%s/'):
        """
        Determines the HttpResponse for the add_view stage.
        """

        opts = obj._meta
        pk_value = obj._get_pk_val()

        msg = _('The %(name)s "%(obj)s" was added successfully.') % \
              {'name': force_unicode(opts.verbose_name), 'obj': force_unicode(obj)}

        if "_continue" in request.POST:
            self.message_user(request, msg + ' ' + _("You may edit it again below."))
            if "_popup" in request.POST:
                post_url_continue += "?_popup=1"
            return HttpResponseRedirect(post_url_continue % pk_value)

        if "_save" in request.POST:
            self.message_user(request, msg)
            return HttpResponseRedirect(post_url_continue % pk_value)
        elif "_popup" in request.POST:
            return HttpResponse(
                '<!DOCTYPE html><html><head><title></title></head><body>'
                '<script type="text/javascript">opener.dismissAddAnotherPopup(window, "%s", "%s");</script></body></html>' % \
                # escape() calls force_unicode.
                (cgi.escape(pk_value), cgi.escapejs(obj)))
        elif "_addanother" in request.POST:
            self.message_user(request,
                              msg + ' ' + (_("You may add another %s below.") % force_unicode(opts.verbose_name)))
            return HttpResponseRedirect(request.path)
        else:
            self.message_user(request, msg)
            if self.has_change_permission(request, None):
                post_url = reverse('admin:%s_%s_changelist' %
                                   (opts.app_label, opts.module_name),
                                   current_app=self.admin_site.name)
            else:
                post_url = reverse('admin:index',
                                   current_app=self.admin_site.name)
            return HttpResponseRedirect(post_url)


class ProductLocationInline(admin.TabularInline):
    model = ProductLocation
    fields = ('product_id', 'sku_id', 'outer_id', 'name', 'outer_sku_id', 'properties_name')

    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '20'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})},
    }


class DepositeAdmin(CustomAdmin):
    list_display = ('id', 'deposite_name', 'location', 'in_use', 'extra_info')
    # list_editable = ('update_time','task_type' ,'is_success','status')


    list_filter = ('in_use',)
    search_fields = ['id', 'deposite_name', 'location']


admin.site.register(Deposite, DepositeAdmin)


class DepositeDistrictAdmin(admin.ModelAdmin):
    list_display = ('id', 'parent_no', 'district_no', 'location', 'in_use', 'extra_info')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    inlines = [ProductLocationInline]

    list_filter = ('in_use',)
    search_fields = ['id', 'parent_no', 'district_no', 'location']


admin.site.register(DepositeDistrict, DepositeDistrictAdmin)


class SupplierTypeAdmin(CustomAdmin):
    list_display = ('id', 'type_name', 'extra_info')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    search_fields = ['id', 'type_name']


admin.site.register(SupplierType, SupplierTypeAdmin)


class SupplierAdmin(CustomAdmin):
    list_display = ('id', 'supply_type', 'supplier_name', 'contact', 'phone', 'mobile', 'fax', 'zip_code', 'email'
                    , 'address', 'account_bank', 'account_no', 'main_page', 'in_use')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('supply_type', 'in_use',)
    search_fields = ['id', 'supplier_name']

    # --------设置页面布局----------------
    fieldsets = (('供应商基本信息:', {
        'classes': ('expand',),
        'fields': (('supplier_name', 'supply_type')
                   , ('contact', 'phone')
                   , ('mobile', 'fax')
                   , ('zip_code', 'email')
                   , ('address')
                   , ('account_bank', 'account_no')
                   , ('main_page', 'in_use')
                   , 'extra_info')
    }),
                 )


admin.site.register(Supplier, SupplierAdmin)


class PurchaseTypeAdmin(CustomAdmin):
    list_display = ('id', 'type_name', 'in_use', 'extra_info')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('in_use',)
    search_fields = ['id', 'type_name']


admin.site.register(PurchaseType, PurchaseTypeAdmin)
