#-*- coding:utf-8 -*-
# Create your views here.

import json
from django.http import HttpResponse,Http404
from django.shortcuts import redirect,render_to_response
from django.views.generic import View
from django.template import RequestContext
from django.contrib.auth.models import User

from shopapp.weixin.views import get_user_openid,valid_openid
from shopapp.weixin.models import WXOrder
from shopapp.weixin.service import WeixinUserService
from shopback.base import log_action, ADDITION, CHANGE

from models import Clicks, XiaoluMama, AgencyLevel, CashOut, CarryLog

from serializers import CashOutSerializer,CarryLogSerializer
from rest_framework import generics
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response


import logging
logger = logging.getLogger('django.request')


import datetime, re


WX_WAIT_PAY  = 1
WX_WAIT_SEND = 2
WX_WAIT_CONFIRM = 3
WX_FINISHED  = 5
WX_CLOSE     = 6
WX_FEEDBACK  = 8
    
WXORDER_STATUS = {
    WX_WAIT_PAY:u'待付款',
    WX_WAIT_SEND:u'待发货',
    WX_WAIT_CONFIRM:u'待确认收货',
    WX_FINISHED:u'已完成',
    WX_CLOSE:u'已关闭',
    WX_FEEDBACK:u'维权中'}

SHOPURL = "http://mp.weixin.qq.com/bizmall/mallshelf?id=&t=mall/list&biz=MzA5NTI1NjYyNg==&shelf_id=2&showwxpaytitle=1#wechat_redirect"

def landing(request):
    return render_to_response("mama_landing.html", context_instance=RequestContext(request))

class CashoutView(View):
    def get(self, request):
        content = request.REQUEST
        code = content.get('code',None)

        openid,unionid = get_user_unionid(code,appid=settings.WEIXIN_APPID,
                                          secret=settings.WEIXIN_SECRET)

        if not valid_openid(openid) or not valid_openid(unionid):
            redirect_url = "https://open.weixin.qq.com/connect/oauth2/authorize?appid=wxc2848fa1e1aa94b5&redirect_uri=http://weixin.huyi.so/m/cashout/&response_type=code&scope=snsapi_base&state=135#wechat_redirect"
            return redirect(redirect_url)
        
        xlmm = XiaoluMama.objects.get(openid=unionid)
        referal_list = XiaoluMama.objects.filter(referal_from=xlmm.mobile)
        cashout_objs = CashOut.objects.filter(xlmm=xlmm.pk,status=CashOut.PENDING)
        data = {"xlmm":xlmm, "cashout": cashout_objs.count(), "referal_list":referal_list}
        
        
        response = render_to_response("mama_cashout.html", data, context_instance=RequestContext(request))
        response.set_cookie("openid",openid)
        response.set_cookie("unionid",unionid)
        return response

    def post(self, request):
        content = request.REQUEST
        unionid = request.COOKIES.get('unionid')
        if not valid_openid(unionid):
            raise Http404
        
        v = content.get("v")
        m = re.match(r'^\d+$', v)

        status = {"code":0, "status":"ok"}
        if m:
            value = int(m.group()) * 100
            try:
                xlmm = XiaoluMama.objects.get(openid=unionid)
                CashOut.objects.create(xlmm=xlmm.pk,value=value)
            except:
                status = {"code":1, "status":"error"}
        else:
            status = {"code":2, "status": "input error"}
            
        return HttpResponse(json.dumps(status),content_type='application/json')



class CashOutList(generics.ListAPIView):
    queryset = CashOut.objects.all().order_by('-created')
    serializer_class = CashOutSerializer
    renderer_classes = (JSONRenderer,)
    filter_fields = ("xlmm",)
    

class CarryLogList(generics.ListAPIView):
    queryset = CarryLog.objects.all().order_by('-carry_date')
    serializer_class = CarryLogSerializer
    renderer_classes = (JSONRenderer,)
    filter_fields = ("xlmm",)
    

from django.conf import settings
from flashsale.pay.options import get_user_unionid
from flashsale.clickcount.models import ClickCount
from flashsale.clickrebeta.models import StatisticsShoppingByDay,StatisticsShopping
from flashsale.mmexam.models import Result

class MamaStatsView(View):
    def get(self, request):
        
        content = request.REQUEST
        code = content.get('code',None)
        
        openid,unionid = get_user_unionid(code,
                                          appid=settings.WEIXIN_APPID,
                                          secret=settings.WEIXIN_SECRET,
                                          request=request)
        
        if not valid_openid(openid):
            redirect_url = "https://open.weixin.qq.com/connect/oauth2/authorize?appid=wxc2848fa1e1aa94b5&redirect_uri=http://weixin.huyi.so/m/m/&response_type=code&scope=snsapi_base&state=135#wechat_redirect"
            return redirect(redirect_url)
        
        service = WeixinUserService(openid,unionId=unionid)
        wx_user = service._wx_user
        
        if not wx_user.isValid():
            return render_to_response("remind.html",{"openid":openid}, 
                                      context_instance=RequestContext(request))
        
        daystr = content.get("day", None)
        today  = datetime.date.today()
        year,month,day = today.year,today.month,today.day
        
        target_date = today
        if daystr:
            year,month,day = daystr.split('-')
            target_date = datetime.date(int(year),int(month),int(day))
            if target_date > today:
                target_date = today
        
        time_from = datetime.datetime(target_date.year, target_date.month, target_date.day)
        time_to = datetime.datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59)
        
        prev_day = target_date - datetime.timedelta(days=1)
        next_day = None
        if target_date < today:
            next_day = target_date + datetime.timedelta(days=1)
        
        exam_pass = False
        result = Result.objects.filter(daili_user=unionid)
        if result.count() > 0:
            exam_pass = result[0].is_Exam_Funished()
        
        mobile = wx_user.mobile
        data   = {}
        try:
            referal_num = XiaoluMama.objects.filter(referal_from=mobile).count()
            xlmm,status = XiaoluMama.objects.get_or_create(openid=unionid)
            if xlmm.mobile  != mobile:
                xlmm.mobile  = mobile
                xlmm.weikefu = wx_user.nickname
                xlmm.save()
            
            mobile_revised = "%s****%s" % (mobile[:3], mobile[-4:])
            agencylevel = AgencyLevel.objects.get(pk=xlmm.agencylevel)
            
            order_num   = 0
            total_value = 0
            carry       = 0

            order_list = StatisticsShopping.objects.filter(linkid=xlmm.pk,shoptime__range=(time_from,time_to))
            order_stat = StatisticsShoppingByDay.objects.filter(linkid=xlmm.pk,tongjidate=target_date)
            if order_stat.count() > 0:
                order_num   = order_stat[0].buyercount
                total_value = order_stat[0].orderamountcount / 100.0
                carry = (order_stat[0].todayamountcount / 100.0) * agencylevel.get_Rebeta_Rate() 
            
            click_state = ClickCount.objects.filter(linkid=xlmm.pk,date=target_date)
            if click_state.count() > 0:
                click_num = click_state[0].valid_num 
            else:
                click_list = Clicks.objects.filter(linkid=xlmm.pk, created__range=(time_from, time_to), isvalid=True)
                click_num  = click_list.values('openid').distinct().count()
                
            click_price = agencylevel.get_Click_Price(order_num) / 100
            click_pay   = click_price * click_num 

            data = {"mobile":mobile_revised, "click_num":click_num, "xlmm":xlmm,
                    "order_num":order_num, "order_list":order_list, "pk":xlmm.pk,"exam_pass":exam_pass,
                    "total_value":total_value, "carry":carry, "agencylevel":agencylevel,
                    "target_date":target_date, "prev_day":prev_day, "next_day":next_day,
                    "click_price":click_price, "click_pay":click_pay, "referal_num":referal_num}
        except Exception,exc:
            logger.error(exc.message,exc_info=True)
        
        response = render_to_response("mama_stats.html", data, context_instance=RequestContext(request))
        response.set_cookie("sunionid",unionid)
        response.set_cookie("sopenid",openid)
        return response


class StatsView(View):
    
    def getUserName(self,uid):
        try:
            return User.objects.get(pk=uid).username
        except:
            return 'none'
        
    def get(self,request):
        content = request.REQUEST
        daystr = content.get("day", None)
        today = datetime.date.today()
        year,month,day = today.year,today.month,today.day

        target_date = today
        if daystr:
            year,month,day = daystr.split('-')
            target_date = datetime.date(int(year),int(month),int(day))
            if target_date > today:
                target_date = today

        time_from = datetime.datetime(target_date.year, target_date.month, target_date.day)
        time_to = datetime.datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59)
        
        prev_day = target_date - datetime.timedelta(days=1)
        next_day = None
        if target_date < today:
            next_day = target_date + datetime.timedelta(days=1)

        pk = content.get('pk','6')
        mama_list = XiaoluMama.objects.filter(manager=pk)
        mama_managers = XiaoluMama.objects.values('manager').distinct()
        manager_ids   = [m.get('manager') for m in mama_managers if m]
        managers      = User.objects.filter(id__in=manager_ids)
        data = []

        for mama in mama_list:
            buyer_num = 0
            order_num = 0
            click_num = 0
            user_num  = 0
            weikefu   = mama.weikefu
            mobile    = mama.mobile
            agencylevel = mama.agencylevel
            username  = self.getUserName(mama.manager)

            day_stats = StatisticsShoppingByDay.objects.filter(linkid=mama.pk,tongjidate=target_date)
            if day_stats.count() > 0:
                buyer_num = day_stats[0].buyercount
                order_num = day_stats[0].ordernumcount

            click_counts = ClickCount.objects.filter(linkid=mama.pk, date=target_date)
            if click_counts.count() > 0:
                click_num = click_counts[0].click_num
                user_num = click_counts[0].user_num
            else:
                click_list = Clicks.objects.filter(linkid=mama.pk, created__gt=time_from, created__lt=time_to)
                click_num  = click_list.count()
                openid_list = click_list.values('openid').distinct()
                user_num = openid_list.count()

            data_entry = {"mobile":mobile[-4:], "weikefu":weikefu,
                          "agencylevel":agencylevel,'username':username,
                          "click_num":click_num, "user_num":user_num,
                          "buyer_num":buyer_num,"order_num":order_num}
            data.append(data_entry)
            
        return render_to_response("stats.html", 
                                  {'pk':int(pk),"data":data,"managers":managers,"prev_day":prev_day,
                                   "target_date":target_date, "next_day":next_day}, 
                                  context_instance=RequestContext(request))

from . import tasks

def logclicks(request, linkid):
    content = request.REQUEST
    code = content.get('code',None)

    openid,unionid = get_user_unionid(code,appid=settings.WEIXIN_APPID,
                                          secret=settings.WEIXIN_SECRET)

    if not valid_openid(openid):
        redirect_url = "https://open.weixin.qq.com/connect/oauth2/authorize?appid=wxc2848fa1e1aa94b5&redirect_uri=http://weixin.huyi.so/m/%d/&response_type=code&scope=snsapi_base&state=135#wechat_redirect" % int(linkid)
        return redirect(redirect_url)

    tasks.task_Create_Click_Record.s(linkid, openid)()

    return redirect(SHOPURL)


from django.shortcuts import get_object_or_404
from django.forms import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder

def chargeWXUser(request,pk):
    
    result = {}
    employee = request.user

    xiaolumm = get_object_or_404(XiaoluMama,pk=pk)
   
    charged = XiaoluMama.objects.charge(xiaolumm, employee)
    if not charged:
        result ={'code':1,'error_response':u'已经被接管'}
            
    if charged :
        result ={'success':True}
        
        log_action(request.user.id,xiaolumm,CHANGE,u'接管用户')
    
    return HttpResponse( json.dumps(result),content_type='application/json')


class XiaoluMamaModelView(View):
    """ 微信接收消息接口 """
    
    def post(self,request ,pk):
        
        content    = request.REQUEST
        user_group_id = content.get('user_group_id')
        
        xlmm = get_object_or_404(XiaoluMama,pk=pk)
        xlmm.user_group_id = user_group_id
        xlmm.save()
        
        user_dict = {'code':0,'response_content':
                     model_to_dict(xlmm, fields=['id','user_group','charge_status'])}
        
        return HttpResponse(json.dumps(user_dict,cls=DjangoJSONEncoder),
                            mimetype="application/json")


from flashsale.pay.models import SaleTrade,Customer
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def cash_Out_Verify(request):
    '''提现审核方法'''
    '''buyer_id 手机 可用现金  体现金额  小鹿钱包消费额
    '''
    data = []
    cashouts_status_is_pending = CashOut.objects.filter(status='pending').order_by('-created')[:80]
    today = datetime.datetime.today()
    day_from = today-datetime.timedelta(days=30)
    day_to = today
    
    for cashout_status_is_pending in cashouts_status_is_pending:
        id = cashout_status_is_pending.id
        xlmm = cashout_status_is_pending.xlmm
        value = cashout_status_is_pending.value/100.0
        status = cashout_status_is_pending.status
        xiaolumama = XiaoluMama.objects.get(pk=xlmm)
        
        # 点击数
        click_nums = 0
        clickcounts = ClickCount.objects.filter(date__gt=day_from, date__lt=day_to, linkid=xlmm)
        for clickcount in clickcounts:
            click_nums = click_nums + clickcount.valid_num

        # 订单数
        shoppings = StatisticsShopping.objects.filter(shoptime__gt=day_from, shoptime__lt=day_to, linkid=xlmm)
        shoppings_count = shoppings.count()

        mobile = xiaolumama.mobile
        cash = xiaolumama.cash/100.0
        
        pay_saletrade = []
        sale_customers = Customer.objects.filter(unionid=xiaolumama.openid)
        if sale_customers.count() > 0:
            customer = sale_customers[0]
            pay_saletrade = SaleTrade.objects.filter(buyer_id=customer.id,
                                                 channel=SaleTrade.WALLET,
                                                 status=SaleTrade.TRADE_FINISHED)
        payment = 0
        for pay in pay_saletrade:
            payment = payment + pay.payment
        
        x_choice = 0 
        cashout_flag = False
        if click_nums >= 150 or shoppings_count >= 6:
            cashout_flag = True
            x_choice = 100.00
        else:
            x_choice = 130.00
        mony_without_pay = cash + payment # 从未消费情况下的金额
        could_cash_out = mony_without_pay - x_choice # 可提现金额
        if could_cash_out < 0:  # 如果可提现金额 小于 0  则设置 成为 0
            could_cash_out = 0
        if could_cash_out >0:
            cashout_flag = True

        data_entry = {'id':id,'xlmm':xlmm,'value':value,'status':status,'mobile':mobile,'cash':cash,'payment':payment,
                      'shoppings_count':shoppings_count,'click_nums':click_nums,'cashout_flag':cashout_flag,'could_cash_out':could_cash_out}
        data.append(data_entry)

    return render_to_response("mama_cashout_verify.html", {"data":data}, context_instance=RequestContext(request))

from django.db.models import F

def cash_modify(request, data):
    cash_id = int(data)
    if cash_id:
        cashout = CashOut.objects.get(pk=cash_id)
        xiaolumama = XiaoluMama.objects.get(pk=cashout.xlmm)
        if xiaolumama.cash >= cashout.value and cashout.status == 'pending':
            today_dt = datetime.date.today()
            CarryLog.objects.get_or_create(xlmm=xiaolumama.id,
                                         order_num=cash_id,
                                         log_type=CarryLog.CASH_OUT,
                                         value=cashout.value,
                                         carry_date=today_dt,
                                         carry_type=CarryLog.CARRY_OUT,
                                         status=CarryLog.CONFIRMED)
  
            # 改变金额
            xiaolumama.cash = F('cash') - cashout.value
            # 改变状态
            cashout.status = 'approved'
            cashout.approve_time = datetime.datetime.now()
            cashout.save()
            xiaolumama.save()
            return HttpResponse('ok')
        else:
            return HttpResponse('reject')# 拒绝操作数据库
    return HttpResponse('server error')

def cash_reject(request, data):
    cash_id = int(data)
    if cash_id:
        cashout = CashOut.objects.get(pk=cash_id)
        cashout.status = 'rejected'
        cashout.save()
        return HttpResponse('ok')
    else:
        return HttpResponse('reject')# 拒绝操作数据库
    return HttpResponse('server error')
