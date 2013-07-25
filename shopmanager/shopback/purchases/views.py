#-*- coding:utf8 -*-
import os
import datetime
import json
import csv
import cStringIO as StringIO
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.servers.basehttp import FileWrapper
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse
from django.conf import settings
from django.db.models import Q,Sum,F
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError, transaction
from djangorestframework.serializer import Serializer
from djangorestframework.utils import as_tuple
from djangorestframework import status
from djangorestframework.renderers import BaseRenderer
from djangorestframework.response import Response
from djangorestframework.mixins import CreateModelMixin
from djangorestframework.views import ModelView,ListOrCreateModelView,InstanceModelView
from shopback.archives.models import Deposite,Supplier,PurchaseType
from shopback.items.models import Product,ProductSku
from shopback.purchases.models import Purchase,PurchaseItem,PurchaseStorage,PurchaseStorageItem,\
    PurchaseStorageRelationship,PurchasePaymentItem
from shopback import paramconfig as pcfg
from shopback.purchases import permissions as perm
from shopback.base import log_action, ADDITION, CHANGE
from shopback.purchases import permissions as perms
from shopback.monitor.models import SystemConfig
from utils import CSVUnicodeWriter
from auth import staff_requried
import logging

logger = logging.getLogger('purchases.handler')
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
        if not purchase.service_date:
            purchase.service_date = datetime.datetime.now()
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
        
        if purchase.status!=pcfg.PURCHASE_DRAFT and not perms.has_check_purchase_permission(request.user):
            return '你没有权限修改'
        
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
    
    if purchase.status!=pcfg.PURCHASE_DRAFT and not perms.has_check_purchase_permission(request.user):
        return HttpResponse(
                            json.dumps({'code':1,'response_error':u'你没有权限删除'}),
                            mimetype='application/json')
    
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
        post_date   = content.get('post_date',None)  
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
        if not purchase.post_date:
            purchase.post_date = datetime.datetime.now()
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
        
        if purchase.status!=pcfg.PURCHASE_DRAFT and not perms.has_confirm_storage_permission(request.user):
            return '你没有权限修改'
        
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

        permissions = {
                 'refresh_storage_ship':purchase_storage.status==pcfg.PURCHASE_DRAFT,
                 'confirm_storage_ship':not undist_storage_items and purchase_storage.status==pcfg.PURCHASE_DRAFT \
                    and perms.has_confirm_storage_permission(request.user)
                 }

        return {'undist_storage_items':undist_storage_items,
                'ship_purchases':ship_purchases,
                'purchase_storage':purchase_storage,
                'perms':permissions}
    
    def post(self, request, id, *args, **kwargs):
        
        try:
            purchase_storage = PurchaseStorage.objects.get(id=id,status=pcfg.PURCHASE_DRAFT)
        except:
            return u'未找到入库单'
        
        undist_storage_items = purchase_storage.distribute_storage_num()
        if undist_storage_items:
            return u'入库项未完全关联采购单'
        
        config = SystemConfig.getconfig()
        
        with transaction.commit_on_success():
            ship_storage_items = PurchaseStorageRelationship.objects.filter(storage_id=purchase_storage.id)
            for item in ship_storage_items:
                item.confirm_storage(config.purchase_price_to_cost_auto)
            
            #如果确认收货，则库存自动入库
            if config.storage_num_to_stock_auto:
                for storage_item in purchase_storage.normal_storage_items.filter(is_addon=False):
                    outer_id     = storage_item.outer_id
                    outer_sku_id = storage_item.outer_sku_id
                    prod = Product.objects.get(outer_id=outer_id)
                    if outer_sku_id:
                        prod_sku = ProductSku.objects.get(outer_id=outer_sku_id,product=prod)
                        prod_sku.update_quantity_incremental(storage_item.storage_num,reverse=True)
                    else:
                        prod.update_collect_num_incremental(storage_item.storage_num,reverse=True)
                    storage_item.is_addon = True
                    storage_item.save()
                    
                purchase_storage.is_addon = True
                        
        purchase_storage.status = pcfg.PURCHASE_APPROVAL
        purchase_storage.save()
        
        log_action(request.user.id,purchase_storage,CHANGE,u'确认收货')
        
        return {'id':purchase_storage.id,'status':purchase_storage.status}
        
@csrf_exempt        
@staff_requried
def refresh_purchasestorage_ship(request,id):
    
    try:
        purchase_storage = PurchaseStorage.objects.get(id=id,status=pcfg.PURCHASE_DRAFT)
    except:
        return HttpResponse('<html><body style="text-align:center;"><h1>未找到该入库单</h1></body></html>')
    
    ship_storage_items = PurchaseStorageRelationship.objects.filter(storage_id=purchase_storage.id)
    for item in ship_storage_items:
        item.delete()
    
    log_action(request.user.id,purchase_storage,CHANGE,u'重新关联')
    
    return HttpResponseRedirect('/purchases/storage/distribute/%s/'%id)
    
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
        
    if purchase.status!=pcfg.PURCHASE_DRAFT and not perms.has_confirm_storage_permission(request.user):
        return HttpResponse(
                            json.dumps({'code':1,'response_error':u'你没有权限删除'}),
                            mimetype='application/json')
        
    storage_item = PurchaseStorageItem.objects.get(id=purchase_item_id,purchase_storage=purchase)
    storage_item.status = pcfg.DELETE
    storage_item.save()
    
    log_action(request.user.id,purchase,CHANGE,u'入库项作废')
    
    return HttpResponse(json.dumps({'code':0,'response_content':'success'}),mimetype='application/json')
    

@staff_requried    
def download_purchasestorage_file(request,id):
    """ 下载入库单信息 """
    try:
        purchase = PurchaseStorage.objects.get(id=id)
    except PurchaseStorage.DoesNotExist:
        raise Http404
    
    is_windows = request.META['HTTP_USER_AGENT'].lower().find('windows') >-1 
    file_name = u'storage-contract(NO-%s).csv'%str(purchase.id)
    myfile = StringIO.StringIO() 
    pcsv = purchase.gen_csv_tuple()
    writer = CSVUnicodeWriter(myfile,encoding= is_windows and "gbk" or 'utf8')
    writer.writerows(pcsv)
        
    response = HttpResponse(myfile.getvalue(), mimetype='application/octet-stream')
    myfile.close()
    response['Content-Disposition'] = 'attachment; filename=%s'%file_name
    #response['Content-Length'] = str(os.stat(file_path).st_size)
    return response

#################################### 采购付款项 #################################
class PurchasePaymentView(ModelView):
    """ 采购付款 """
    
    def get(self, request, *args, **kwargs):
        
        waitpay_purchases = Purchase.objects.filter(status=pcfg.PURCHASE_APPROVAL)
        waitpay_storages  = PurchaseStorage.objects.filter(status=pcfg.PURCHASE_APPROVAL)
        
        return {'purchases':waitpay_purchases,'storages':waitpay_storages}
        
    def post(self, request, *args, **kwargs):
        
        content   = request.REQUEST
        paytype   = content.get('paytype')
        purchase_id    = content.get('purchase')
        storage_detail = content.getlist('storage_detail')
        payment        = content.get('payment')
        origin_no      = content.get('origin_no')
        additional     = content.get('additional')
        memo           = content.get('memo')
        
        waitpay_purchases = Purchase.objects.filter(status=pcfg.PURCHASE_APPROVAL)
        waitpay_storages  = PurchaseStorage.objects.filter(status=pcfg.PURCHASE_APPROVAL)
        
        purchase  = None
        storage   = None
        payment_item = None
        try:
            with transaction.commit_on_success():
                
                payment   = float(payment or 0)
                if not payment:
                    raise Exception(u'付款金额不能为空')
                elif paytype in (pcfg.PC_PREPAID_TYPE,pcfg.PC_POD_TYPE):
                    if not purchase_id:
                        raise Exception(u'请选择采购单')
                    try:
                        purchase = Purchase.objects.get(id=purchase_id,status=pcfg.PURCHASE_APPROVAL)
                    except Purchase.DoesNotExist:
                        raise Exception(u'请选择正确的采购单')
                    else:
                        purchase.pay(payment)
                        
                elif paytype==pcfg.PC_COD_TYPE:
                    if not storage_id:
                        raise Exception(u'请选择入库单')
                    try:
                        storage = PurchaseStorage.objects.get(id=storage_id,status=pcfg.PURCHASE_APPROVAL)
                    except PurchaseStorage.DoesNotExist:
                        raise Exception(u'请选择正确的入库单')
                    else:
                        storage.pay(payment)
                        
                elif paytype==pcfg.PC_OTHER_TYPE:
                    if (purchase_id and storage_id) or (not purchase_id and not storage_id):
                        raise Exception(u'请选择采购单或物流单之一')
                    if purchase_id:
                        try:
                            purchase = Purchase.objects.get(id=purchase_id,status=pcfg.PURCHASE_APPROVAL)
                        except Purchase.DoesNotExist:
                            raise Exception(u'未找到采购单')
                        else:  
                            purchase.pay(payment,additional=additional)
                    else:
                        try:
                            storage = PurchaseStorage.objects.get(id=storage_id)
                        except PurchaseStorage.DoesNotExist:
                            raise Exception(u'未找到入库单')     
                        else:
                            storage.pay(payment,additional=additional) 
                else:
                    raise Exception(u'请选择正确的付款类型') 
                
                payment_item = PurchasePaymentItem.objects.create(
                                                                  pay_type=paytype,
                                                                  storage_id=storage_id,
                                                                  purchase_id=purchase_id,
                                                                  pay_time=datetime.datetime.now(),
                                                                  payment=payment,
                                                                  origin_no=origin_no,
                                                                  extra_info=memo)
        except Exception,exc:
            logger.error(exc,exc_info=True)
            return {'purchases':waitpay_purchases,'storages':waitpay_storages,'error_msg':exc.message}
        else:
            return HttpResponseRedirect("/admin/purchases/purchasepaymentitem/?q=%s"%payment_item.id)
            
            
class CODPaymentDistributeView(ModelView):
    """ 货到付款多入库单金额分配 """
    
    def get(self, request, *args, **kwargs):
        
        content     = request.REQUEST
        storageids  = content.getlist('storageids')
        wait_payments = {}
        
        for sid in storageids:
            try:
                storage = PurchaseStorage.objects.get(id=sid,status=pcfg.PURCHASE_APPROVAL)
            except PurchaseStorage.DoesNotExist:
                raise Http404
            else:
                relat_ships = PurchaseStorageRelationship.objects.filter(storage_id=sid)
                for ship in relat_ships:
                    
                    
        
        
   
        
    