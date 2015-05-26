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
#ISOTIMEFORMAT='%Y-%m-%d %X'
ISOTIMEFORMAT='%Y-%m-%d '
today = datetime.date.today()
real_today=datetime.date.today().strftime("%Y-%m-%d ")
def order_flashsale(request):
    global today
    today = datetime.date.today()
    today2 = datetime.date.today()
    #today2 = today2 - datetime.timedelta(days=1)
    now2=today2.strftime("%Y-%m-%d ")
    rec=[]
    #print type(rec)
    trade_info=SaleTrade.objects.all()
        #item=trade_info[0]
    print 'order0' ,  trade_info
    #rec['trade']=trade_info
    #print type(rec),rec
    for item in trade_info:
        info={}  
        #info['product']=[]
        #info['order']=[]
        info['trade']=item
        info['detail']=[]
        #sum={}
        
        print 'order1' ,  item.sale_orders.all()
#         a=item.tid
#         print type(a)
#         b='FO'+str(a)[2:21]
#         print b
#         print type(b)
#         c=unicode(b, "utf-8")
#         print type(c)
#         print c
        for order_info in item.sale_orders.all():
                #order_info=SaleOrder.objects.get(oid=c)
                sum={}
                print 'orderinfo' ,  order_info
                
                print 'order2' ,  order_info.outer_id 
                #info['order'].append(order_info)
                sum['order']=order_info
                product_info=Product.objects.get(outer_id=order_info.outer_id) 
                print product_info,'tttttt'
                #info['product'].append(product_info)
                sum['product']=product_info
                info['detail'].append(sum)
        rec.append(info)
        print '本次结束',   rec
    print rec
    
    
    #order_info=SaleOrder.objects.all()
    
    #return render_to_response("pay/order_flash.html",order_info,context_instance=RequestContext(request))
    #return render(request, 'pay/order_flash.html',{'trade_info': trade_info,'order_info': order_info})
    return render(request, 'pay/order_flash.html',{'info': rec,'time':real_today,'yesterday':'所有'})


def time_rank(request,time_id):
     global today
     realtoday=datetime.date.today().strftime("%Y-%m-%d ")#真正的今天的时间
     day=time_id
     print int(day),type(day)
     if int(day) == 1:
         #print '222'
         #print time.strftime( ISOTIMEFORMAT, time.localtime( time.time() ) )
         #today = datetime.date.today() 
         today = today - datetime.timedelta(days=1)
         now=today.strftime("%Y-%m-%d ")
         print '今天是',type(now)
         trade_info=SaleTrade.objects.get(id=2)
         #print trade_info.created.strftime("%Y-%m-%d ") 
         rec=[]
    #print type(rec)
         trade_info=SaleTrade.objects.all()
        #item=trade_info[0]
         #print 'order0' ,  trade_info
    #rec['trade']=trade_info
    #print type(rec),rec
         for item in trade_info:
             info={} 
             print '订单是',type(item.pay_time.strftime("%Y-%m-%d "))
             info['trade']=item
             info['detail']=[]
             for order_info in item.sale_orders.all():
                #order_info=SaleOrder.objects.get(oid=c)
                sum={}
                print 'orderinfo' ,  order_info
                
                print 'order2' ,  order_info.outer_id 
                #info['order'].append(order_info)
                sum['order']=order_info
                product_info=Product.objects.get(outer_id=order_info.outer_id) 
                print product_info,'tttttt'
                #info['product'].append(product_info)
                sum['product']=product_info
                info['detail'].append(sum)
             if item.created.strftime("%Y-%m-%d ")==now: #测试用的时间为pay——time
                 rec.append(info)
             print '本次结束',   rec
         print rec
    
    
    #order_info=SaleOrder.objects.all()
    
    #return render_to_response("pay/order_flash.html",order_info,context_instance=RequestContext(request))
    #return render(request, 'pay/order_flash.html',{'trade_info': trade_info,'order_info': order_info})
         return render(request, 'pay/order_flash.html',{'info': rec,'time':real_today,'yesterday':now})
     #return render(request, 'pay/order_flash.html')
     elif int(day) == 0:
         today = datetime.date.today()
         now=today.strftime("%Y-%m-%d ")
         print '今天是',type(now)
         trade_info=SaleTrade.objects.get(id=2)
         #print trade_info.created.strftime("%Y-%m-%d ") 
         rec=[]
    #print type(rec)
         trade_info=SaleTrade.objects.all()
        #item=trade_info[0]
         #print 'order0' ,  trade_info
    #rec['trade']=trade_info
    #print type(rec),rec
         for item in trade_info:
             print '订单是',type(item.pay_time.strftime("%Y-%m-%d "))
             info={}  
             info['trade']=item
             info['detail']=[]
             for order_info in item.sale_orders.all():
                #order_info=SaleOrder.objects.get(oid=c)
                sum={}
                print 'orderinfo' ,  order_info
                
                print 'order2' ,  order_info.outer_id 
                #info['order'].append(order_info)
                sum['order']=order_info
                product_info=Product.objects.get(outer_id=order_info.outer_id) 
                print product_info,'tttttt'
                #info['product'].append(product_info)
                sum['product']=product_info
                info['detail'].append(sum)
             
             if item.created.strftime("%Y-%m-%d ")==now: 
                 rec.append(info)
             print '本次结束',   rec
         print rec
    
    
    #order_info=SaleOrder.objects.all()
    
    #return render_to_response("pay/order_flash.html",order_info,context_instance=RequestContext(request))
    #return render(request, 'pay/order_flash.html',{'trade_info': trade_info,'order_info': order_info})
         return render(request, 'pay/order_flash.html',{'info': rec,'time':real_today,'yesterday':now})
   
     else :
         if today.strftime("%Y-%m-%d ")==realtoday:
             order_flashsale(request)
         else:
             today = today + datetime.timedelta(days=1)
         now=today.strftime("%Y-%m-%d ")
         print '今天是',type(now)
         trade_info=SaleTrade.objects.get(id=2)
         #print trade_info.created.strftime("%Y-%m-%d ") 
         rec=[]
    #print type(rec)
         trade_info=SaleTrade.objects.all()
        #item=trade_info[0]
         #print 'order0' ,  trade_info
    #rec['trade']=trade_info
    #print type(rec),rec
         for item in trade_info:
             print '订单是',type(item.pay_time.strftime("%Y-%m-%d "))
             info={}  
             info['trade']=item
             info['detail']=[]
             for order_info in item.sale_orders.all():
                #order_info=SaleOrder.objects.get(oid=c)
                sum={}
                print 'orderinfo' ,  order_info
                
                print 'order2' ,  order_info.outer_id 
                #info['order'].append(order_info)
                sum['order']=order_info
                product_info=Product.objects.get(outer_id=order_info.outer_id) 
                print product_info,'tttttt'
                #info['product'].append(product_info)
                sum['product']=product_info
                info['detail'].append(sum)
             if item.created.strftime("%Y-%m-%d ")==now: 
                 rec.append(info)
             print '本次结束',   rec
         print rec
    
    
    #order_info=SaleOrder.objects.all()
    
    #return render_to_response("pay/order_flash.html",order_info,context_instance=RequestContext(request))
    #return render(request, 'pay/order_flash.html',{'trade_info': trade_info,'order_info': order_info})
         return render(request, 'pay/order_flash.html',{'info': rec,'time':real_today,'yesterday':now})  
 #增加交易状态的处理
def sale_state(request,state_id):
    print '编号' , type( state_id)
#     if state_id ==u'1':
#         state="WAIT_BUYER_PAY"#待付款
#     elif state_id ==u'1':
#         state="WAIT_SELLER_SEND_GOODS"#已经付款
#     else:
#         state="TRADE_FINISHED"#交易成功
    print '状态是' ,  state_id
    global today
    today = datetime.date.today()
    today2 = datetime.date.today()
    today2 = today2 - datetime.timedelta(days=1)
    now2=today2.strftime("%Y-%m-%d ")
    rec=[]
    #print type(rec)
    trade_info=SaleTrade.objects.all()
        #item=trade_info[0]
    print 'order0' ,  trade_info
    #rec['trade']=trade_info
    #print type(rec),rec
    for item in trade_info:
        info={}  
        #info['product']=[]
        #info['order']=[]
        info['trade']=item
        info['detail']=[]
        #sum={}
        
        print 'order1' ,  item.sale_orders.all()
#         a=item.tid
#         print type(a)
#         b='FO'+str(a)[2:21]
#         print b
#         print type(b)
#         c=unicode(b, "utf-8")
#         print type(c)
#         print c
        for order_info in item.sale_orders.all():
                #order_info=SaleOrder.objects.get(oid=c)
                sum={}
                print 'orderinfo' ,  order_info
                
                print 'order2' ,  order_info.outer_id 
                #info['order'].append(order_info)
                sum['order']=order_info
                product_info=Product.objects.get(outer_id=order_info.outer_id) 
                print product_info,'tttttt'
                #info['product'].append(product_info)
                sum['product']=product_info
                info['detail'].append(sum)
        print '状态2是' ,  item.status
        if item.status==long(state_id):
            rec.append(info)
        print '本次结束',   rec
    print rec
    
    
    #order_info=SaleOrder.objects.all()
    
    #return render_to_response("pay/order_flash.html",order_info,context_instance=RequestContext(request))
    #return render(request, 'pay/order_flash.html',{'trade_info': trade_info,'order_info': order_info})
    return render(request, 'pay/order_flash.html',{'info': rec,'time':real_today,'yesterday':'所有'})    
     


#退款状态
def refund_state(request,state_id):
    print '编号' , type( state_id)
#     if state_id ==u'1':
#         state="WAIT_BUYER_PAY"#待付款
#     elif state_id ==u'1':
#         state="WAIT_SELLER_SEND_GOODS"#已经付款
#     else:
#         state="TRADE_FINISHED"#交易成功
    print '状态是' ,  state_id
    global today
    today = datetime.date.today()
    today2 = datetime.date.today()
    today2 = today2 - datetime.timedelta(days=1)
    now2=today2.strftime("%Y-%m-%d ")
    rec=[]
    #print type(rec)
    trade_info=SaleTrade.objects.all()
        #item=trade_info[0]
    print 'order0' ,  trade_info
    #rec['trade']=trade_info
    #print type(rec),rec
    for item in trade_info:
        info={}  
        #info['product']=[]
        #info['order']=[]
        info['trade']=item
        info['detail']=[]
        #sum={}
        
        print 'order1' ,  item.sale_orders.all()
#         a=item.tid
#         print type(a)
#         b='FO'+str(a)[2:21]
#         print b
#         print type(b)
#         c=unicode(b, "utf-8")
#         print type(c)
#         print c
        for order_info in item.sale_orders.all():
                #order_info=SaleOrder.objects.get(oid=c)
                sum={}
                print 'orderinfo' ,  order_info
                
                print 'order2' ,  order_info.outer_id 
                #info['order'].append(order_info)
                sum['order']=order_info
                product_info=Product.objects.get(outer_id=order_info.outer_id) 
                print product_info,'tttttt'
                #info['product'].append(product_info)
                sum['product']=product_info
                info['detail'].append(sum)
        print '状态2是' ,  order_info.refund_status
        if order_info.refund_status==long(state_id):
            rec.append(info)
        print '本次结束',   rec
    print rec
    
    
    #order_info=SaleOrder.objects.all()
    
    #return render_to_response("pay/order_flash.html",order_info,context_instance=RequestContext(request))
    #return render(request, 'pay/order_flash.html',{'trade_info': trade_info,'order_info': order_info})
    return render(request, 'pay/order_flash.html',{'info': rec,'time':real_today,'yesterday':now2})                 
   
   
def refunding_state(request,state_id):
    print '编号' , type( state_id)
#     if state_id ==u'1':
#         state="WAIT_BUYER_PAY"#待付款
#     elif state_id ==u'1':
#         state="WAIT_SELLER_SEND_GOODS"#已经付款
#     else:
#         state="TRADE_FINISHED"#交易成功
    print '状态是' ,  state_id
    global today
    today = datetime.date.today()
    today2 = datetime.date.today()
    today2 = today2 - datetime.timedelta(days=1)
    now2=today2.strftime("%Y-%m-%d ")
    rec=[]
    #print type(rec)
    trade_info=SaleTrade.objects.all()
        #item=trade_info[0]
    print 'order0' ,  trade_info
    #rec['trade']=trade_info
    #print type(rec),rec
    for item in trade_info:
        info={}  
        #info['product']=[]
        #info['order']=[]
        info['trade']=item
        info['detail']=[]
        #sum={}
        
        print 'order1' ,  item.sale_orders.all()
#         a=item.tid
#         print type(a)
#         b='FO'+str(a)[2:21]
#         print b
#         print type(b)
#         c=unicode(b, "utf-8")
#         print type(c)
#         print c
        for order_info in item.sale_orders.all():
                #order_info=SaleOrder.objects.get(oid=c)
                sum={}
                print 'orderinfo' ,  order_info
                
                print 'order2' ,  order_info.outer_id 
                #info['order'].append(order_info)
                sum['order']=order_info
                product_info=Product.objects.get(outer_id=order_info.outer_id) 
                print product_info,'tttttt'
                #info['product'].append(product_info)
                sum['product']=product_info
                info['detail'].append(sum)
        print '状态2是' ,  order_info.refund_status
        if order_info.refund_status!=long(0) and order_info.refund_status!=long(7):
            rec.append(info)
        print '本次结束',   rec
    print rec
    
    
    #order_info=SaleOrder.objects.all()
    
    #return render_to_response("pay/order_flash.html",order_info,context_instance=RequestContext(request))
    #return render(request, 'pay/order_flash.html',{'trade_info': trade_info,'order_info': order_info})
    return render(request, 'pay/order_flash.html',{'info': rec,'time':real_today,'yesterday':now2})             
             
             
         
         
    