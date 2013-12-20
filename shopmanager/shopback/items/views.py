#-*- coding:utf8 -*-
import re
import datetime
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse,HttpResponseNotFound
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.db.models import Q,Sum
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from djangorestframework.serializer import Serializer
from djangorestframework.utils import as_tuple
from djangorestframework import status
from djangorestframework.response import Response,ErrorResponse
from djangorestframework.mixins import CreateModelMixin
from shopback import paramconfig as pcfg
from shopback.base.views import ModelView,ListOrCreateModelView,ListModelView
from shopback.items.models import Item,SkuProperty,Product,ProductSku,ProductLocation
from shopback.archives.models import DepositeDistrict
from shopback.users.models import User
from shopback.items.tasks import updateUserItemsTask,updateItemNum
from shopback.base.authentication import login_required_ajax
from auth import apis
from common.utils  import update_model_fields
from shopback.base import log_action, ADDITION, CHANGE
import logging

DISTRICT_REGEX = '^(?P<pno>[a-zA-Z0-9]+)-(?P<dno>[0-9]+)$'
ASSRIGN_PARAMS_REGEX = '^(?P<num_iid>[0-9]+)-(?P<sku_id>[0-9]+)?$'
logger = logging.getLogger('items.handler')

def update_user_items(request):

    content = request.REQUEST
    user_id = content.get('user_id') or request.user.get_profile().visitor_id

    update_nums = updateUserItemsTask(user_id)

    response = {'update_nums':update_nums}

    return HttpResponse(json.dumps(response),mimetype='application/json')


@csrf_exempt
@login_required_ajax
def update_product_stock(request):

    content  = request.REQUEST
    outer_id = content.get('outer_id')
    sku_id   = content.get('sku_id')
    outer_sku_id   = content.get('outer_sku_id')
    num      = content.get('num')
    remain_num = content.get('remain_num',0)
    mode     = content.get('mode',0) #0增量，1全量
    
    prod     = None
    prod_sku = None
    num ,mode ,remain_num = int(num),int(mode),int(remain_num)
    if sku_id or outer_sku_id:
        try:
            if sku_id:
                prod_sku = ProductSku.objects.get(id=sku_id)
            else:
                prod_sku = ProductSku.objects.get(product__outer_id=outer_id,outer_id=outer_sku_id)
        except:
            response = {'code':1,'response_error':u'商品规格未找到'}
            return HttpResponse(json.dumps(response),mimetype='application/json')
        else:
            prod_sku.update_quantity(num,full_update=mode,dec_update=False)
            
            prod_sku.remain_num = remain_num
            update_model_fields(prod_sku,update_fields=['remain_num'])
            
            prod = prod_sku.product
        
    else:       
        try:
            prod = Product.objects.get(outer_id=outer_id)
        except:
            response = {'code':1,'response_error':u'商品未找到'}
            return HttpResponse(json.dumps(response),mimetype='application/json')
        else:
            
            prod.update_collect_num(num,full_update=mode)
            
            prod.remain_num = remain_num
            update_model_fields(prod,update_fields=['remain_num'])
                
    log_action(request.user.id,prod,CHANGE,u'更新商品库存及预留库存：%s-%s,%d,%d'%(outer_id,sku_id or outer_sku_id,num,remain_num))
    
    response = {
                'outer_id':prod.outer_id,
                'collect_num':prod.collect_num,
                'remain_num':prod.remain_num,
                'is_stock_warn':prod.is_stock_warn,
                'is_warning':prod.is_warning,
                }
    if prod_sku:
        quantity = prod_sku.quantity
        response['sku'] = {
                        'id':prod_sku.id,
                        'outer_id':prod_sku.outer_id,
                        'quantity':prod_sku.quantity,
                        'remain_num':prod_sku.remain_num,
                        'is_stock_warn':prod_sku.is_stock_warn,
                        'is_warning':prod_sku.is_warning,
                        }
    response = {'code':0,'response_content':response}
    return HttpResponse(json.dumps(response),mimetype='application/json')

#######################################################################################33

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
    """ docstring for ProductItemView """
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
        
        outer_id = kwargs.get('outer_id','None')
        try:
            instance = Product.objects.get(outer_id=outer_id)
        except:
            return HttpResponseNotFound(u'商品未找到')
        
        ins_dict = instance.json
        
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


class ProductSearchView(ModelView):
    """ 根据商品编码，名称查询商品 """
    
    def get(self, request, *args, **kwargs):
        
        q  = request.GET.get('q')
        if not q:
            return '没有输入查询关键字'.decode('utf8')
        products = Product.objects.filter(Q(outer_id=q)|Q(name__contains=q),status__in=(pcfg.NORMAL,pcfg.REMAIN))
        
        prod_list = [(prod.outer_id,prod.pic_path,prod.name,prod.cost,prod.collect_num,prod.created,[(sku.outer_id,sku.name,sku.quantity) for sku in 
                    prod.pskus.order_by('-created')]) for prod in products]
        
        return prod_list

    def post(self, request, *args, **kwargs):
        #修改库存商品信息
    
        return 0
    
    
class ProductBarCodeView(ModelView):
    """ docstring for ProductBarCodeView """

    
    def get(self, request, *args, **kwargs):
        #获取库存商品列表

        queryset = Product.objects.filter(status__in=(pcfg.NORMAL,pcfg.REMAIN))
        
        return [p.json for p in queryset]
 
    def post(self, request, *args, **kwargs):
        
        content       = request.REQUEST
        outer_id      = content.get('outer_id') or None
        outer_sku_id  = content.get('outer_sku_id')
        barcode       = content.get('barcode') or ''
        
        product     = None
        product_sku = None
        try:
            product   =  Product.objects.get(outer_id=outer_id)
        except Product.DoesNotExist:
            return u'未找到商品'
            
        if outer_sku_id :
            try:
                product_sku   =  ProductSku.objects.get(outer_id=outer_sku_id,product=product)
            except ProductSku.DoesNotExist:
                return u'未找到商品规格' 
            
            product_sku.barcode = barcode.strip()
            product_sku.save()
        else:
            product.barcode  =  barcode.strip()
            product.save()
        
        return {'barcode':product_sku and product_sku.BARCODE or product.BARCODE}   
        
          

############################################ 产品区位操作 #######################################
class ProductDistrictView(ModelView):
    """ 根据商品编码，名称查询商品 """
    
    def get(self, request, id,*args, **kwargs):
        
        content = request.REQUEST
        try:
            product = Product.objects.get(id=id)
        except:
            return u'商品未找到'
        
        return {'product':product.json}
        
    def post(self, request, id,*args, **kwargs):
        
        content   = request.REQUEST
        outer_id  = content.get('outer_id') or None
        outer_sku_id = content.get('outer_sku_id') or None
        district  = content.get('district')
        
        r  = re.compile(DISTRICT_REGEX)
        m  = r.match(district)
        if not m:
            return u'标签不合规则'
        
        tag_dict = m.groupdict()
        pno = tag_dict.get('pno')
        dno = tag_dict.get('dno')
        district = DepositeDistrict.objects.get(parent_no=pno,district_no=dno)
        
        product   = Product.objects.get(outer_id=outer_id)
        if outer_sku_id:
            ProductSku.objects.get(outer_id=outer_sku_id,product=product)
        
        location,state = ProductLocation.objects.get_or_create(outer_id=outer_id,outer_sku_id=outer_sku_id,district=district)
        return {'outer_id':location.outer_id,'outer_sku_id':location.outer_sku_id,'district':district}
        
        
@csrf_exempt
@login_required_ajax            
def delete_product_district(request):
    
    content      = request.REQUEST
    outer_id     = content.get('outer_id') or None
    outer_sku_id = content.get('outer_sku_id') or None
    district     = content.get('district')

    r  = re.compile(DISTRICT_REGEX)
    m  = r.match(district)
    if not m:
        ret = {'code':1,'error_response':u'标签不合规则'}
        return HttpResponse(json.dumps(ret),mimetype="application/json")
        
    tag_dict = m.groupdict()
    pno = tag_dict.get('pno')
    dno = tag_dict.get('dno')
    district = DepositeDistrict.objects.get(parent_no=pno,district_no=dno)
    
    try:
        location = ProductLocation.objects.get(outer_id=outer_id,outer_sku_id=outer_sku_id,district=district)
        location.delete()
    except Exception,exc:
        logger.error(exc.message,exc_info=True)
        ret = {'code':1,'error_response':u'未找到删除项'}
        return HttpResponse(json.dumps(ret),mimetype="application/json")
    
    ret = {'code':0,'response_content':'success'}
    return HttpResponse(json.dumps(ret),mimetype="application/json")


@csrf_exempt
@login_required_ajax            
def deposite_district_query(request):
        
    content = request.REQUEST
    q       = content.get('term')
    if not q:
        ret = {'code':1,'error_response':u'查询内容不能为空'}
        return HttpResponse(json.dumps(ret),mimetype="application/json")

    districts = DepositeDistrict.objects.filter(parent_no__icontains=q)

    ret = [{'id':str(d),'label':str(d),'value':str(d)} for d in districts]
    
    return HttpResponse(json.dumps(ret),mimetype="application/json")
    
    
##################################### 警告库存商品规格管理 ##################################

class ProductOrSkuStatusMdView(ModelView):
    """ 库存警告商品管理 """
    
    def post(self, request,*args, **kwargs):
        
        content      = request.REQUEST
        outer_id     = content.get('outer_id')
        outer_sku_id = content.get('outer_sku_id')
        is_delete    = content.get('is_delete') == 'yes'
        is_remain    = content.get('is_remain') == 'yes'
        
        status       = (is_delete and pcfg.DELETE) or (is_remain and pcfg.REMAIN) or pcfg.NORMAL
        if outer_sku_id:
            row = ProductSku.objects.filter(product=outer_id,outer_id=outer_sku_id).update(status=status)
        else:
            row = Product.objects.filter(outer_id=outer_id).update(status=status)
        
        return {'updates_num':row}

class ProductWarnMgrView(ModelView):
    """ 库存警告商品管理 """
    
    def get(self, request, *args, **kwargs):
        
        pskus = ProductSku.objects.filter(product__status=pcfg.NORMAL,status=pcfg.NORMAL,is_assign=False)\
            .extra(where=["quantity<=shop_items_productsku.remain_num+shop_items_productsku.wait_post_num"])
        
        return {'warn_skus':pskus}
        
    def post(self, request,*args, **kwargs):
        
        pass
    
class ProductNumAssignView(ModelView):
    """ docstring for ProductNumAssignView """
    
    def get(self, request, *args, **kwargs):
        #获取某outer_id对应的商品，以及同步商品库存
        
        content       = request.REQUEST
        outer_id      = content.get('outer_id')
        outer_sku_id  = content.get('outer_sku_id')
        
        real_num  = 0
        lday_num  = 0
        product = Product.objects.get(outer_id=outer_id)
        if outer_sku_id:
            try:
                product_sku = ProductSku.objects.get(outer_id=outer_)
            except:
                pass
            else:
                real_num = product_sku.quantity - product_sku.wait_post_num
                lday_num  = product_sku.warn_num
        else:
            real_num = product.collect_num - product.wait_post_num
            lday_num  = product.warn_num
            
        items_dict_list    = []
        items   = Item.objects.filter(outer_id=outer_id,status=True)
        for item in items:
            
            #item = Item.get_or_create(item.user.visitor_id,item.num_iid,force_update=True)
            item_dict  = {}
            sku_dict   = {}
            item_dict['num_iid']    = item.num_iid
            item_dict['outer_id']   = item.outer_id
            item_dict['seller_nick']   = item.user.nick
            item_dict['sync_stock']    = item.sync_stock and 1 or 0
            item_dict['approve_status']     = item.approve_status
            item_dict['with_hold_quantity'] = item.with_hold_quantity
            item_dict['has_showcase']       = item.has_showcase and 1 or 0
            item_dict['num']        = item.num
            item_dict['title']      = item.title
            item_dict['pic_url']    = item.pic_url
            item_dict['detail_url'] = item.detail_url
            try:
                spty = SkuProperty.objects.get(num_iid=item.num_iid,outer_id=outer_sku_id,status='normal')
            except:
                pass
            else:
                sku_dict['sku_id']     = spty.sku_id
                sku_dict['outer_id']   = spty.outer_id
                sku_dict['properties_name']    = spty.properties_name
                sku_dict['with_hold_quantity'] = spty.with_hold_quantity
                sku_dict['quantity']   = spty.quantity
            item_dict['sku']  = sku_dict
                
            items_dict_list.append(item_dict)
            
        return {'items_list':items_dict_list,
                'outer_id':outer_id,
                'outer_sku_id':outer_sku_id,
                'real_num':real_num,
                'lday_num':lday_num}
    
    def post(self, request, *args, **kwargs):
        #删除product或productsku
        
        content   = request.REQUEST
        outer_id  =  content.get('assign_outer_id')
        outer_sku_id  =  content.get('assign_outer_sku_id')
        
        try:
            item_list = self.parse_params(content)
            
            self.valid_params(item_list,outer_id,outer_sku_id)
            
            self.assign_num_action(item_list)
        except Exception,exc:
            logger.error(exc.message,exc_info=True)
            return exc.message
        
        if outer_sku_id :
            row = ProductSku.objects.filter(outer_id=outer_sku_id,product__outer_id=outer_id).update(is_assign=True)
        else:
            row = Product.objects.filter(outer_id=outer_id).update(is_assign=True)
            
        return {'success':row}
    
    def parse_params(self,content):
        
        items_list = []
        try:
            r  = re.compile(ASSRIGN_PARAMS_REGEX)
            
            for k,v in content.iteritems():
                m = r.match(k)
                if not m :
                    continue
                
                d = m.groupdict()
                items_list.append((d['num_iid'],d['sku_id'],int(v)))
                    
        except:
            raise Exception(u'参数格式不对')
        return items_list
    
    def valid_params(self,item_list,outer_id,outer_sku_id):
        
        product     = None
        product_sku = None
        if outer_sku_id:
            product_sku = ProductSku.objects.get(product__outer_id=outer_id,outer_id=outer_sku_id)
        
        product = Product.objects.get(outer_id=outer_id)
        
        real_num = product_sku and product_sku.realnum or product.realnum
        assign_num   = 0
        for item in item_list:
            if item[2] != 0 and item[1] and not product_sku:
                raise Exception(u'该商品有系统规格跟线上规格不符')
            assign_num += item[2]
        
        if assign_num > real_num:
            raise Exception(u'库存分配超出实际库存')
        
        
    def assign_num_action(self,item_list):
        
        for item in item_list:
            
            im = Item.objects.get(num_iid=item[0])
            hold_num = im.with_hold_quantity
            if item[1]:
                hold_num = SkuProperty.objects.get(num_iid=item[0],sku_id=item[1]).with_hold_quantity
            
            if item[2] < hold_num:    
                raise Exception(u'分配库存小于线上拍下待付款数')
            
            response = apis.taobao_item_quantity_update\
                        (num_iid=item[0],quantity=item[2],sku_id=item[1],tb_user_id=im.user.visitor_id)   
                            
               
            
            
                        