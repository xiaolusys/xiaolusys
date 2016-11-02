# -*- coding:utf8 -*-
import json
import urllib, urllib2
from rest_framework import permissions
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer, BrowsableAPIRenderer
from rest_framework.views import APIView
from rest_framework import authentication
from shopback.base.new_renders import new_BaseJSONRenderer
from django.http import HttpResponse
from rest_framework.response import Response
from shopback.trades.models import TradeWuliu
from shopback.items.models import Product
from flashsale.pay.models import SaleTrade, SaleOrder
import datetime
from . import serializers
from flashsale.restpro.tasks import SaveWuliu_only

BADU_KD100_URL = "http://www.kuaidiapi.cn/rest"
BAIDU_POST_CODE_EXCHANGE = {
    'YUNDA': 'yunda',
    'YUNDA_QR': 'yunda',
    'STO': 'shentong',
    'EMS': 'ems',
    'ZTO': 'zhongtong',
    'ZJS': 'zhaijisong',
    'SF': 'shunfeng',
    'YTO': 'yuantong',
    'HTKY': 'huitongkuaidi',
    'TTKDEX': 'tiantian',
    'QFKD': 'quanfengkuaidi',
}
POST_CODE_NAME_MAP = {
    'YUNDA': u'韵达快递',
    'YUNDA_QR': u'韵达快递',
    'STO': u'申通快递',
    'EMS': u'邮政EMS',
    'ZTO': u'中通快递',
    'ZJS': u'宅急送',
    'SF': u'顺丰速运',
    'YTO': u'圆通',
    'HTKY': u'汇通快递',
    'TTKDEX': u'天天快递',
    'QFKD': u'全峰快递',
}


##fang 2015-8-22 new version
# 本次修复主要是请求要具有选择性
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
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)
    renderer_classes = (new_BaseJSONRenderer, BrowsableAPIRenderer,)

    def get(self, request, *args, **kwargs):
        apikey = '47deda738666430bab15306c2878dd3a'
        # 访问的API代码
        uid = '39400'
        try:
            number = request.GET['tid']
            print(number, "ppppp")
        except:
            ##本地固定
            number = "xd15081955d45da07263e"
        try:
            trade_info = SaleTrade.objects.get(id=number)
        except:
            trade_info = SaleTrade.objects.get(tid=number)
        try:
            exType = trade_info.logistics_company.code
            out_sid = trade_info.out_sid
        except:
            if trade_info.status == 2:
                sale_order = SaleOrder.objects.filter(sale_trade=trade_info)
                shelf = False
                for t in sale_order:
                    shelf_status = Product.objects.get(outer_id=t.outer_id).shelf_status
                    if shelf_status == 0:
                        shelf = True
                        break
                if shelf == True:
                    return Response({"result": False, "message": "您的订单正在配货", "time": trade_info.pay_time})
                else:
                    return Response({"result": False, "message": "付款成功", "time": trade_info.pay_time})
            elif trade_info.status == 7:
                return Response({"result": False, "message": "交易关闭", "time": trade_info.created})

            return Response({"result": False, "message": "订单创建完成", "time": trade_info.created})
        if exType not in POST_CODE_NAME_MAP.keys():
            return Response({"result": False, "message": "亲，包裹已经发出，物流信息暂未更新", "time": trade_info.consign_time})

        count = TradeWuliu.objects.filter(tid=trade_info.tid).count()
        if (count == 0 or count == 1):
            tid = trade_info.tid
            data = {'id': BAIDU_POST_CODE_EXCHANGE.get(exType), 'order': out_sid, 'key': apikey, 'uid': uid}
            req = urllib2.urlopen(BADU_KD100_URL, urllib.urlencode(data), timeout=30)
            content = json.loads(req.read())
            SaveWuliu_only.delay(tid, content)  # 异步任务，存储物 流信息到数据库
            return Response(
                {"result": True, "ret": content, "time": trade_info.consign_time, "create_time": trade_info.pay_time})
        else:
            wuliu_info = TradeWuliu.objects.filter(tid=trade_info.tid)[0]
            last_time = wuliu_info.created  # 上一次的访问时间
            now = datetime.datetime.now()
            # 时间差值
            last_now = (now - last_time).seconds
            # 两个小时内访问数据库

            if wuliu_info.status == 4:
                info = TradeWuliu.objects.filter(tid=trade_info.tid)
                serializer = serializers.TradeWuliuSerializer(info, many=True).data
                return Response({"result": True, "ret": serializer, "time": trade_info.consign_time,
                                 "create_time": trade_info.pay_time})
            elif last_now < 6800:
                print "两个小时内哦"
                info = TradeWuliu.objects.filter(tid=trade_info.tid)
                serializer = serializers.TradeWuliuSerializer(info, many=True).data
                return Response({"result": True, "ret": serializer, "time": trade_info.consign_time,
                                 "create_time": trade_info.pay_time})
            # 两个小时外，就请求接口API
            else:
                tid = trade_info.tid
                data = {'id': BAIDU_POST_CODE_EXCHANGE.get(exType), 'order': out_sid, 'key': apikey, 'uid': uid}
                req = urllib2.urlopen(BADU_KD100_URL, urllib.urlencode(data), timeout=30)
                content = json.loads(req.read())
                SaveWuliu_only.delay(tid, content)  # 异步任务，存储物流信息到数据库
                return Response({"result": True, "ret": content, "time": trade_info.consign_time,
                                 "create_time": trade_info.pay_time})
