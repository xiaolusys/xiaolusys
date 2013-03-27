#-*- coding:utf8 -*-
import datetime
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse,HttpResponseNotFound
from  django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from djangorestframework.serializer import Serializer
from djangorestframework.utils import as_tuple
from djangorestframework import status
from djangorestframework.response import Response,ErrorResponse
from djangorestframework.mixins import CreateModelMixin
from shopback import paramconfig as pcfg
from shopback.base.views import ModelView,ListOrCreateModelView,ListModelView
from shopback.items.models import Item,Product,ProductSku
from shopback.users.models import User
from shopback.items.tasks import updateUserItemsTask
from shopapp.syncnum.tasks import updateItemNum
from auth import apis
import logging

logger = logging.getLogger('items.handler')

def update_user_items(request):

    content = request.REQUEST
    user_id = content.get('user_id') or request.user.get_profile().visitor_id

    update_nums = updateUserItemsTask(user_id)


    response = {'update_nums':update_nums}

    return HttpResponse(json.dumps(response),mimetype='application/json')


@csrf_exempt
def update_product_stock(request):

    content  = request.REQUEST
    outer_id = content.get('outer_id')
    sku_id   = content.get('sku_id')
    num      = content.get('num')
    mode     = content.get('mode') #0增量，1全量
    
    prod     = None
    prod_sku = None
    num ,mode = int(num),int(mode)
    if sku_id:
        try:
            prod_sku = ProductSku.objects.get(id=sku_id)
        except:
            response = {'code':1,'response_error':u'商品规格未找到'}
            return HttpResponse(json.dumps(response),mimetype='application/json')
        else:
            if mode == 0:
                prod_sku.update_quantity_incremental(num,reverse=True)
            else:
                prod_sku.quantity=num
                prod_sku.save()
            prod = prod_sku.product
    else:       
        try:
            prod = Product.objects.get(outer_id=outer_id)
        except:
            response = {'code':1,'response_error':u'商品未找到'}
            return HttpResponse(json.dumps(response),mimetype='application/json')
        else:
            if mode == 0:
                prod.update_collect_num_incremental(num,reverse=True)
            else:
                prod.collect_num = num
                prod.save()
         
    response = {
                'outer_id':prod.outer_id,
                'collect_num':prod.collect_num,
                'is_stock_warn':prod.is_stock_warn,
                'is_warning':prod.is_warning,
                }
    if prod_sku:
        quantity = prod_sku.quantity
        print 'quantity:',str(quantity)
        response['sku'] = {
                        'id':prod_sku.id,
                        'outer_id':prod_sku.outer_id,
                        'quantity':prod_sku.quantity,
                        'is_stock_warn':prod_sku.is_stock_warn,
                        'is_warning':prod_sku.is_warning,
                        }
    response = {'code':0,'response_content':response}
    return HttpResponse(json.dumps(response),mimetype='application/json')


def update_user_item(request):

    content = request.REQUEST
    user_id = content.get('user_id')
    num_iid = content.get('num_iid')

    try:
        profile = User.objects.get(visitor_id=user_id)
    except User.DoesNotExist:
        return HttpResponse(json.dumps({'code':0,'error_reponse':'user_id is not correct'}))

    try:
        Item.objects.get(num_iid=None)
    except Item.DoesNotExist:
        try:
            response = apis.taobao_item_get(num_iid=num_iid,tb_user_id=profile.visitor_id)
            item_dict = response['item_get_response']['item']
            item = Item.save_item_through_dict(user_id,item_dict)

        except Exception,e:
            return HttpResponse(json.dumps({'code':0,'error_reponse':'update item fail.'}))

    item_dict = {'code':1,'reponse':Serializer().serialize(item)}
    return  HttpResponse(json.dumps(item_dict,cls=DjangoJSONEncoder))


class ProductListView(ListOrCreateModelView):
    """ docstring for ProductListView """
    queryset = None
    
    def get(self, request, *args, **kwargs):
        #获取库存商品列表
        model = self.resource.model

        queryset = self.get_queryset() if self.get_queryset() is not None else model.objects.all()

        if hasattr(self, 'resource'):
            ordering = getattr(self.resource, 'ordering', None)
        else:
            ordering = None

        kwargs.update({'status':pcfg.NORMAL})

        if ordering:
            args = as_tuple(ordering)
            queryset = queryset.order_by(*args)
            
        queryset = queryset.filter(**kwargs)

        return queryset
 
    
    def get_queryset(self):
        return self.queryset
    

class ProductItemView(ListModelView):
    """ docstring for ProductListView """
    queryset = None
    
    def get(self, request, *args, **kwargs):
        #获取某outer_id对应的商品，以及同步商品库存
        outer_id = kwargs.get('outer_id','')
        sync_stock = request.REQUEST.get('sync_stock','no')
        model = self.resource.model
        
        update_time  = datetime.datetime.now()
        if sync_stock == 'yes':
            items = model.objects.filter(outer_id=outer_id,approve_status=pcfg.ONSALE_STATUS)
            for item in items:
                updateItemNum(item.num_iid,update_time)
        
        queryset = self.get_queryset() if self.get_queryset() is not None else model.objects.all()

        if hasattr(self, 'resource'):
            ordering = getattr(self.resource, 'ordering', None)
        else:
            ordering = None

        if ordering:
            args = as_tuple(ordering)
            queryset = queryset.order_by(*args)
            
        item_dict = {}
        items = queryset.filter(**kwargs)
        item_dict['itemobjs'] =  Serializer().serialize(items)
        item_dict['layer_table'] = render_to_string('items/itemstable.html', { 'object':item_dict['itemobjs']})    
        
        return item_dict
    
    def post(self, request, *args, **kwargs):
        #删除product或productsku
        outer_id = kwargs.get('outer_id')
        outer_sku_id = request.REQUEST.get('outer_sku_id',None)
        if outer_sku_id:
            row = ProductSku.objects.filter(product=outer_id,outer_id=outer_sku_id).update(status=pcfg.DELETE)
        else:
            row = Product.objects.filter(outer_id=outer_id).update(status=pcfg.DELETE)
        
        return {'updates_num':row}
    
    def get_queryset(self):
        return self.queryset


class ProductModifyView(ListModelView):
    """ docstring for ProductListView """
    
    def get(self, request, *args, **kwargs):
        #取消库存警告
        outer_id = kwargs.get('outer_id')
        outer_sku_id = request.REQUEST.get('outer_sku_id',None)
        if outer_sku_id :
            row = ProductSku.objects.filter(product=outer_id,outer_id=outer_sku_id).update(is_assign=True)
        else:
            row = Product.objects.filter(outer_id=outer_id).update(is_assign=True)
            
        return {'updates_num':row}
    
    
    
class ProductUpdateView(ModelView):
    """ docstring for ProductListView """
    
    def get(self, request, *args, **kwargs):
        
        outer_id = kwargs.get('outer_id',None)
        try:
            instance = Product.objects.get(outer_id=outer_id)
        except:
            return HttpResponseNotFound(u'商品未找到')
        
        ins_dict = {
                    'id':instance.id,
                    'outer_id':instance.outer_id,
                    'name':instance.name,
                    'collect_num':instance.collect_num,
                    'remain_num':instance.remain_num,
                    'sync_stock':instance.sync_stock,
                    'is_split':instance.is_split,
                    'is_match':instance.is_match,
                    'is_assign':instance.is_assign,
                    'is_stock_warn':instance.is_stock_warn,
                    'is_warning':instance.is_warning,
                    }
        
        sku_list = []
        ins_dict['pskus'] = sku_list
        for sku in instance.pskus:
            sku_dict = {
                        'id':sku.id,
                        'outer_id':sku.outer_id,
                        'properties_name':sku.properties_name,
                        'properties_alias':sku.properties_alias,
                        'quantity':sku.quantity,
                        'warn_num':sku.warn_num,
                        'remain_num':sku.remain_num,
                        'sync_stock':sku.sync_stock,
                        'is_split':sku.is_split,
                        'is_match':sku.is_match,
                        'status':sku.status,
                        'is_stock_warn':sku.is_stock_warn,
                        'is_assign':sku.is_assign,
                        'is_warning':sku.is_warning,
                        }
            sku_list.append(sku_dict)
        
        return ins_dict
    
    
    def post(self, request, *args, **kwargs):
        #修改库存商品信息
        
        
        
            
        return 0
   
   
class ProductSkuCreateView(ModelView):
    """ docstring for ProductSkuCreateView """
    
    def get(self, request, *args, **kwargs):
        
        prod_sku_id = request.REQUEST.get('prod_sku_id',None)
        try:
            instance = ProductSku.objects.get(id=prod_sku_id)
        except:
            raise ErrorResponse(status.HTTP_404_NOT_FOUND)
        
        return instance
    
    
    def post(self, request, *args, **kwargs):
        #创建库存产品属性信息
    
            
        return 0
    
    
class ProductSkuInstanceView(ModelView):
    """ docstring for ProductSkuInstanceView """
    
    def get(self, request, sku_id, *args, **kwargs):

        try:
            instance = ProductSku.objects.get(id=sku_id)
        except:
            raise ErrorResponse(status.HTTP_404_NOT_FOUND)
        
        product_sku = self._resource.filter_response(instance)
        product_sku['layer_table'] = render_to_string('items/productskutable.html', { 'object':instance}) 
        
        return product_sku
    
    
    def post(self, request, *args, **kwargs):
        #修改库存商品信息
    
        return 0






