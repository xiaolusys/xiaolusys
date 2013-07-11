#-*- coding:utf8 -*-
import os
import datetime
import json
import csv
import cStringIO as StringIO
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse, Http404
from django.core.servers.basehttp import FileWrapper
from django.template.loader import render_to_string
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from djangorestframework.serializer import Serializer
from djangorestframework.utils import as_tuple
from djangorestframework import status
from djangorestframework.renderers import BaseRenderer
from djangorestframework.response import Response
from djangorestframework.mixins import CreateModelMixin
from djangorestframework.views import ModelView,ListOrCreateModelView,InstanceModelView
from shopback.archives.models import Deposite,Supplier,PurchaseType
from shopback.items.models import Product,ProductSku
from shopback.purchases.models import Purchase,PurchaseItem,PurchaseStorage,PurchaseStorageItem,PurchaseStorageRelationship
from shopback import paramconfig as pcfg
from shopback.purchases import permissions as perm
from shopback.base import log_action, ADDITION, CHANGE
from utils import CSVUnicodeWriter
from auth import staff_requried

#################################### 采购单 #################################

class PurchaseView(ModelView):
    """ 采购单 """
    
    def get(self, request, *args, **kwargs):
        
        params = {}
        params['suppliers']      = Supplier.objects.filter(in_use=True)
        params['deposites']      = Deposite.objects.filter(in_use=True)
        params['purchase_types'] = PurchaseType.objects.filter(in_use=True)
        
        return params
    
    def post(self, request, *args, **kwargs):
        
        content = request.REQUEST
        purchase_id = content.get('purchase_id')
        purchase    = None
        if purchase_id:
            try:
                purchase = Purchase.objects.get(id=purchase_id)
            except:
                return u'输入采购编号未找到'
        else:
            purchase = Purchase()

        for k,v in content.iteritems():
            if not v :continue
            hasattr(purchase,k) and setattr(purchase,k,v)
        purchase.save()
        
        log_action(request.user.id,purchase,ADDITION,u'创建采购单')
        
        return {'id':purchase.id}


class PurchaseInsView(ModelView):
    """ 采购单修改界面 """
    
    def get(self, request, id, *args, **kwargs):
        
        try:
            purchase = Purchase.objects.get(id=id)
        except Exception,exc:
            raise Http404
            
        params = {}
        params['suppliers']      = Supplier.objects.filter(in_use=True)
        params['deposites']      = Deposite.objects.filter(in_use=True)
        params['purchase_types'] = PurchaseType.objects.filter(in_use=True)
        params['purchase']       = purchase.json
        params['perms']          = {
                                    'can_check_purchase':purchase.status == pcfg.PURCHASE_DRAFT \
                                        and perm.has_check_purchase_permission(request.user),
                                    'can_show_storage':purchase.status in (pcfg.PURCHASE_APPROVAL,pcfg.PURCHASE_FINISH)}
        return params
    
    def post(self, request, id, *args, **kwargs):
        
        try:
            purchase = Purchase.objects.get(id=id)
        except Exception,exc:
            raise Http404
        
        if purchase.status != pcfg.PURCHASE_DRAFT :
            return u'该采购无需审核'
        
        if not perm.has_check_purchase_permission(request.user):
            return u'你没有权限审核'
        
        purchase.status = pcfg.PURCHASE_APPROVAL
        purchase.save()
        
        return {'id':purchase.id,'status':purchase.status}


class PurchaseItemView(ModelView):
    """ 采购单项 """
    
    def get(self, request, *args, **kwargs):
        
        pass
        
    def post(self, request, *args, **kwargs):
        
        content = request.REQUEST
        
        purchase_id = content.get('purchase_id')
        outer_id = content.get('outer_id')
        sku_id   = content.get('sku_id')
        price    = content.get('price')
        num      = content.get('num')
        supplier_item_id = content.get('supplier_item_id')
        std_price = content.get('std_price')
        
        prod     = None
        prod_sku = None
        try:
            prod = Product.objects.get(outer_id=outer_id)
            if sku_id:
                prod_sku = ProductSku.objects.get(outer_id=sku_id,product=prod)
        except :
            return u'未找到商品及规格' 
        
        try:
            purchase = Purchase.objects.get(id=purchase_id)
        except:
            return u'未找到采购单'
        
        purchase_item,state = PurchaseItem.objects.get_or_create(
                                purchase=purchase,outer_id=outer_id,outer_sku_id=sku_id)
        purchase_item.name = prod.name
        purchase_item.properties_name  = prod_sku and prod_sku.name or ''
        purchase_item.supplier_item_id = supplier_item_id
        purchase_item.std_price = std_price
        purchase_item.price = price
        purchase_item.purchase_num = num
        purchase_item.total_fee = float(price or 0)*int(num or 0)
        purchase_item.save()
        
        log_action(request.user.id,purchase,CHANGE,u'%s采购项（%s,%s）'%(state and u'添加' or u'修改',outer_id,sku_id))
        
        return purchase_item.json


class PurchaseShipStorageView(ModelView):
    """ 采购单与入库单关联视图 """
    
    def get(self, request, id, *args, **kwargs):
        try:
            purchase = Purchase.objects.get(id=id)
        except:
            return u'未找到采购单'
        
        #给关联采购单分配入库数量，并返回未分配的入库数
        unfinish_purchase_items = purchase.unfinish_purchase_items            
        #获取关联采购单信息
        ship_storages        = purchase.get_ship_storages()
        
        return {'unfinish_purchase_items':unfinish_purchase_items,'ship_storages':ship_storages}
    

@csrf_exempt        
@staff_requried    
def delete_purchase_item(request):
    """ 删除采购项 """
    content     = request.REQUEST
    purchase_id = content.get('purchase_id')
    purchase_item_id = content.get('purchase_item_id')
    
    try:
        purchase = Purchase.objects.get(id=purchase_id)
    except:
        raise http404
        
    purchase_item = PurchaseItem.objects.get(id=purchase_item_id,purchase=purchase)
    purchase_item.status = pcfg.DELETE
    purchase_item.save()
    
    log_action(request.user.id,purchase,CHANGE,u'采购项作废')
    
    return HttpResponse(json.dumps({'code':0,'response_content':'success'}),mimetype='application/json')
    

@staff_requried    
def download_purchase_file(request,id):
    """ 下载采购合同信息 """
    try:
        purchase = Purchase.objects.get(id=id)
    except Purchase.DoesNotExist:
        raise Http404
    
    is_windows = request.META['HTTP_USER_AGENT'].lower().find('windows') >-1 
    file_name = u'purchase-contract(NO-%s).csv'%str(purchase.id)
    myfile = StringIO.StringIO() 
    pcsv = purchase.gen_csv_tuple()
    writer = CSVUnicodeWriter(myfile,encoding= is_windows and "gbk" or 'utf8')
    writer.writerows(pcsv)
        
    response = HttpResponse(myfile.getvalue(), mimetype='application/octet-stream')
    myfile.close()
    response['Content-Disposition'] = 'attachment; filename=%s'%file_name
    #response['Content-Length'] = str(os.stat(file_path).st_size)
    return response


#################################### 采购入库单 #################################

class PurchaseStorageView(ModelView):
    """ 采购单 """
    
    def get(self, request, *args, **kwargs):
        
        params = {}
        params['suppliers']      = Supplier.objects.filter(in_use=True)
        params['deposites']      = Deposite.objects.filter(in_use=True)
        
        return params
    
    def post(self, request, *args, **kwargs):
        
        content = request.REQUEST
        purchase_id = content.get('purchase_storage_id')
        purchase    = None
        if purchase_id:
            try:
                purchase = PurchaseStorage.objects.get(id=purchase_id)
            except:
                return u'输入采购编号未找到'
        else:
            purchase = PurchaseStorage()

        for k,v in content.iteritems():
            if not v :continue
            hasattr(purchase,k) and setattr(purchase,k,v)
        purchase.save()
        
        log_action(request.user.id,purchase,ADDITION,u'创建采购单')
        
        return {'id':purchase.id}


class PurchaseStorageInsView(ModelView):
    """ 采购单修改界面 """
    
    def get(self, request, id, *args, **kwargs):
        
        try:
            purchase = PurchaseStorage.objects.get(id=id)
        except Exception,exc:
            raise Http404
            
        params = {}
        params['suppliers']      = Supplier.objects.filter(in_use=True)
        params['deposites']      = Deposite.objects.filter(in_use=True)
        params['purchase_storage'] = purchase.json
        
        return params


class PurchaseStorageItemView(ModelView):
    """ 采购单项 """
    
    def get(self, request, *args, **kwargs):
        
        pass
        
    def post(self, request, *args, **kwargs):
        
        content = request.REQUEST
        
        purchase_id = content.get('purchase_storage_id')
        outer_id = content.get('outer_id')
        sku_id   = content.get('sku_id')
        num      = content.get('num')
        
        prod     = None
        prod_sku = None
        try:
            prod = Product.objects.get(outer_id=outer_id)
            if sku_id:
                prod_sku = ProductSku.objects.get(outer_id=sku_id,product=prod)
        except :
            return u'未找到商品及规格' 
        
        try:
            purchase = PurchaseStorage.objects.get(id=purchase_id)
        except:
            return u'未找到入库单'
        
        purchase_item,state = PurchaseStorageItem.objects.get_or_create(
                                purchase_storage=purchase,outer_id=outer_id,outer_sku_id=sku_id)
        purchase_item.name = prod.name
        purchase_item.properties_name  = prod_sku and prod_sku.name or ''
        purchase_item.storage_num = num
        purchase_item.status = pcfg.NORMAL
        purchase_item.save()
        
        log_action(request.user.id,purchase,CHANGE,u'%s采购项（%s,%s）'%(state and u'添加' or u'修改',outer_id,sku_id))
        
        return purchase_item.json


class StorageDistributeView(ModelView):
    """ 采购入库单匹配 """
    
    def get(self, request, id, *args, **kwargs):
        try:
            purchase_storage = PurchaseStorage.objects.get(id=id)
        except:
            return u'未找到入库单'
        
        #给关联采购单分配入库数量，并返回未分配的入库数
        undist_storage_items = purchase_storage.distribute_storage_num()            
        #获取关联采购单信息
        ship_purchases       = purchase_storage.get_ship_purchases()
        
        return {'undist_storage_items':undist_storage_items,'ship_purchases':ship_purchases}
    
    
@csrf_exempt        
@staff_requried    
def delete_purchasestorage_item(request):
    """ 删除采购项 """
    content     = request.REQUEST
    purchase_id = content.get('purchase_storage_id')
    purchase_item_id = content.get('purchase_storage_item_id')
    
    try:
        purchase = PurchaseStorage.objects.get(id=purchase_id)
    except PurchaseStorage.DoesNotExist:
        raise http404
        
    storage_item = PurchaseStorageItem.objects.get(id=purchase_item_id,purchase_storage=purchase)
    storage_item.status = pcfg.DELETE
    storage_item.save()
    
    log_action(request.user.id,purchase,CHANGE,u'采购项作废')
    
    return HttpResponse(json.dumps({'code':0,'response_content':'success'}),mimetype='application/json')
    

@staff_requried    
def download_purchasestorage_file(request,id):
    """ 下载采购合同信息 """
    try:
        purchase = PurchaseStorage.objects.get(id=id)
    except PurchaseStorage.DoesNotExist:
        raise Http404
    
    is_windows = request.META['HTTP_USER_AGENT'].lower().find('windows') >-1 
    file_name = u'purchase-contract(NO-%s).csv'%str(purchase.id)
    myfile = StringIO.StringIO() 
    pcsv = purchase.gen_csv_tuple()
    writer = CSVUnicodeWriter(myfile,encoding= is_windows and "gbk" or 'utf8')
    writer.writerows(pcsv)
        
    response = HttpResponse(myfile.getvalue(), mimetype='application/octet-stream')
    myfile.close()
    response['Content-Disposition'] = 'attachment; filename=%s'%file_name
    #response['Content-Length'] = str(os.stat(file_path).st_size)
    return response

