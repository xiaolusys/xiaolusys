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
from shopback.purchases.models import Purchase,PurchaseItem
from shopback import paramconfig as pcfg
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
        
        purchase_items = []
        for item in purchase.purchase_items.exclude(status=pcfg.PURCHASE_INVALID):
            item_dict = {}
            item_dict['id'] = item.id
            item_dict['supplier_item_id'] = item.supplier_item_id
            item_dict['outer_id']     = item.outer_id
            item_dict['name']         = item.name 
            item_dict['outer_sku_id'] = item.outer_sku_id
            item_dict['properties_name'] = item.properties_name
            item_dict['total_fee']       = item.total_fee
            item_dict['payment']         = item.payment
            item_dict['purchase_num']    = item.purchase_num 
            item_dict['price']           = item.price
            item_dict['std_price']       = item.std_price
            purchase_items.append(item_dict)
        
        purchase_dict = {}
        purchase_dict['id']        = purchase.id
        purchase_dict['origin_no'] = purchase.origin_no
        purchase_dict['supplier_id']      = purchase.supplier.id
        purchase_dict['deposite_id']      = purchase.deposite.id
        purchase_dict['purchase_type_id'] = purchase.purchase_type.id
        purchase_dict['forecast_date']    = purchase.forecast_date
        purchase_dict['post_date']        = purchase.post_date
        purchase_dict['service_date']     = purchase.service_date
        purchase_dict['total_fee']        = purchase.total_fee
        purchase_dict['payment']          = purchase.payment
        purchase_dict['extra_name']       = purchase.extra_name
        purchase_dict['extra_info']       = purchase.extra_info
        purchase_dict['purchase_items']   = purchase_items
            
        params = {}
        params['suppliers']      = Supplier.objects.filter(in_use=True)
        params['deposites']      = Deposite.objects.filter(in_use=True)
        params['purchase_types'] = PurchaseType.objects.filter(in_use=True)
        params['purchase']       = purchase_dict
        
        return params
    


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
        
        purchase_item_dict = {'id':purchase_item.id,
                              'supplier_item_id':purchase_item.supplier_item_id,
                              'outer_id':purchase_item.outer_id,
                              'name':purchase_item.name,
                              'outer_sku_id':purchase_item.outer_sku_id,
                              'properties_name':purchase_item.properties_name,
                              'std_price':purchase_item.std_price,
                              'price':purchase_item.price,
                              'purchase_num':purchase_item.purchase_num,
                              'total_fee':purchase_item.total_fee,
                              }
        return purchase_item_dict

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
        
    rows = PurchaseItem.objects.filter(id=purchase_item_id,purchase=purchase).update(status=pcfg.PURCHASE_INVALID)
  
    if rows == 0:
        return HttpResponse(json.dumps({'code':1,'response_error':'fail'}),mimetype='application/json')
    
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


