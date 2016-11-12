# -*- coding:utf8 -*-.
import json
from django.db.models import Q,F
from django.views.generic import View
from django.http import Http404,HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from .models import PickGroup,WavePick,PickItem,PickPublish
from shopback.trades.models import MergeTrade
from shopback.items.models import Product,ProductSku
from shopback import paramconfig as pcfg

import logging
logger = logging.getLogger('django.request')


class WaveView(View):
    def get(self,request):
        
        groups = PickGroup.objects.all()
        response = render_to_response('create_wave.html', 
                                      {"groups":groups}, 
                                      context_instance=RequestContext(request))
        return response
        
    def post(self,request):
        
        content = request.POST
        group_id = content.get('group_id')
        group    = PickGroup.objects.get(id=group_id)
        wave_id  = group.generateWaveNoByGroup()
                
        response = render_to_response('wave_item_list.html', 
                                      {"wave_id":wave_id}, 
                                      context_instance=RequestContext(request))
        return response
        


class WaveDetailView(View):
    
    def getOrderItems(self,trade_list):
        
        order_items = {}
        for trade in trade_list:
            for order in trade.print_orders:
                
                outer_id     = order.outer_id or str(order.num_iid)
                outer_sku_id = order.outer_sku_id or str(order.sku_id)
                
                products  = Product.objects.filter(outer_id=order.outer_id)
                product   = products.count() > 0 and products[0] or None
                prod_skus = ProductSku.objects.filter(outer_id=order.outer_sku_id,product=product)
                prod_sku  = prod_skus.count() > 0 and prod_skus[0] or None
    
                
                combose_id = outer_id + outer_sku_id                
                order_num      = order.num
                
                if order_items.has_key(combose_id):
                    order_items[combose_id]['num'] += order_num
                    
                else:
                    order_location = (product and product.get_districts_code() or '',
                                      prod_sku and prod_sku.get_districts_code() or '')[prod_sku and 1 or 0] 
                    order_title    = ('%s-%s'%(product and product.name or '', 
                                               prod_sku and prod_sku.name or '')  
                                     or '%s-%s'%(order.title,order.sku_properties_name))
                    order_barcode  = prod_sku and prod_sku.BARCODE or product.BARCODE
                
                    order_items[combose_id]={'num':order_num,
                                           'barcode':order_barcode, 
                                           'location':order_location,
                                           'title': order_title }
        
        order_list = sorted(order_items.items(),key=lambda d:d[1]['location'])
        
        return order_list    
    
    def getOrderItemIdentity(self,order_items):
        
        item_map = {}
        index    = 1
        for item in order_items:
            item_map[item[0]] = index
            item_map[item[0]] = (index,item[1]['barcode'])
            item[1]['identity'] = index
            index += 1
            
        return item_map
            
    
    def get(self,request,wave_id):
        
        wpicks = WavePick.objects.filter(wave_no=wave_id)       
        out_sids = [wp.out_sid for wp in wpicks]
        trades   = MergeTrade.objects.filter(out_sid__in=out_sids,
                                             sys_status__in=(pcfg.WAIT_PREPARE_SEND_STATUS,
                                                             pcfg.WAIT_CHECK_BARCODE_STATUS))
        
        order_items = self.getOrderItems(trades)
        item_identity_map = self.getOrderItemIdentity(order_items)     
        
        PickItem.objects.filter(out_sid__in=out_sids).delete()
        
        for trade in trades:
            out_sid = trade.out_sid
            wpick = WavePick.objects.get(wave_no=wave_id,out_sid=out_sid)
            for order in trade.print_orders:
                pick_item,state = PickItem.objects.get_or_create(
                                            out_sid=out_sid,
                                            outer_id=order.outer_id,
                                            outer_sku_id=order.outer_sku_id,
                                            )
                product_no = order.outer_id+order.outer_sku_id                             
                witem  = item_identity_map.get(product_no)                                    
                
                pick_item.wave_no = wave_id
                pick_item.serial_no = wpick.serial_no
                pick_item.barcode   = witem[1]
                pick_item.title     = order.title,
                pick_item.item_num  = F('item_num') + order.num
                pick_item.identity  = witem[0]
                pick_item.save()
                
        
        response = render_to_response('wave_detail.html', 
                                      {"wave_id":wave_id,"order_items":order_items}, 
                                      context_instance=RequestContext(request))
        return response
        
    def post(self,request,wave_id):
        
        content = request.POST
        out_sid = content.get('out_sid')
        serial_no = content.get('serial_no')
        pgroup = PickGroup.objects.get(wave_no=wave_id)  
        
        isSuccess = True
        errmsg = ''
        try:
            WavePick.objects.create(wave_no=wave_id,out_sid=out_sid,serial_no=serial_no,group_id=pgroup.id)
        except:
            isSuccess = False
            errmsg = u"单号重复"
            
        retparams   = {'isSuccess':isSuccess,'out_sid':out_sid,'serial_no':serial_no,'errmsg':errmsg}
        return HttpResponse(json.dumps(retparams),content_type='application/json')
    
    
from django.db.models import Max

class AllocateView(View):
    
    def genPublishValue(self,pickitems):
        
        char_list = []
        for i in range(1,13):
            char  = "00"
            items = pickitems.filter(serial_no=i)
            if items.count() > 0:
                char = '%02d'%items[0].item_num
            char_list.append(char)
            
        return ''.join(char_list)
    
    def getPickGroupByWaveNo(self,wave_no):
        
        waves = WavePick.objects.filter(wave_no=wave_no)
        if waves.count() > 0:
            return waves[0].group_id
        return None
          
    def getPickItemAllocate(self,wave_id):
        
        pick_items = PickItem.objects.filter(wave_no=wave_id)
        
        identity_list = []
        max_identity = pick_items.aggregate(max_identity=Max('identity')).get('max_identity') or 0
        for i in range(1,max_identity+1):
            
            identity_items = pick_items.filter(identity=i)
            pick_value     = ','.join(['(%d,%d)'%(item.serial_no,item.item_num) for item in identity_items])
            identity_list.append((i,identity_items[0].barcode,pick_value))
            
        return identity_list
          
          
    def get(self, request, wave_id):
        
        pick_alloctates = self.getPickItemAllocate(wave_id)
        group_id = self.getPickGroupByWaveNo(wave_id)
        
        response = render_to_response('allocate_detail.html', 
                                      {"group_id":group_id,
                                       "wave_id":wave_id,
                                       "pick_alloctates":pick_alloctates},
                                      context_instance=RequestContext(request))
        return response
        
    
    def post(self, request, wave_id):
        
        content = request.POST
        barcode = content.get('barcode')
        identity = content.get('identity')
        
        if identity.isdigit() and len(identity)<3:
            
            pick_items = PickItem.objects.filter(identity=identity,
                                                 wave_no=wave_id).order_by('serial_no')
            identity   = identity
            barcode    = ''
        else:
            pick_items = PickItem.objects.filter(barcode=identity,
                                                 wave_no=wave_id).order_by('serial_no')
            identity   = ''
            barcode    = identity
        
        if pick_items.count() > 0:
            if not identity:
                identity = str(pick_items[0].identity)
                
        publish_value  =  self.genPublishValue(pick_items)
        
        group_id = self.getPickGroupByWaveNo(wave_id)
        ppublish,state  = PickPublish.objects.get_or_create(group_id=group_id)
        ppublish.pvalue = publish_value
        ppublish.save()
        
        resparams = {'barcode':barcode,'identity':identity}
        return HttpResponse(json.dumps(resparams),content_type='application/json')
        
        
class PublishView(View):
    
    def get(self, request, group_id):
        
        pick_publish,state = PickPublish.objects.get_or_create(group_id=group_id)
        
        return HttpResponse(pick_publish.pvalue)
        

    
