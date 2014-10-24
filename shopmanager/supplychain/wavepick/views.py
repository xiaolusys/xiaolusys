# -*- coding:utf8 -*-.
import json
from django.views.generic import View
from django.http import Http404,HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from .models import PickGroup,WavePick,PickItem,PickPublish
from shopback.trades.models import MergeTrade
from shopback.items.models import Product,ProductSku
from shopback import paramconfig as pcfg

import json


class WaveView(View):
    def get(self,request):
        
        groups = PickGroup.objects.all()
        response = render_to_response('create_wave.html', 
                                      {"groups":groups}, 
                                      context_instance=RequestContext(request))
        return response
        
    def post(self,request):
        
        content = request.REQUEST
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
    
                product_id = product and product.id or ''
                sku_id     = prod_sku and prod_sku.id or ''
                
                product_location = product and product.get_districts_code() or ''
                product_sku_location = prod_sku and prod_sku.get_districts_code() or ''
                
                if order_items.has_key(outer_id):
                    order_items[outer_id]['num'] += order.num
                    skus = order_items[outer_id]['skus']
                    if skus.has_key(outer_sku_id):
                        skus[outer_sku_id]['num'] += order.num
                    else:   
                        prod_sku_name = prod_sku and prod_sku.name or order.sku_properties_name
                        skus[outer_sku_id] = {'sku_name':prod_sku_name,
                                              'num':order.num,
                                              'barcode':prod_sku.BARCODE, 
                                              'location':product_sku_location}
                else:
                    prod_sku_name = prod_sku and prod_sku.name or order.sku_properties_name
                    order_items[outer_id]={'num':order.num,
                                           'barcode':product.BARCODE, 
                                           'location':product_location,
                                           'title': product.name if product else order.title,
                                           'skus':{outer_sku_id:{'sku_name':prod_sku_name,
                                                                 'num':order.num,
                                                                 'barcode':prod_sku.BARCODE, 
                                                                 'location':product_sku_location}}}
        
        order_list = sorted(order_items.items(),key=lambda d:d[1]['location'])
        for order in order_list:
            skus = order[1]['skus']
            order[1]['skus'] = sorted(skus.items(),key=lambda d:d[1]['location'])
            
        return order_list    
    
    def get(self,request,wave_id):
        
        wpicks = WavePick.objects.filter(wave_no=wave_id)       
        out_sids = [wp.out_sid for wp in wpicks]
        trades   = MergeTrade.objects.filter(out_sid__in=out_sids,
                                             sys_status__in=(pcfg.WAIT_PREPARE_SEND_STATUS,
                                                             pcfg.WAIT_CHECK_BARCODE_STATUS))
        
        order_items = self.getOrderItems(trades)
        
        for trade in trades:
            out_sid = trade.out_sid
            wpick = WavePick.objects.get(wave_no=wave_id,out_sid=out_sid)
            for order in trade.print_orders:
                pick_item,state = PickItem.objects.get_or_create(
                                            out_sid=out_sid,
                                            outer_id=order.outer_id,
                                            outer_sku_id=order.outer_sku_id,
                                            )
                pick_item.wave_no = wave_id
                pick_item.serial_no = wpick.serial_no
                pick_item.barcode = order.outer_id+order.outer_sku_id
                pick_item.title   = order.title,
                pick_item.item_num  = order.num
                pick_item.save()
                print pick_item.barcode,u'%s%s'%(order.outer_id,order.outer_sku_id)
                
        
        response = render_to_response('wave_detail.html', 
                                      {"wave_id":wave_id,"order_items":order_items}, 
                                      context_instance=RequestContext(request))
        return response
        
    def post(self,request,wave_id):
        
        content = request.REQUEST
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
        return HttpResponse(json.dumps(retparams),mimetype='application/json')
    

class AllocateView(View):
    
    def getPublishValue(self,pickitems):
        
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
            
    def get(self, request, wave_id):
        
        response = render_to_response('allocate_detail.html', 
                                      {"wave_id":wave_id}, 
                                      context_instance=RequestContext(request))
        return response
        
    
    def post(self, request, wave_id):
        
        content = request.REQUEST
        barcode = content.get('barcode')
        
        pick_items = PickItem.objects.filter(wave_no=wave_id,barcode=barcode).order_by('serial_no')
        publish_value  =  self.getPublishValue(pick_items)
        
        group_id = self.getPickGroupByWaveNo(wave_id)
        ppublish,state =  PickPublish.objects.get_or_create(group_id=group_id)
        ppublish.pvalue = publish_value
        ppublish.save()
        
        resparams = {'barcode':barcode,'pickval':','.join(['(%d,%d)'%(item.serial_no,item.item_num) for item in pick_items])}
        return HttpResponse(json.dumps(resparams),mimetype='application/json')
        
        
class PublishView(View):
    
    def get(self, request, group_id):
        
        pick_publish,state = PickPublish.objects.get_or_create(group_id=group_id)
        
        return HttpResponse(pick_publish.pvalue)
        

    
