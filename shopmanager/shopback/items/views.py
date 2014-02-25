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
from shopback.items.models import Item,SkuProperty,Product,ProductSku,ProductLocation,APPROVE_STATUS,ONLINE_PRODUCT_STATUS
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
logger = logging.getLogger('django.request')

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
    product_id = content.get('product_id')
    sku_id   = content.get('sku_id')
    outer_sku_id   = content.get('outer_sku_id')
    num      = content.get('num')
    remain_num = content.get('remain_num','')
    reduce_num = content.get('reduce_num',0)
    mode     = content.get('mode',0) #0增量，1全量
    
    if not num :
        return HttpResponse(json.dumps({'code':1,'response_error':u'库存数量不能为空'})
                            ,mimetype='application/json')
    
    prod     = None
    prod_sku = None
    num ,mode ,reduce_num = int(num),int(mode),int(reduce_num)
    try:
        try:
            prod = Product.objects.get(id=product_id)
        except:
            prod = Product.objects.get(outer_id=outer_id)
        
        if sku_id or outer_sku_id:
            if sku_id:
                prod_sku = ProductSku.objects.get(id=sku_id)
            else:
                prod_sku = ProductSku.objects.get(product__outer_id=outer_id,outer_id=outer_sku_id)
            
            prod_sku.update_quantity(num,full_update=mode,dec_update=False)
            prod_sku.update_reduce_num(reduce_num,full_update=mode,dec_update=False)
            prod = prod_sku.product
            
        else:       
            prod.update_collect_num(num,full_update=mode)
            prod.update_reduce_num(reduce_num,full_update=mode,dec_update=False)
        
        if remain_num :  
            if prod_sku:
                prod_sku.remain_num = int(remain_num)
            else:
                prod.remain_num     = int(remain_num)
            update_model_fields(prod_sku or prod,update_fields=['remain_num'])
    except Product.DoesNotExist:
        response = {'code':1,'response_error':u'商品未找到'}
        return HttpResponse(json.dumps(response),mimetype='application/json')
    except ProductSku.DoesNotExist:
        response = {'code':1,'response_error':u'商品规格未找到'}
        return HttpResponse(json.dumps(response),mimetype='application/json')
    except Exception,exc:
        response = {'code':1,'response_error':exc.message}
        return HttpResponse(json.dumps(response),mimetype='application/json')
                
    log_action(request.user.id,prod,CHANGE,u'更新商品库存,%s，编码%s-%s,库存数%d,预留数%s,预减数%d'%
               (mode and u'全量' or u'增量',prod.outer_id,prod_sku and prod_sku.outer_id or sku_id,num,remain_num or '-',reduce_num))
    
    response = {
                'id':prod.id,
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

############################ 库存商品操作 ###############################

class ProductView(ModelView):
    """ docstring for ProductView """
    
    def get(self, request, id, *args, **kwargs):
        
        product = Product.objects.get(id=id)
        
        return product.json


    def post(self, request, id, *args, **kwargs):
        
        try:
            product = Product.objects.get(id=id)
        
            content =  request.REQUEST
            
            fields = ['outer_id','barcode','name','remain_num','weight','cost','std_purchase_price','std_sale_price'
                      ,'agent_price','staff_price','is_split','sync_stock','post_check','is_match','match_reason'
                      ,'buyer_prompt','memo']
            
            check_fields = set(['is_split','sync_stock','post_check','is_match'])
            
            for k,v in content.iteritems():
                if k not in fields:continue
                if k in check_fields:
                    check_fields.remove(k)
                if k in ('wait_post_num','remain_num'):
                    v = int(v)
                setattr(product,k,v)
            
            for k in check_fields:
                setattr(product,k,False)
            
            product.save()
        except Product.DoesNotExist:
            return u'商品未找到'
        except Exception,exc:
            return u'填写信息不规则'
        log_action(request.user.id,product,CHANGE,u'更新商品基本信息')
        
        return product.json
    
        
class ProductSkuView(ModelView):
    """ docstring for ProductSkuView """
    
    def get(self, request, pid, sku_id, *args, **kwargs):

        try:
            instance = ProductSku.objects.get(id=sku_id)
        except:
            raise ErrorResponse(status.HTTP_404_NOT_FOUND)
        
        product_sku = self._resource.filter_response(instance)
        product_sku['layer_table'] = render_to_string('items/productskutable.html', { 'object':instance}) 
        
        return product_sku
    
    
    def post(self, request,pid, sku_id, *args, **kwargs):
        #修改库存商品信息
        try:
            product_sku = ProductSku.objects.get(product=pid,id=sku_id)
        
            content = request.REQUEST
            update_check = content.get('update_check') 
            fields = ['outer_id','properties_alias','wait_post_num','remain_num','warn_num'
                      ,'cost','std_sale_price','agent_price','staff_price','match_reason'
                      ,'barcode','buyer_prompt','memo']
            
            check_fields = set(['sync_stock','post_check','is_match'])
            if update_check:
                fields.extend(list(check_fields))
                
            for k,v in content.iteritems():
                if k not in fields:
                    continue
                if k in check_fields:
                    check_fields.remove(k)
                if k in ('wait_post_num','remain_num','warn_num'):
                    v = int(v)
                setattr(product_sku,k,v) 
            
            if update_check:
                for k in check_fields:
                    setattr(product_sku,k,False)    
            
            product_sku.save()
        
        except ProductSku.DoesNotExist:
            return '未找到商品属性'
        except Exception,exc:
            return u'填写信息不规则'
        
        log_action(request.user.id,product_sku.product,CHANGE,u'更新商品规格信息:%s'%unicode(product_sku))
        
        return product_sku.json
    
    
        
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
            if outer_sku_id :
                product_sku   =  ProductSku.objects.get(outer_id=outer_sku_id,product=product)
                
                product_sku.barcode = barcode.strip()
                product_sku.save()
            else:
                product.barcode  =  barcode.strip()
                product.save()
        
        except Product.DoesNotExist:
            return u'未找到商品'
        except ProductSku.DoesNotExist:
            return u'未找到商品规格' 
        except Exception,exc:
            return exc.message
        
        log_action(request.user.id,product,CHANGE,u'更新商品条码:(%s-%s,%s)'
                   %(outer_id or '',outer_sku_id or '',barcode))
        
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
        
        log_action(request.user.id,product,CHANGE,u'更新商品库位:(%s-%s,%s)'%(outer_id or '',outer_sku_id or '',district))
        
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
    
    log_action(request.user.id,Product.objects.get(outer_id=outer_id),CHANGE,
               u'删除商品库位:(%s-%s,%s)'%(outer_id or '',outer_sku_id or '',district))
    
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
        product_id   = content.get('product_id')
        sku_id       = content.get('sku_id')
        is_delete    = content.get('is_delete') == 'true'
        is_remain    = content.get('is_remain') == 'true'
        
        status       = (is_delete and pcfg.DELETE) or (is_remain and pcfg.REMAIN) or pcfg.NORMAL
        
        queryset     = ProductSku.objects.all()
        if product_id:
            queryset = queryset.filter(product__id=product_id)
        else :
            queryset = queryset.filter(product__outer_id=outer_id)
            
        if sku_id: 
            queryset = queryset.filter(id=sku_id)
            
        if outer_sku_id:
            queryset = queryset.filter(outer_id=outer_sku_id)
            
        row = queryset.update(status=status)
        
        log_action(request.user.id,queryset[0].product,CHANGE,
                   u'更改规格库存状态:%s,%s'%(outer_sku_id or sku_id,dict(ONLINE_PRODUCT_STATUS).get(status)))
        
        return {'updates_num':row}

class ProductWarnMgrView(ModelView):
    """ 库存警告商品管理 """
    
    def get(self, request, *args, **kwargs):
        
        pskus = ProductSku.objects.filter(product__status=pcfg.NORMAL,status=pcfg.NORMAL,is_assign=False)\
            .extra(where=["(quantity<=shop_items_productsku.remain_num+shop_items_productsku.wait_post_num "+
            "OR quantity<=shop_items_productsku.remain_num)"])
        
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
        product_sku = None
        if outer_sku_id:
            try:
                product_sku = ProductSku.objects.get(product__outer_id=outer_id,outer_id=outer_sku_id)
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
            if outer_sku_id:
                try:
                    spty = SkuProperty.objects.get(num_iid=item.num_iid,outer_id=outer_sku_id,status=pcfg.NORMAL)
                except:
                    continue
                else:
                    sku_dict['sku_id']     = spty.sku_id
                    sku_dict['outer_id']   = spty.outer_id
                    sku_dict['properties_name']    = product_sku.properties_name
                    sku_dict['with_hold_quantity'] = spty.with_hold_quantity
                    sku_dict['quantity']   = spty.quantity
            
            item_dict['sku']  = sku_dict
            
            item_dict['num_iid']    = item.num_iid
            item_dict['outer_id']   = item.outer_id
            item_dict['seller_nick']   = item.user.nick
            item_dict['sync_stock']    = item.sync_stock and 1 or 0
            item_dict['approve_status']     = dict(APPROVE_STATUS).get(item.approve_status,'')
            item_dict['with_hold_quantity'] = item.with_hold_quantity
            item_dict['has_showcase']       = item.has_showcase and 1 or 0
            item_dict['num']        = item.num
            item_dict['title']      = item.title
            item_dict['pic_url']    = item.pic_url
            item_dict['detail_url'] = item.detail_url
                
            items_dict_list.append(item_dict)
        
        assign_tpl_string = render_to_string('items/product_assign_warn.html',{'items_list':items_dict_list,
                                            'outer_id':outer_id,
                                            'outer_sku_id':outer_sku_id,
                                            'real_num':real_num,
                                            'lday_num':lday_num})
        
        return {'id':product.id,
               'outer_id':outer_id,
               'name':product.name,
               'barcode':product.barcode,
               'is_match':product.is_match,
               'sync_stock':product.sync_stock,
               'is_assign':product.is_assign,
               'post_check':product.post_check,
               'buyer_prompt':product.buyer_prompt,
               'memo':product.memo,
               'match_reason':product.match_reason,
               'sku':product_sku and product_sku.json or {},
               'assign_template':assign_tpl_string
               }
    
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
        
        product = Product.objects.get(outer_id=outer_id)
        
        if outer_sku_id :
            row = ProductSku.objects.filter(outer_id=outer_sku_id,product__outer_id=outer_id).update(is_assign=True)
        else:
            row = Product.objects.filter(outer_id=outer_id).update(is_assign=True)
        
        log_action(request.user.id,product,CHANGE,u'手动分配商品线上库存')
            
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
            raise Exception('参数格式不对'.decode('utf8'))
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
                raise Exception('该商品有系统规格跟线上规格不符'.decode('utf8'))
            assign_num += item[2]
        
        if assign_num > real_num:
            raise Exception('库存分配超出实际库存'.decode('utf8'))
        
        
    def assign_num_action(self,item_list):
        
        for item in item_list:
            
            im = Item.objects.get(num_iid=item[0])
            hold_num = im.with_hold_quantity
            
            sku = None
            if item[1]:
                sku = SkuProperty.objects.get(num_iid=item[0],sku_id=item[1])
                hold_num = sku.with_hold_quantity
            
            if item[2] < hold_num:    
                raise Exception('分配库存小于线上拍下待付款数'.decode('utf8'))
            
            apis.taobao_item_quantity_update\
                        (num_iid=item[0],quantity=item[2],sku_id=item[1],tb_user_id=im.user.visitor_id)   
            
            if sku:  
                sku.quantity = item[2]
                sku.save()
            else:    
                im.num = item[2]
                im.save()  
                            
               
            
            
                        