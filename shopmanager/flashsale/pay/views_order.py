#-*- encoding:utf8 -*-
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response,render
from django.template import RequestContext

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth import authenticate, login as auth_login, SESSION_KEY
from shopback.items.models import Product,ProductSku,ProductCategory
from .models import SaleTrade,SaleOrder,genUUID,Customer
from .tasks import confirmTradeChargeTask
from flashsale.xiaolumm.models import CarryLog,XiaoluMama
import time
import datetime
ISOTIMEFORMAT='%Y-%m-%d '
today = datetime.date.today()
real_today=datetime.date.today().strftime("%Y-%m-%d ")



def order_flashsale(request):
    global today
    now2=today.strftime("%Y-%m-%d ")
    now4=datetime.datetime.strptime(now2+' 00:00:00', '%Y-%m-%d %H:%M:%S')
    now5=datetime.datetime.strptime(now2+' 23:59:59', '%Y-%m-%d %H:%M:%S')
    print '现在',now4
    print '现在',now5
    rec=[]
    trade_info=SaleTrade.objects.filter(created__range=(now4,now5))
    for item in trade_info:
        info={}  
        info['trade']=item
        info['detail']=[]
        for order_info in item.sale_orders.all():
                sum={}
                sum['order']=order_info
                product_info=Product.objects.get(outer_id=order_info.outer_id) 
                sum['product']=product_info
                info['detail'].append(sum)
        rec.append(info)
    return render(request, 'pay/order_flash.html',{'info': rec,'time':real_today,'yesterday':today})


def time_rank(request,time_id):
     global today
     realtoday=datetime.date.today().strftime("%Y-%m-%d ")#真正的今天的时间
     day=time_id
     print int(day),type(day)
     if int(day) == 1:
         today = today- datetime.timedelta(days=1)
         now2=today.strftime("%Y-%m-%d ")
         now4=datetime.datetime.strptime(now2+' 00:00:00', '%Y-%m-%d %H:%M:%S')
         now5=datetime.datetime.strptime(now2+' 23:59:59', '%Y-%m-%d %H:%M:%S')
         print '现在',now4
         print '现在',now5
         rec=[]
         trade_info=SaleTrade.objects.filter(created__range=(now4,now5))
         for item in trade_info:
             info={} 
             info['trade']=item
             info['detail']=[]
             
             for order_info in item.sale_orders.all():
                sum={}
                print 'orderinfo' ,  order_info
                print 'order2' ,  order_info.outer_id 
                sum['order']=order_info
                product_info=Product.objects.get(outer_id=order_info.outer_id) 
                sum['product']=product_info
                info['detail'].append(sum)
             rec.append(info)
             print '本次结束',   rec
        # print rec
         return render(request, 'pay/order_flash.html',{'info': rec,'time':real_today,'yesterday':today})
     
     
     elif int(day) == 0:
         today = datetime.date.today()
         now=today.strftime("%Y-%m-%d ")
         print '今天是',type(now)
         rec=[]
         today = datetime.date.today()
         now2=today.strftime("%Y-%m-%d ")
         now4=datetime.datetime.strptime(now2+' 00:00:00', '%Y-%m-%d %H:%M:%S')
         now5=datetime.datetime.strptime(now2+' 23:59:59', '%Y-%m-%d %H:%M:%S')
         trade_info=SaleTrade.objects.filter(created__range=(now4,now5))
         print '现在',now4
         print '现在',now5
         for item in trade_info:
             info={}  
             info['trade']=item
             info['detail']=[]
             for order_info in item.sale_orders.all():
                sum={}
                print 'orderinfo' ,  order_info
                print 'order2' ,  order_info.outer_id 
                sum['order']=order_info
                product_info=Product.objects.get(outer_id=order_info.outer_id) 
                print product_info,'tttttt'
                sum['product']=product_info
                info['detail'].append(sum)                         
             rec.append(info)
             print '本次结束',   rec
         print rec
         return render(request, 'pay/order_flash.html',{'info': rec,'time':real_today,'yesterday':today})
   
     else :
         if today.strftime("%Y-%m-%d ")==realtoday:
             today = datetime.date.today()
         else:
             today = today + datetime.timedelta(days=1)
         now2=today.strftime("%Y-%m-%d ")
         now4=datetime.datetime.strptime(now2+' 00:00:00', '%Y-%m-%d %H:%M:%S')
         now5=datetime.datetime.strptime(now2+' 23:59:59', '%Y-%m-%d %H:%M:%S')
         trade_info=SaleTrade.objects.filter(created__range=(now4,now5))
         rec=[]
         for item in trade_info:
                 info={}  
                 info['trade']=item
                 info['detail']=[]
                 for order_info in item.sale_orders.all():
                    sum={}
                    print 'orderinfo' ,  order_info                
                    print 'order2' ,  order_info.outer_id 
                    sum['order']=order_info
                    product_info=Product.objects.get(outer_id=order_info.outer_id) 
                    print product_info,'tttttt'
                    sum['product']=product_info
                    info['detail'].append(sum)              
                 rec.append(info)
         return render(request, 'pay/order_flash.html',{'info': rec,'time':real_today,'yesterday':today})  
     
 #增加交易状态的处理
def sale_state(request,state_id):
    print '编号' , type( state_id)
    print '状态是' ,  state_id
    global today
    now2=today.strftime("%Y-%m-%d ")
    now4=datetime.datetime.strptime(now2+' 00:00:00', '%Y-%m-%d %H:%M:%S')
    now5=datetime.datetime.strptime(now2+' 23:59:59', '%Y-%m-%d %H:%M:%S')
    rec=[]
    trade_info=SaleTrade.objects.filter(created__range=(now4,now5))
    for item in trade_info:
        info={}  
        info['trade']=item
        info['detail']=[]
        print 'order1' ,  item.sale_orders.all()
        for order_info in item.sale_orders.all():
                sum={}
                print 'orderinfo' ,  order_info                
                print 'order2' ,  order_info.outer_id 
                sum['order']=order_info
                product_info=Product.objects.get(outer_id=order_info.outer_id) 
                print product_info,'tttttt'
                sum['product']=product_info
                info['detail'].append(sum)
        print '状态2是' ,  item.status
        if item.status==long(state_id):
            rec.append(info)
        print '本次结束',   rec
    print rec
    return render(request, 'pay/order_flash.html',{'info': rec,'time':real_today,'yesterday':today})    
     


#退款状态
def refund_state(request,state_id):
    print '编号' , type( state_id)
    print '状态是' ,  state_id
    global today
    now2=today.strftime("%Y-%m-%d ")
    now4=datetime.datetime.strptime(now2+' 00:00:00', '%Y-%m-%d %H:%M:%S')
    now5=datetime.datetime.strptime(now2+' 23:59:59', '%Y-%m-%d %H:%M:%S')
    trade_info=SaleTrade.objects.filter(created__range=(now4,now5))
    rec=[]
    print 'order0' ,  trade_info
    for item in trade_info:
        info={}  
        info['trade']=item
        info['detail']=[] 
        for order_info in item.sale_orders.all():
                sum={}
                print 'orderinfo' ,  order_info
                print 'order2' ,  order_info.outer_id 
                sum['order']=order_info
                product_info=Product.objects.get(outer_id=order_info.outer_id) 
                print product_info,'tttttt'
                sum['product']=product_info
                info['detail'].append(sum)
                if order_info.refund_status==long(state_id):
                  rec.append(info)
                  print '本次结束',   rec
    print rec
    return render(request, 'pay/order_flash.html',{'info': rec,'time':real_today,'yesterday':today})                 
   
   
def refunding_state(request,state_id):
    print '编号' , type( state_id)
    print '状态是' ,  state_id
    global today
    now2=today.strftime("%Y-%m-%d ")
    now4=datetime.datetime.strptime(now2+' 00:00:00', '%Y-%m-%d %H:%M:%S')
    now5=datetime.datetime.strptime(now2+' 23:59:59', '%Y-%m-%d %H:%M:%S')
    rec=[]
    trade_info=SaleTrade.objects.filter(created__range=(now4,now5))
    print 'order0' ,  trade_info
    for item in trade_info:
        info={}  
        info['trade']=item
        info['detail']=[]       
        print 'order1' ,  item.sale_orders.all()
        for order_info in item.sale_orders.all():
                sum={}
                print 'orderinfo' ,  order_info
                print 'order2' ,  order_info.outer_id 
                sum['order']=order_info
                product_info=Product.objects.get(outer_id=order_info.outer_id) 
                print product_info,'tttttt'
                sum['product']=product_info
                info['detail'].append(sum)
                if order_info.refund_status!=long(0) and order_info.refund_status!=long(7):
                      rec.append(info)
                      print '本次结束',   rec
    print rec
   
    return render(request, 'pay/order_flash.html',{'info': rec,'time':real_today,'yesterday':today})             
             
             
         
         
    