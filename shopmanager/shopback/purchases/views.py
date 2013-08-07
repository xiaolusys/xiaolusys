#-*- coding:utf8 -*-
import re
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
from django.contrib import messages
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
    PurchaseStorageRelationship,PurchasePayment,PurchasePaymentItem
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
        state       = False
        
        if purchase_id:
            try:
                purchase = Purchase.objects.get(id=purchase_id)
            except:
                return u'输入采购编号未找到'
        else:
            state = True
            purchase = Purchase()

        for k,v in content.iteritems():
            if not v :continue
            hasattr(purchase,k) and setattr(purchase,k,v)
        if not purchase.service_date:
            purchase.service_date = datetime.datetime.now()
        purchase.save()
        
        log_action(request.user.id,purchase,state and ADDITION or CHANGE,u'%s采购单'%(state and u'新建' or u'修改'))
        
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
        
        log_action(request.user.id,purchase,CHANGE,u'审核采购单')
        
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
        
        if purchase.status==pcfg.PURCHASE_FINISH :
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
        purchase_item.status=pcfg.NORMAL
        purchase_item.save()
        
        log_action(request.user.id,purchase,CHANGE,u'%s采购项（%s,%s,%s,%s）'%
                   (state and u'添加' or u'修改',outer_id,sku_id,num,price))
        
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
    """ 入库单 """
    
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
        state       = False
        
        if purchase_id:
            try:
                purchase = PurchaseStorage.objects.get(id=purchase_id)
            except:
                return u'输入采购编号未找到'
        else:
            state = True
            purchase = PurchaseStorage()
        
        for k,v in content.iteritems():
            if not v :continue
            hasattr(purchase,k) and setattr(purchase,k,v)
        if not purchase.post_date:
            purchase.post_date = datetime.datetime.now()
        purchase.save()
        
        log_action(request.user.id,purchase,state and ADDITION or CHANGE,u'%s入库单'%(state and u'新建' or u'修改'))
        
        return {'id':purchase.id}


class PurchaseStorageInsView(ModelView):
    """ 入库单修改界面 """
    
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
    """ 入库单项 """
    
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
        
        if purchase_storage.normal_storage_items.count()==0:
            return u'空入库单'
            
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
        waitpay_storages  = PurchaseStorage.objects.filter(status__in=(pcfg.PURCHASE_APPROVAL,pcfg.PURCHASE_DRAFT))

        return {'purchases':waitpay_purchases,'storages':waitpay_storages}
        
    def post(self, request, *args, **kwargs):
        
        content   = request.REQUEST
        paytype   = content.get('paytype')
        purchase_id    = content.get('purchase')
        storageids = content.getlist('storage')
        payment        = content.get('payment')
        memo           = content.get('memo')
        
        waitpay_purchases = Purchase.objects.filter(status=pcfg.PURCHASE_APPROVAL)
        waitpay_storages  = PurchaseStorage.objects.filter(status__in=(pcfg.PURCHASE_APPROVAL,pcfg.PURCHASE_DRAFT))
        
        purchase            = None
        purchase_payment    = None
        storages            = []
        
        try:
            payment   = float(payment or 0)
            if not payment:
                raise Exception(u'付款金额不能为空')
            
            if paytype==pcfg.PC_PREPAID_TYPE:
                if not purchase_id:
                    raise Exception(u'请选择采购单')
                
                purchase = Purchase.objects.get(id=purchase_id,status=pcfg.PURCHASE_APPROVAL)
                
            elif paytype in (pcfg.PC_POD_TYPE,pcfg.PC_COD_TYPE):
                for storage_id in storageids:
                    storage =  PurchaseStorage.objects.get(id=storage_id,\
                                                status__in=(pcfg.PURCHASE_DRAFT,pcfg.PURCHASE_APPROVAL))
                    storages.append(storage)
                    
                if paytype == pcfg.PC_POD_TYPE and len(storages) != 1:
                    raise Exception(u'请选择一个入库单')
                
                if paytype == pcfg.PC_POD_TYPE:
                    undist_storage_items = storages[0].distribute_storage_num()
                    if undist_storage_items:
                        raise Exception(u'入库项未完全关联采购单')
                
            elif paytype==pcfg.PC_OTHER_TYPE:
                if (purchase_id and storage_id) or (not purchase_id and not storage_id):
                    raise Exception(u'请选择采购单或物流单之一')
                
                if purchase_id:
                    purchase = Purchase.objects.get(id=purchase_id,status=pcfg.PURCHASE_APPROVAL)
                else:
                    for storage_id in storageids:
                        storage =  PurchaseStorage.objects.get(id=storage_id,status__in=(pcfg.PURCHASE_APPROVAL,pcfg.PURCHASE_DRAFT))
                        storages.append(storage)
            else:
                raise Exception(u'付款类型错误') 
            
            purchase_payment = PurchasePayment.objects.create(
                                                          pay_type   = paytype,
                                                          apply_time = datetime.datetime.now(),
                                                          payment    = payment,
                                                          applier    = request.user.username,
                                                          status     = pcfg.PP_WAIT_APPLY,
                                                          extra_info = memo)
            
            log_action(request.user.id,purchase_payment,CHANGE,u'创建采购付款单')
            
            if paytype == pcfg.PC_PREPAID_TYPE:
                purchase_payment.apply_for_prepay(purchase,payment)
                
            elif paytype == pcfg.PC_POD_TYPE:
                purchase_payment.apply_for_podpay(storages[0],payment)
                
            elif paytype == pcfg.PC_COD_TYPE:
                total_unpay_fee = 0
                for storage in storages:
                    total_unpay_fee += storage.total_unpay_fee 
                
                if total_unpay_fee <= 0:
                    raise Exception(u'没有找到待付款项')
                
                for storage in storages:
                    purchase_payment.apply_for_codpay(storage,(storage.total_unpay_fee/total_unpay_fee)*payment)
            else :
                purchase_payment.apply_for_otherpay(purchase,storages,payment)
        except Exception,exc:
            logger.error(exc.message,exc_info=True)
            if purchase_payment:
                purchase_payment.invalid()
                log_action(request.user.id,purchase_payment,CHANGE,u'创建采购付款单出错:%s'%exc.message)
                
            return {'purchases':waitpay_purchases,'storages':waitpay_storages,'error_msg':exc.message}
        else:
            return HttpResponseRedirect("/purchases/payment/distribute/%d/"%purchase_payment.id)
            
            
class PaymentDistributeView(ModelView):
    """ 付款单金额分配 """
    
    def get(self, request, id, *args, **kwargs):
        
        try:
            purchase_payment = PurchasePayment.objects.get(id=id)
        except PruchasePayment.DoesNotExist:
            return u'采购付款单未找到'
        
        perms = {'can_confirm_payment':perm.has_payment_confirm_permission(request.user) 
                 and purchase_payment.status==pcfg.PP_WAIT_PAYMENT,
                'can_apply_payment':purchase_payment.status in (pcfg.PP_WAIT_APPLY,pcfg.PP_WAIT_PAYMENT)}
        
        return {'purchase_payment':purchase_payment.json,'perms':perms}
        
        
    def post(self, request, id, *args, **kwargs):
        
        try:
            purchase_payment = PurchasePayment.objects.get(id=id,status__in=(pcfg.PP_WAIT_APPLY,pcfg.PP_WAIT_PAYMENT))
        except PruchasePayment.DoesNotExist:
            raise Http404
        
        try:
            content  = request.REQUEST.copy()
            
            pmt_dict = self.parse_params(content)
            
            self.valid_params(pmt_dict,purchase_payment.payment)
            
            self.fill_payment(pmt_dict) 
        except Exception,exc:
            
            perms = {'can_confirm_payment':perm.has_payment_confirm_permission(request.user) \
                     and purchase_payment.status==pcfg.PP_WAIT_PAYMENT,
                     'can_apply_payment':purchase_payment.status in (pcfg.PP_WAIT_APPLY,pcfg.PP_WAIT_PAYMENT)}
            return {'purchase_payment':purchase_payment.json,'error_msg':exc.message,'perms':perms}
        
        purchase_payment.status = pcfg.PP_WAIT_PAYMENT
        purchase_payment.save()
        
        log_action(request.user.id,purchase_payment,CHANGE,u'申请付款')
        
        messages.add_message(request, messages.INFO, u'付款保存成功,并已申请付款')
        
        return HttpResponseRedirect('/admin/purchases/purchasepayment/?q=%s'%id)
        
        
    def parse_params(self,content):
        
        try:
            r  = re.compile('^(?P<name>\w+)-(?P<id>[0-9]+)(-(?P<item_id>[0-9]+))?$')
            
            pmt_dict = {"purchase":{},"storages":{}}
            
            for k,v in content.iteritems():
                m = r.match(k)
                if not m :
                    continue
                
                v = round(float(v),2)
                d = m.groupdict()
                if d['name'] == 'purchase':
                    handle      = pmt_dict['purchase'] 
                    id           = d['id']
                    item_id      = d['item_id']
                    
                    if not handle.has_key('payment_items'):
                        handle['payment_items'] = []
                    
                    if item_id:
                        handle['payment_items'].append((item_id,v))
                    else:
                        handle['id'] = id
                        handle['payment'] = v
                        
                elif d['name'] == 'storage':
                    handle       = pmt_dict['storages'] 
                    id           = d['id']
                    item_id      = d['item_id']
                    
                    if handle.has_key(id):
                        storage_dict = handle[id]
                    else:
                        handle[id] = storage_dict = {'payment_items':[]}
                        
                    if not item_id:
                        storage_dict['id'] = id
                        storage_dict['payment'] = v
                        continue
                        
                    storage_dict['payment_items'].append((item_id,v))
        except:
            raise Exception(u'参数格式不对')
        return pmt_dict
    
    def valid_params(self,d,global_payment):
        
        total_payment = 0
        if d['purchase']:
            purchase = d['purchase']
            payment  = purchase['payment']
            item_payment = 0.0
            for item in purchase['payment_items']:
                item_payment += item[1]
            
            if round(payment,1) != round(item_payment,1):
                raise Exception(u'采购项目分配金额与采购单分配总金额不等')
            
            total_payment = payment
        else:
            storages = d['storages']
            for k,storage in storages.iteritems():
                item_payment = 0.0
                payment  = storage['payment']
                
                for item in storage['payment_items']:
                    item_payment += item[1]
                    
                if round(payment,1) != round(item_payment,1):
                    raise Exception(u'入库项目分配金额与入库单分配总金额不等')
                
                total_payment += item_payment
                
        if round(global_payment,1) != round(total_payment,1):
            raise Exception(u'总付款金额与分配金额不等')
        
    def fill_payment(self,pmt_dict):
        
        if pmt_dict['purchase']:
            for item in pmt_dict['purchase']['payment_items']:
                payment_item = PurchasePaymentItem.objects.get(id=item[0])
                payment_item.payment = item[1]
                payment_item.save()
                
        else:
            for k,storage in pmt_dict['storages'].iteritems():
                for item in storage['payment_items']:
                    payment_item = PurchasePaymentItem.objects.get(id=item[0])
                    payment_item.payment = item[1]
                    payment_item.save()        
        
@csrf_exempt        
def confirm_payment_amount(request):
    
    content    = request.REQUEST
    id       = content.get('id','none')
    pay_bank = content.get('pay_bank')
    pay_no   = content.get('pay_no')
    pay_time = content.get('pay_time')  
    try:
        purchase_payment = PurchasePayment.objects.get(id=id,status=pcfg.PP_WAIT_PAYMENT)
    except PurchasePayment.DoesNotExist:
        raise Http404
                  
    if not perm.has_payment_confirm_permission(request.user):
        raise Http404
    
    purchase_payment.pay_bank = pay_bank
    purchase_payment.pay_no   = pay_no
    purchase_payment.pay_time = pay_time or datetime.datetime.now()
        
    purchase_payment.confirm_pay(request.user.username)
    
    messages.add_message(request, messages.INFO, u'成功确认付款')
    log_action(request.user.id,purchase_payment,CHANGE,u'确认付款')
    
    return HttpResponseRedirect('/admin/purchases/purchasepayment/?q=%s'%id)
    
    