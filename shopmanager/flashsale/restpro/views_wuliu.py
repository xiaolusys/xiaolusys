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
class WuliuView(APIView):
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
        apikey = '47deda738666430bab15306c2878dd3a'     
    #apikey='6a214a769ab8426da93445e9d2078cc8'
    #访问的API代码  
        uid = '39400'
    #uid='39500'
    
        #
        try :
            
             number=request.GET['tid']
        except:
            ##本地固定
             #number="13294025981601113267"
             ##服务器固定
             number="13294025981600958639"
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
        
        
def test(request):
            print "大家好"
            if request.method=='GET':
                print "大家好"
            return Response(99)

    
    

     
