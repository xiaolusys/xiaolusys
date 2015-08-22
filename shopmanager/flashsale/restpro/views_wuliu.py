#-*- coding:utf8 -*-
import json
import urllib,urllib2
from rest_framework import viewsets
from rest_framework import authentication
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework import permissions
from rest_framework.compat import OrderedDict
from rest_framework.renderers import JSONRenderer,TemplateHTMLRenderer,BrowsableAPIRenderer
from rest_framework.views import APIView
from rest_framework import filters
from rest_framework import authentication
from rest_framework import status
from shopback.base.new_renders import new_BaseJSONRenderer   
from django.http import  HttpResponse
from rest_framework.response import Response

from flashsale.restpro.serializers import Trade_wuliuSerializer
#fang  2015-8-19
from shopback.trades.models import Trade_wuliu
from shopback.items.models import Product
from flashsale.pay.models import  SaleTrade,SaleOrder
# BADU_KD100_URL = "http://baidu.kuaidi100.com/query"
BADU_KD100_URL = "http://www.kuaidiapi.cn/rest"
BAIDU_POST_CODE_EXCHANGE={
                         'YUNDA':'yunda',
                         'STO':'shentong',
                         'EMS':'ems',
                         'ZTO':'zhongtong',
                         'ZJS':'zhaijisong',
                         'SF':'shunfeng',
                         'YTO':'yuantong',
                         'HTKY':'huitongkuaidi',
                         'TTKDEX':'tiantian',
                         'QFKD':'quanfengkuaidi',
                         }
POST_CODE_NAME_MAP = {'YUNDA':u'韵达快递',
                      'STO':u'申通快递',
                      'EMS':u'邮政EMS',
                      'ZTO':u'中通快递',
                      'ZJS':u'宅急送',
                      'SF':u'顺丰速运',
                      'YTO':u'圆通',
                      'HTKY':u'汇通快递',
                      'TTKDEX':u'天天快递',
                      'QFKD':u'全峰快递',
                      }

# def getLogisticTrace22(out_sid,exType):
#     
#     post_array = []
#     post_array.append((u'快递公司', POST_CODE_NAME_MAP.get(exType,'other')))
#     post_array.append((u'快递单号', out_sid))
#     
#     if exType not in POST_CODE_NAME_MAP.keys():
#         post_array.append(('运输信息',[('','暂时无法查询该快递公司')]))
#         return post_array
#     
#     data = {'type':BAIDU_POST_CODE_EXCHANGE.get(exType),'postid':out_sid}
#     req = urllib2.urlopen(BADU_KD100_URL, urllib.urlencode(data),timeout=30)
#     content = json.loads(req.read())
#     
#     if content.get('message') != 'ok':
#         post_array.append(('运输信息',[('','暂未查询到快递信息')]))
#         return post_array
#     
#     traces  = []
#     for t in content['data']:
#         traces.append((t['ftime'],t['context']))
#     post_array.append(('运输信息', traces))
#     
#     return post_array    
#     
    
from shopback.trades.models import MergeTrade
class WuliuView01(APIView):
    """ 物流地址api     方凯能         2015-8-13 
     /rest/wuliu/      传递参数tid
     
         id          快递代号、点击 代码对照 查看所有快递对应代号
         name        快递名称
         order          快递单号、注意区分大小写
    快递API单号状态（status）
    -1     待查询、在批量查询中才会出现的状态,指提交后还没有进行任何更新的单号
0     查询异常
1     暂无记录、单号没有任何跟踪记录
2     在途中
3     派送中
4     已签收
5     拒收、用户拒签
6     疑难件、以为某些原因无法进行派送
7     无效单
8     超时单
9     签收失败
    
    快递API错误代号（errcode）
    0000     接口调用正常,无任何错误
0001     传输参数格式有误
0002     用户编号(uid)无效
0003     用户被禁用
0004     key无效
0005     快递代号(id)无效
0006     访问次数达到最大额度
0007     查询服务器返回错误
    
    
    '""" 
    #print '这里是地址api'
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication,authentication.BasicAuthentication,)
    renderer_classes = (new_BaseJSONRenderer,BrowsableAPIRenderer,)
    def get(self, request, *args, **kwargs):
        # print '这这里是物流list'
        #apikey = '47deda738666430bab15306c2878dd3a'     
        apikey='ebd77d3a6ef243c4bf1b1f8610443e27'
    #访问的API代码  
        #uid = '39400'
        uid='40340'
    
        #
        try :            
            number=request.GET['tid']
        except:
            ##本地固定
            number="13294025981601113267"
            ##服务器固定
            #number="13294025981600958639"
        trade_info=MergeTrade.objects.get( tid=number )
        #.out_sid,item.logistics_company.code
        #exType = request.GET['exType']
        #out_sid=request.GET['out_sid']
        exType=trade_info.logistics_company.code
        out_sid=trade_info.out_sid
        
        #
#         post_array = []
#         post_array.append((u'快递公司', POST_CODE_NAME_MAP.get(exType,'other')))
#         post_array.append((u'快递单号', out_sid))
    
        if exType not in POST_CODE_NAME_MAP.keys():
            # post_array.append(('运输信息',[('','暂时无法查询该快递公司')]))
            # return post_array
            return Response("暂时无法查询此公司")  
            # paramsData = {'key': apikey, 'uid': uid, 'order':order, 'id':id}  
        data = {'id':BAIDU_POST_CODE_EXCHANGE.get(exType),'order':out_sid,'key': apikey,'uid': uid}
        req = urllib2.urlopen(BADU_KD100_URL, urllib.urlencode(data),timeout=30)
        content = json.loads(req.read())
    
#         if content.get('message') != '':
#             post_array.append(('运输信息',[('','暂未查询到快递信息')]))
#             return post_array
#     
#         traces  = []
#         for t in content['data']:
#             traces.append((t['time'],t['content']))
#         post_array.append(('运输信息', traces))
#         print  "信息",post_array
        return Response(content)    
        
        
def test22(request):
            
    print "大家好"
    if request.method=='GET':
        print "大家好,进入get方法"
        #return  Response(99)
                # print '这这里是物流list'
        #apikey = '47deda738666430bab15306c2878dd3a'     
        apikey='ebd77d3a6ef243c4bf1b1f8610443e27'
    #访问的API代码  
        # uid = '39400'
        uid='40340'
        #
        try :
            number=request.GET['tid']
        except:
            ##本地固定
            number="13294025981601113267"
            ##服务器固定
            # number="13294025981600958639"
        trade_info=MergeTrade.objects.get( tid=number )
        #.out_sid,item.logistics_company.code
        #exType = request.GET['exType']
        #out_sid=request.GET['out_sid']
        exType=trade_info.logistics_company.code
        out_sid=trade_info.out_sid
        
        #
#         post_array = []
#         post_array.append((u'快递公司', POST_CODE_NAME_MAP.get(exType,'other')))
#         post_array.append((u'快递单号', out_sid))
    
        if exType not in POST_CODE_NAME_MAP.keys():
            # post_array.append(('运输信息',[('','暂时无法查询该快递公司')]))
            # return post_array
            return Response("暂时无法查询此公司")  
            # paramsData = {'key': apikey, 'uid': uid, 'order':order, 'id':id}  
        data = {'id':BAIDU_POST_CODE_EXCHANGE.get(exType),'order':out_sid,'key': apikey,'uid': uid}
        req = urllib2.urlopen(BADU_KD100_URL, urllib.urlencode(data),timeout=30)
        content = json.loads(req.read())
        print content
        
        # wuliu=   Trade_wuliu()
        #wuliu.tid=number
        #wuliu.status=content['status']
        #wuliu.out_sid=content['order']
        #wuliu.errcode=content['errcode']
        for t in content['data']:
            wuliu=   Trade_wuliu()
            wuliu.tid=number
            wuliu.status=content['status']
            wuliu.logistics_company=content['name']
            wuliu.out_sid=content['order']
            wuliu.errcode=content['errcode']
            wuliu.content=t['content']
            wuliu.time=t['time']
            wuliu.save()
        print wuliu
#         if content.get('message') != '':
#             post_array.append(('运输信息',[('','暂未查询到快递信息')]))
#             return post_array
#     
#         traces  = []
#         for t in content['data']:
#             traces.append((t['time'],t['content']))
#         post_array.append(('运输信息', traces))
        print  "信息",content['status']
        return Response(content)    
    
    
from flashsale.restpro.tasks import SaveWuliu,SaveWuliu_only
def test(request):
            
    print "大家好"
    if request.method=='GET':
        #trade=MergeTrade.objects.filter(sys_status='FINISHED')[:10]
        trade=SaleTrade.objects.filter()[:10]
        for info in trade:
           #SaveWuliu(info.tid)
            print info.tid
            #test1.delay()
            SaveWuliu.delay(info.tid)
        #print  "信息",content['status']
        return     HttpResponse("ok")         


def  SaveWuliu01(tid):
        print "调用"
        apikey='ebd77d3a6ef243c4bf1b1f8610443e27'
    #访问的API代码  
        uid='40340'
        
        trade_info=MergeTrade.objects.get( tid=tid )
        exType=trade_info.logistics_company.code
        out_sid=trade_info.out_sid
        if exType not in POST_CODE_NAME_MAP.keys():
            return Response("暂时无法查询此公司")  
        data = {'id':BAIDU_POST_CODE_EXCHANGE.get(exType),'order':out_sid,'key': apikey,'uid': uid}
        req = urllib2.urlopen(BADU_KD100_URL, urllib.urlencode(data),timeout=30)
        content = json.loads(req.read())
        print content
        for t in content['data']:
            wuliu=   Trade_wuliu()
            wuliu.tid=tid
            wuliu.status=content['status']
            wuliu.logistics_company=content['name']
            wuliu.out_sid=content['order']
            wuliu.errcode=content['errcode']
            wuliu.content=t['content']
            wuliu.time=t['time']
            wuliu.save()
            
            
            
            
            
            
            
            
 ##fang 2015-8-20  version      就是边查边存      
class WuliuView02(APIView):
    """ 物流地址api     方凯能         2015-8-20
     /rest/wuliu/      传递参数tid
     
         id          快递代号、点击 代码对照 查看所有快递对应代号
         name        快递名称
         order          快递单号、注意区分大小写
    快递API单号状态（status）
    -1     待查询、在批量查询中才会出现的状态,指提交后还没有进行任何更新的单号
0     查询异常
1     暂无记录、单号没有任何跟踪记录
2     在途中
3     派送中
4     已签收
5     拒收、用户拒签
6     疑难件、以为某些原因无法进行派送
7     无效单
8     超时单
9     签收失败
    
    快递API错误代号（errcode）
    0000     接口调用正常,无任何错误
0001     传输参数格式有误
0002     用户编号(uid)无效
0003     用户被禁用
0004     key无效
0005     快递代号(id)无效
0006     访问次数达到最大额度
0007     查询服务器返回错误
    
    
    '""" 
    #print '这里是地址api'
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication,authentication.BasicAuthentication,)
    renderer_classes = (new_BaseJSONRenderer,BrowsableAPIRenderer,)
    def get(self, request, *args, **kwargs):
       
        apikey = '47deda738666430bab15306c2878dd3a'     
        #apikey='ebd77d3a6ef243c4bf1b1f8610443e27'
    #访问的API代码  
        uid = '39400'
       # uid='40340'
    
        #
        try :            
            number=request.GET['tid']
        except:
            ##本地固定
            number="xd15081555cedf5eb94f3"
            ##服务器固定
            #number="xd15081955d45da07263e"
        try:
            trade_info=SaleTrade.objects.get( id=number )
        except:
            trade_info=SaleTrade.objects.get(tid=number )
        
        #.out_sid,item.logistics_company.code
        #exType = request.GET['exType']
        #out_sid=request.GET['out_sid']
        try:
            exType=trade_info.logistics_company.code
            out_sid=trade_info.out_sid
        except:
            return    Response({"result":False}) 
        
        #
#         post_array = []
#         post_array.append((u'快递公司', POST_CODE_NAME_MAP.get(exType,'other')))
#         post_array.append((u'快递单号', out_sid))
    
        if exType not in POST_CODE_NAME_MAP.keys():
            # post_array.append(('运输信息',[('','暂时无法查询该快递公司')]))
            # return post_array
            return Response({"result":False})   
            # paramsData = {'key': apikey, 'uid': uid, 'order':order, 'id':id}  
        tid=trade_info.tid
        data = {'id':BAIDU_POST_CODE_EXCHANGE.get(exType),'order':out_sid,'key': apikey,'uid': uid}
        req = urllib2.urlopen(BADU_KD100_URL, urllib.urlencode(data),timeout=30)
        content = json.loads(req.read())
        for t in content['data']:
            wuliu=   Trade_wuliu()
            wuliu.tid=tid
            wuliu.status=content['status']
            wuliu.logistics_company=content['name']
            wuliu.out_sid=content['order']
            wuliu.errcode=content['errcode']
            wuliu.content=t['content']
            wuliu.time=t['time']
            wuliu.save()
#         if content.get('message') != '':
#             post_array.append(('运输信息',[('','暂未查询到快递信息')]))
#             return post_array
#     
#         traces  = []
#         for t in content['data']:
#             traces.append((t['time'],t['content']))
#         post_array.append(('运输信息', traces))
#         print  "信息",post_array
        return Response({"result":True,"ret":content})                
    
    
    
    
    
    
   ##fang 2015-8-21 new version        
class WuliuView03(APIView):
    """ 物流地址api     方凯能         2015-8-20
     /rest/wuliu/      传递参数tid
     
         id          快递代号、点击 代码对照 查看所有快递对应代号
         name        快递名称
         order          快递单号、注意区分大小写
    快递API单号状态（status）
    -1     待查询、在批量查询中才会出现的状态,指提交后还没有进行任何更新的单号
0     查询异常
1     暂无记录、单号没有任何跟踪记录
2     在途中
3     派送中
4     已签收
5     拒收、用户拒签
6     疑难件、以为某些原因无法进行派送
7     无效单
8     超时单
9     签收失败
    
    快递API错误代号（errcode）
    0000     接口调用正常,无任何错误
0001     传输参数格式有误
0002     用户编号(uid)无效
0003     用户被禁用
0004     key无效
0005     快递代号(id)无效
0006     访问次数达到最大额度
0007     查询服务器返回错误
    '""" 
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication,authentication.BasicAuthentication,)
    renderer_classes = (new_BaseJSONRenderer,BrowsableAPIRenderer,)
    def get(self, request, *args, **kwargs):
        apikey = '47deda738666430bab15306c2878dd3a'     
        #apikey='ebd77d3a6ef243c4bf1b1f8610443e27'
    #访问的API代码  
        uid = '39400'
       # uid='40340'
        try :            
            number=request.GET['tid']
        except:
            ##本地固定
            #number="xd15081555cedf5eb94f3"
            ##服务器固定
            number="xd15081955d45da07263e"
        try:
            trade_info=SaleTrade.objects.get( id=number )
        except:
            trade_info=SaleTrade.objects.get(tid=number )
        try:
            exType=trade_info.logistics_company.code
            out_sid=trade_info.out_sid
        except:
            #print trade_info.status
            if trade_info.status==2:
                return    Response({"result":False,"message":"您的订单正在配货","time":trade_info.pay_time }) 
            elif trade_info.status==7:
                return    Response({"result":False, "message":"交易关闭","time":trade_info.created }) 
            return    Response({"result":False,"message":"订单创建完成","time":trade_info.created }) 
        if exType not in POST_CODE_NAME_MAP.keys():
            return Response({"result":False,"message":"亲，您的包裹已经在路上啦!暂时不支持此快递公司物流信息哦！","time":trade_info.consign_time})   
        
        tid=trade_info.tid
        data = {'id':BAIDU_POST_CODE_EXCHANGE.get(exType),'order':out_sid,'key': apikey,'uid': uid}
        req = urllib2.urlopen(BADU_KD100_URL, urllib.urlencode(data),timeout=30)
        content = json.loads(req.read())
        SaveWuliu_only.delay(tid,content)  ##异步任务，存储物流信息到数据库
        return Response({"result":True,"ret":content,"time":trade_info.consign_time,"create_time":trade_info.pay_time})                    
    
import datetime,time    
from . import serializers     
    ##fang 2015-8-22 new version        
    #本次修复主要是请求要具有选择性
class WuliuView(APIView):
    """ 物流地址api     方凯能         2015-8-20
     /rest/wuliu/      传递参数tid
     
         id          快递代号、点击 代码对照 查看所有快递对应代号
         name        快递名称
         order          快递单号、注意区分大小写
    快递API单号状态（status）
    -1     待查询、在批量查询中才会出现的状态,指提交后还没有进行任何更新的单号
0     查询异常
1     暂无记录、单号没有任何跟踪记录
2     在途中
3     派送中
4     已签收
5     拒收、用户拒签
6     疑难件、以为某些原因无法进行派送
7     无效单
8     超时单
9     签收失败
    
    快递API错误代号（errcode）
    0000     接口调用正常,无任何错误
0001     传输参数格式有误
0002     用户编号(uid)无效
0003     用户被禁用
0004     key无效
0005     快递代号(id)无效
0006     访问次数达到最大额度
0007     查询服务器返回错误
    '""" 
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication,authentication.BasicAuthentication,)
    renderer_classes = (new_BaseJSONRenderer,BrowsableAPIRenderer,)
    def get(self, request, *args, **kwargs):
        apikey = '47deda738666430bab15306c2878dd3a'     
        #apikey='ebd77d3a6ef243c4bf1b1f8610443e27'
    #访问的API代码  
        uid = '39400'
       # uid='40340'
        try :            
            number=request.GET['tid']
        except:
            ##本地固定
            number="xd15081555cedf5eb94f3"
            ##服务器固定
            #number="xd15081955d45da07263e"
        try:
            trade_info=SaleTrade.objects.get( id=number )
        except:
            trade_info=SaleTrade.objects.get(tid=number )
        try:
            exType=trade_info.logistics_company.code
            out_sid=trade_info.out_sid
        except:
            #print trade_info.status
            if trade_info.status==2:
                product_outid=SaleOrder.objects.get(sale_trade=trade_info).outer_id
                shelf_status=Product.objects.get(outer_id=product_outid).shelf_status
                if  shelf_status==0:
                    return    Response({"result":False,"message":"您的订单正在配货","time":trade_info.pay_time }) 
                else:
                    return    Response({"result":False,"message":"付款成功","time":trade_info.pay_time }) 
                #print "订单",Product.objects.get(outer_id=product_outid).shelf_status
                #return    Response({"result":False,"message":"您的订单正在配货","time":trade_info.pay_time }) 
            elif trade_info.status==7:
                return    Response({"result":False, "message":"交易关闭","time":trade_info.created }) 
            
            return    Response({"result":False,"message":"订单创建完成","time":trade_info.created }) 
        if exType not in POST_CODE_NAME_MAP.keys():
            return Response({"result":False,"message":"亲，您的包裹已经在路上啦!暂时不支持此快递公司物流信息哦！","time":trade_info.consign_time})   
        
        
        
        count=Trade_wuliu.objects.filter(tid=trade_info.tid).count()
        print "数目",count
        if (count==0  or count==1):
            tid=trade_info.tid
            data = {'id':BAIDU_POST_CODE_EXCHANGE.get(exType),'order':out_sid,'key': apikey,'uid': uid}
            req = urllib2.urlopen(BADU_KD100_URL, urllib.urlencode(data),timeout=30)
            content = json.loads(req.read())
            SaveWuliu_only.delay(tid,content)  ##异步任务，存储物流信息到数据库
            return Response({"result":True,"ret":content,"time":trade_info.consign_time,"create_time":trade_info.pay_time})        
        else :
            wuliu_info=Trade_wuliu.objects.filter(tid=trade_info.tid)[0]
            last_time=wuliu_info.created  #上一次的访问时间
            #print wuliu_info.created,type(wuliu_info.created)
            now =datetime.datetime.now()
            #print now,type(now)
            #时间差值
            last_now=(now-last_time).seconds
            #两个小时内访问数据库
            
            if wuliu_info.status==4:
                info=Trade_wuliu.objects.filter(tid=trade_info.tid)
                serializer=serializers.Trade_wuliuSerializer(info,many=True).data
                return Response({"result":True,"ret":serializer,"time":trade_info.consign_time,"create_time":trade_info.pay_time})
            elif last_now<6800:
                print "两个小时内哦"
                info=Trade_wuliu.objects.filter(tid=trade_info.tid)
                serializer=serializers.Trade_wuliuSerializer(info,many=True).data
                return Response({"result":True,"ret":serializer,"time":trade_info.consign_time,"create_time":trade_info.pay_time})
            #两个小时外，就请求接口API
            else:
                tid=trade_info.tid
                data = {'id':BAIDU_POST_CODE_EXCHANGE.get(exType),'order':out_sid,'key': apikey,'uid': uid}
                req = urllib2.urlopen(BADU_KD100_URL, urllib.urlencode(data),timeout=30)
                content = json.loads(req.read())
                SaveWuliu_only.delay(tid,content)  ##异步任务，存储物流信息到数据库
                return Response({"result":True,"ret":content,"time":trade_info.consign_time,"create_time":trade_info.pay_time})   
                
                    