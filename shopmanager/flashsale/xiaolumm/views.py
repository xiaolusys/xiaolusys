#-*- coding:utf-8 -*-

import json
from django.http import HttpResponse,Http404
from django.shortcuts import redirect,render_to_response
from django.views.generic import View
from django.template import RequestContext
from django.contrib.auth.models import User
from django.db.models import Sum

from shopapp.weixin.views import get_user_openid,valid_openid
from shopapp.weixin.models import WXOrder
from shopapp.weixin.service import WeixinUserService
from shopback.base import log_action, ADDITION, CHANGE

from models import Clicks, XiaoluMama, AgencyLevel, CashOut, CarryLog, UserGroup
from flashsale.pay.models import SaleTrade,Customer,SaleRefund

from serializers import CashOutSerializer,CarryLogSerializer
from rest_framework import generics
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response


import logging
logger = logging.getLogger('django.request')


import datetime, re


SHOPURL = "http://mp.weixin.qq.com/bizmall/mallshelf?id=&t=mall/list&biz=MzA5NTI1NjYyNg==&shelf_id=2&showwxpaytitle=1#wechat_redirect"

def landing(request):
    return render_to_response("mama_landing.html", context_instance=RequestContext(request))

def get_xlmm_cash_iters(xlmm,cash_outable=False):
    
    cash = xlmm.cash / 100.0
    pay_saletrade = []
    sale_customers = Customer.objects.filter(unionid=xlmm.openid)
    if sale_customers.count() > 0:
        customer = sale_customers[0]
        pay_saletrade = SaleTrade.objects.filter(buyer_id=customer.id,
                                             channel=SaleTrade.WALLET,
                                             status__in=SaleTrade.INGOOD_STATUS)
    payment = 0
    for pay in pay_saletrade:
        sale_orders = pay.sale_orders.filter(refund_status__gt=SaleRefund.REFUND_REFUSE_BUYER)
        total_refund = sale_orders.aggregate(total_refund=Sum('refund_fee')).get('total_refund') or 0
        payment = payment + pay.payment - total_refund

    x_choice = 0
    if cash_outable:
        x_choice = 100.00
    else:
        x_choice = 130.00
    mony_without_pay = cash + payment # 从未消费情况下的金额
    leave_cash_out = mony_without_pay - x_choice   # 可提现金额

    could_cash_out = cash
    if leave_cash_out < cash:
        could_cash_out = leave_cash_out

    if could_cash_out < 0 :
        could_cash_out = 0
    
    return (cash,payment,could_cash_out)


class CashoutView(View):
    def get(self, request):
        content = request.REQUEST
        code = content.get('code',None)

        openid,unionid = get_user_unionid(code,appid=settings.WEIXIN_APPID,
                                          secret=settings.WEIXIN_SECRET,
                                          request=request)

        if not valid_openid(openid) or not valid_openid(unionid):
            redirect_url = "https://open.weixin.qq.com/connect/oauth2/authorize?appid=wxc2848fa1e1aa94b5&redirect_uri=http://weixin.huyi.so/m/cashout/&response_type=code&scope=snsapi_base&state=135#wechat_redirect"
            return redirect(redirect_url)
        
        xlmm = XiaoluMama.objects.get(openid=unionid)
        referal_list = XiaoluMama.objects.filter(referal_from=xlmm.mobile)
        cashout_objs = CashOut.objects.filter(xlmm=xlmm.pk,status=CashOut.PENDING)
        
#         day_to   = datetime.datetime.now()
#         day_from = day_to - datetime.timedelta(days=30)
        # 点击数
        clickcounts = ClickCount.objects.filter(linkid=xlmm.id)
        click_nums  = clickcounts.aggregate(total_count=Sum('valid_num')).get('total_count') or 0

        # 订单数
        shoppings = StatisticsShopping.objects.filter(linkid=xlmm.id)
        shoppings_count = shoppings.count()
        
        cash_outable = click_nums >= 150 or shoppings_count >= 6
            
        cash, payment, could_cash_out = get_xlmm_cash_iters(xlmm, cash_outable=cash_outable)
        
        data = {"xlmm":xlmm, "cashout": cashout_objs.count(), 
                "referal_list":referal_list ,"could_cash_out":int(could_cash_out)}
        
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

from flashsale.clickcount.tasks import CLICK_ACTIVE_START_TIME, CLICK_MAX_LIMIT_DATE  

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
        
        target_date = datetime.date.today()
        yesterday   = target_date - datetime.timedelta(days=1)
        time_from = datetime.datetime(target_date.year, target_date.month, target_date.day)
        time_to = datetime.datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59)
        
        mobile = wx_user.mobile
        data   = {}
        try:
            referal_num = XiaoluMama.objects.filter(referal_from=mobile).count()
            xlmm,state  = XiaoluMama.objects.get_or_create(openid=unionid)
            if xlmm.mobile  != mobile:
                xlmm.mobile  = mobile
                xlmm.weikefu = xlmm.weikefu or wx_user.nickname
                xlmm.save()
            
            if xlmm.status == XiaoluMama.FROZEN:
                return render_to_response("mama_404.html")
            
            mobile_revised = "%s****%s" % (mobile[:3], mobile[-4:])
            
            mm_clogs = CarryLog.objects.filter(xlmm=xlmm.id)
            pending_value = mm_clogs.filter(status=CarryLog.PENDING).aggregate(total_value=Sum('value')).get('total_value') or 0 
            
            total_income = mm_clogs.filter(carry_type=CarryLog.CARRY_IN,status=CarryLog.CONFIRMED).aggregate(total_value=Sum('value')).get('total_value') or 0
            total_pay    = mm_clogs.filter(carry_type=CarryLog.CARRY_OUT,status=CarryLog.CONFIRMED).aggregate(total_value=Sum('value')).get('total_value') or 0
            
            yest_income = mm_clogs.filter(carry_type=CarryLog.CARRY_IN,carry_date=yesterday).aggregate(total_value=Sum('value')).get('total_value') or 0
            yest_pay    = mm_clogs.filter(carry_type=CarryLog.CARRY_OUT,carry_date=yesterday).aggregate(total_value=Sum('value')).get('total_value') or 0
            
            pending_value = pending_value / 100.0
            total_income  = total_income / 100.0
            total_pay     = total_pay / 100.0
            yest_income   = yest_income / 100.0
            yest_pay      = yest_pay / 100.0
            
            order_num   = 0
            order_stat = StatisticsShoppingByDay.objects.filter(linkid=xlmm.pk,tongjidate=target_date)
            if order_stat.count() > 0:
                order_num   = order_stat[0].buyercount

            click_list = Clicks.objects.filter(linkid=xlmm.pk, click_time__range=(time_from, time_to), isvalid=True)
            click_num  = click_list.values('openid').distinct().count()
                    
            #设置最高有效最高点击上限
            max_click_count = xlmm.get_Mama_Max_Valid_Clickcount(order_num)
            if time_from.date() >= CLICK_MAX_LIMIT_DATE:
                click_num = min(max_click_count,click_num)
                
            referal_mm = 0
#             if xlmm.progress != XiaoluMama.PASS :
#                 if xlmm.referal_from:
#                     referal_mamas = XiaoluMama.objects.filter(mobile=xlmm.referal_from)
#                     if referal_mamas.count() > 0:
#                         referal_mm = referal_mamas[0].id
#                 else:
#                     referal_mm = 1
                
            data = {"mobile":mobile_revised, "click_num":click_num, "xlmm":xlmm,
                    'referal_mmid':referal_mm,"order_num":order_num,  "pk":xlmm.pk,
                    'pending_value':pending_value,"referal_num":referal_num,
                    'total_income':total_income,'total_pay':total_pay,
                    'yest_income':yest_income,'yest_pay':yest_pay}
            
        except Exception,exc:
            logger.error(exc.message,exc_info=True)
        
        response = render_to_response("mama_stats.html", data, context_instance=RequestContext(request))
        response.set_cookie("sunionid",unionid)
        response.set_cookie("sopenid",openid)
        return response
    
class MamaIncomeDetailView(View):
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
        
        active_start = CLICK_ACTIVE_START_TIME.date() == time_from.date()
        
        prev_day = target_date - datetime.timedelta(days=1)
        next_day = None
        if target_date < today:
            next_day = target_date + datetime.timedelta(days=1)
        
        exam_pass = False
        result = Result.objects.filter(daili_user=unionid)
        if result.count() > 0:
            exam_pass = result[0].is_Exam_Funished()
            
        data   = {}
        try:
            xlmm,state  = XiaoluMama.objects.get_or_create(openid=unionid)
            if xlmm.status == XiaoluMama.FROZEN:
                return render_to_response("mama_404.html")
            
            order_num   = 0
            total_value = 0
            carry       = 0

            order_list = StatisticsShopping.normal_objects.filter(linkid=xlmm.pk,shoptime__range=(time_from,time_to))
            order_stat = StatisticsShoppingByDay.objects.filter(linkid=xlmm.pk,tongjidate=target_date)
            carry_confirm = False
            if order_stat.count() > 0:
                order_num   = order_stat[0].buyercount
                total_value = order_stat[0].orderamountcount / 100.0
                carry = (order_stat[0].todayamountcount / 100.0) * xlmm.get_Mama_Order_Rebeta_Rate()
                carry_confirm = order_stat[0].carry_Confirm()
            
            click_state = ClickCount.objects.filter(linkid=xlmm.pk,date=target_date)
            click_price  = xlmm.get_Mama_Click_Price(order_num) / 100
            
            click_num    = 0 
            click_pay    = 0 
            ten_click_num   = 0 
            ten_click_price = click_price + 0.3 
            ten_click_pay   = 0 
            if not active_start:
                if click_state.count() > 0:
                    click_num = click_state[0].valid_num
                else:
                    click_qs   = Clicks.objects.filter(linkid=xlmm.pk, isvalid=True)
                    click_list = Clicks.objects.filter(linkid=xlmm.pk, click_time__range=(time_from, time_to), isvalid=True)
                    click_num  = click_list.values('openid').distinct().count()
                    
                #设置最高有效最高点击上限
                max_click_count = xlmm.get_Mama_Max_Valid_Clickcount(order_num)
                if time_from.date() >= CLICK_MAX_LIMIT_DATE:
                    click_num = min(max_click_count,click_num)
                
                click_pay   = click_price * click_num 
                
            else:
                click_qs   = Clicks.objects.filter(linkid=xlmm.pk, isvalid=True)
                click_num  = click_qs.filter(click_time__range=(datetime.datetime(2015,6,15), 
                                                                datetime.datetime(2015,6,15,10,0,0))
                                             ).values('openid').distinct().count()

                ten_click_num = click_qs.filter(click_time__range=(datetime.datetime(2015,6,15,10), 
                                                                   datetime.datetime(2015,6,15,23,59,59))
                                                ).values('openid').distinct().count()
                                                
                #设置最高有效最高点击上限
                max_click_count = xlmm.get_Mama_Max_Valid_Clickcount(order_num)
                if time_from.date() >= CLICK_MAX_LIMIT_DATE:
                    click_num = min(max_click_count,click_num)
                    ten_click_num = min(max_click_count,ten_click_num)
                
                click_pay  = click_num * click_price                              
                ten_click_pay = ten_click_num * ten_click_price
                
            data = { "xlmm":xlmm,"pk":xlmm.pk,
                    "order_num":order_num, "order_list":order_list, 
                    "exam_pass":exam_pass,"total_value":total_value,
                    "carry":carry, 'carry_confirm':carry_confirm,
                    "target_date":target_date,"prev_day":prev_day, "next_day":next_day,
                    'active_start':active_start,"click_num":click_num,
                    "click_price":click_price, "click_pay":click_pay,"ten_click_num":ten_click_num,
                    "ten_click_price":ten_click_price, "ten_click_pay":ten_click_pay}
            
        except Exception,exc:
            logger.error(exc.message,exc_info=True)
        
        response = render_to_response("mama_income.html", data, context_instance=RequestContext(request))
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
                click_list = Clicks.objects.filter(linkid=mama.pk, click_time__range=(time_from,time_to))
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

    click_time = datetime.datetime.now()
    tasks.task_Create_Click_Record.s(linkid, openid, click_time)()

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


from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def cash_Out_Verify(request, id, xlmm):
    '''提现审核方法'''
    '''buyer_id 手机 可用现金  体现金额  小鹿钱包消费额
    '''
    data = []
#     cashouts_status_is_pending = CashOut.objects.filter(status='pending').order_by('-created')
#     today = datetime.datetime.today()
#     day_from = today-datetime.timedelta(days=30)
#     day_to = today

    cashout_status_is_pending = CashOut.objects.get(id=id)

    # for cashout_status_is_pending in cashouts_status_is_pending:
    # xlmm = cashout_status_is_pending.xlmm
    value = cashout_status_is_pending.value/100.0
    status = cashout_status_is_pending.status
    xiaolumama = XiaoluMama.objects.get(pk=xlmm)
    
    clickcounts = ClickCount.objects.filter(linkid=xlmm)
    click_nums  = clickcounts.aggregate(total_count=Sum('valid_num')).get('total_count') or 0

    # 订单数
    shoppings = StatisticsShopping.objects.filter(linkid=xlmm)
    shoppings_count = shoppings.count()

    mobile = xiaolumama.mobile
    cash_outable = click_nums >= 150 or shoppings_count >= 6
        
    cash, payment, could_cash_out = get_xlmm_cash_iters(xiaolumama, cash_outable=cash_outable)

    data_entry = {'id':id,'xlmm':xlmm,'value':value,'status':status,'mobile':mobile,'cash':cash,'payment':payment,
                  'shoppings_count':shoppings_count,'click_nums':click_nums,'could_cash_out':could_cash_out}
    data.append(data_entry)

    return render_to_response("mama_cashout_verify.html", {"data":data}, context_instance=RequestContext(request))

from django.db import transaction
from django.db.models import F
from django.conf import settings
from flashsale.pay.models import Envelop
from shopapp.weixin.models import WeixinUnionID

@transaction.commit_on_success
def cash_modify(request, data):
    cash_id = int(data)
    if cash_id:
        cashout = CashOut.objects.get(pk=cash_id)
        xiaolumama = XiaoluMama.objects.get(pk=cashout.xlmm)
        cash_iters = get_xlmm_cash_iters(xiaolumama, cash_outable=True)
        
        if cash_iters[2] * 100 >= cashout.value and cashout.status == 'pending':
            today_dt = datetime.date.today()
            
            pre_cash = xiaolumama.cash
            # 改变金额
            urows = XiaoluMama.objects.filter(pk=cashout.xlmm,cash__gte=cashout.value).update(cash=F('cash')-cashout.value)
            if urows == 0:
                return HttpResponse('reject')
            # 改变状态
            cashout.status = 'approved'
            cashout.approve_time = datetime.datetime.now()
            cashout.save()
            
            CarryLog.objects.get_or_create(xlmm=xiaolumama.id,
                                         order_num=cash_id,
                                         log_type=CarryLog.CASH_OUT,
                                         value=cashout.value,
                                         carry_date=today_dt,
                                         carry_type=CarryLog.CARRY_OUT,
                                         status=CarryLog.CONFIRMED)
            
            wx_union = WeixinUnionID.objects.get(app_key=settings.WXPAY_APPID,unionid=xiaolumama.openid)
            
            mama_memo = u"小鹿妈妈编号:{0},提现前:{1}"
            Envelop.objects.get_or_create(referal_id=cashout.id,
                                          amount=cashout.value,
                                          recipient=wx_union.openid,
                                          platform=Envelop.WXPUB,
                                          subject=Envelop.CASHOUT,
                                          status=Envelop.WAIT_SEND,
                                          receiver=xiaolumama.id,
                                          body=u'一份耕耘，一份收获，谢谢你的努力！',
                                          description=mama_memo.format(str(xiaolumama.id),pre_cash))
            
            log_action(request.user.id,cashout,CHANGE,u'提现审核通过')
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


from django.db.models import Avg,Count,Sum

@csrf_exempt
def stats_summary(request):
    #  根据日期查看每个管理人员 所管理的所有代理的点击情况和转化情况
    data = []
    content = request.REQUEST
    daystr = content.get("day", None)
    today = datetime.date.today()
    year,month,day = today.year,today.month,today.day

    target_date = today
    if daystr:
        year,month,day = daystr.split('-')
        target_date = datetime.date(int(year),int(month),int(day))
        if target_date >= today:
            target_date = today

    time = datetime.datetime(target_date.year, target_date.month, target_date.day)

    prev_day = target_date - datetime.timedelta(days=1)
    next_day = None
    if target_date < today:
        next_day = target_date + datetime.timedelta(days=1)

    xiaolumamas = XiaoluMama.objects.exclude(manager=0).values('manager').distinct()

    for xlmm_manager in xiaolumamas:
        xiaolumama_manager2 = xlmm_manager['manager']
        sum_click_num = 0
        sum_click_valid = 0
        sum_user_num = 0
        active_num = 0
        clickcounts = ClickCount.objects.filter(username=xiaolumama_manager2, date=time)
        mamas_l2 = XiaoluMama.objects.filter(agencylevel=2,manager=xiaolumama_manager2) # 代理类别为2的妈妈
        xlmm_num = mamas_l2.count() # 这个管理员下面的妈妈数量
        
        for clickcount in clickcounts:
            sum_click_valid  = sum_click_valid + clickcount.valid_num
            sum_click_num = sum_click_num + clickcount.click_num
            sum_user_num = sum_user_num + clickcount.user_num

            if clickcount.user_num > 4 and clickcount.agencylevel > 1:
                active_num = active_num + 1
                
        if xlmm_num == 0:
            activity = 0
        else:
            activity = round(float(active_num)/xlmm_num,3)
        # '管理员',xiaolumama_manager2
        # '点击数量 ' ,sum_click_num
        # '点击人数',sum_user_num
        xiaolumms = XiaoluMama.objects.filter(manager=xiaolumama_manager2)
        sum_buyercount = 0
        sum_ordernumcount = 0
        for xiaolumm in xiaolumms:
            shoppings = StatisticsShoppingByDay.objects.filter(linkid=xiaolumm.id, tongjidate=time)
            for shopping in shoppings:
                sum_buyercount = sum_buyercount + shopping.buyercount
                sum_ordernumcount = sum_ordernumcount + shopping.ordernumcount
        # '购买人数',sum_buyercount,'订单数量',sum_ordernumcount
        try:
            username = User.objects.get(id=xiaolumama_manager2).username
        except:
            username = 'error.manager'

        if sum_user_num == 0 :
            conversion_rate = 0

        else:
            conversion_rate = float(sum_buyercount)/sum_user_num # 转化率等于 购买人数 除以 点击数

            conversion_rate =  round(float(conversion_rate), 3)
        data_entry = {"username": username,"sum_ordernumcount":sum_ordernumcount,
                      "sum_buyercount":sum_buyercount,
                      "uv_summary":sum_user_num,"pv_summary":sum_click_num,"conversion_rate":conversion_rate,
                      "xlmm_num":xlmm_num,"activity":activity,'sum_click_valid':sum_click_valid}
        data.append(data_entry)

    return render_to_response("stats_summary.html", {"data": data,"prev_day":prev_day,
                              "target_date":target_date, "next_day":next_day}, 
                              context_instance=RequestContext(request))



###################### 妈妈审核功能

from flashsale.pay.models_user import Customer
from flashsale.pay.models import SaleTrade,SaleOrder

def get_Deposit_Trade(openid):
    try:
        customer = Customer.objects.get(unionid=openid)  # 找到对应的unionid 等于小鹿妈妈openid的顾客

        sale_orders = SaleOrder.objects.filter(outer_id='RMB100', payment=100, status=SaleOrder.WAIT_SELLER_SEND_GOODS,
                                     sale_trade__buyer_id=customer.id,
                                     sale_trade__status=SaleTrade.WAIT_SELLER_SEND_GOODS)

        if sale_orders.count() == 0:
            return None
        return sale_orders[0].sale_trade  # 返回订单
    except:
        return None


@csrf_exempt
def mama_Verify(request):
    # 审核妈妈成为代理的功能
    data = []
    xlmms = XiaoluMama.objects.filter(manager=0)  # 找出没有被接管的妈妈
    
    default_code = ['BLACK','NORMAL']
    default_code.append(request.user.username)
    user_groups = UserGroup.objects.filter(code__in=default_code)
    
    for xlmm in xlmms:
        trade = get_Deposit_Trade(xlmm.openid)
        if trade:
            id = xlmm.id
            mobile = xlmm.mobile
            weikefu = xlmm.weikefu
            referal_from = xlmm.referal_from
            data_entry = {"id": id, "mobile": mobile, "sum_trade": "YES","weikefu":weikefu,'referal_from':referal_from,'cat_list':user_groups}
            data.append(data_entry)
    user = request.user.username
    return render_to_response("mama_verify.html", {'data': data,'user':user}, context_instance=RequestContext(request))


@csrf_exempt
def mama_Verify_Action(request):
    mama_id = request.GET.get('id')
    referal_mobile = request.GET.get('tuijianren','').strip()
    weikefu = request.GET.get('weikefu')
    user_group =int(request.GET.get('group'))

    xlmm = XiaoluMama.objects.get(id=mama_id)

    customer = Customer.objects.get(unionid=xlmm.openid)  # 找到对应的unionid 等于小鹿妈妈openid的顾客
    sale_orders = SaleOrder.objects.filter(outer_id='RMB100', payment=100, status=SaleOrder.WAIT_SELLER_SEND_GOODS,
                                 sale_trade__buyer_id=customer.id,
                                 sale_trade__status=SaleTrade.WAIT_SELLER_SEND_GOODS)
    
    if sale_orders.count() == 0:
        return HttpResponse('reject')
    
    referal_mama = None
    if referal_mobile:
        try:
            referal_mama = XiaoluMama.objects.normal_queryset.get(mobile=referal_mobile)
            if referal_mama.referal_from == xlmm.mobile or referal_mobile == xlmm.mobile:
                return HttpResponse('cross')
        except XiaoluMama.DoesNotExist:
            return HttpResponse('unfound')
        except XiaoluMama.MultipleObjectsReturned:
            return HttpResponse('multiple')
    
    order = sale_orders[0]
    order.status = SaleOrder.TRADE_FINISHED # 改写订单明细状态
    order.save()

    trade = order.sale_trade
    trade.status = SaleTrade.TRADE_FINISHED  # 改写 订单状态
    trade.save()
    
    diposit_cash = 13000
    recruit_rebeta = 5000
    # 修改小鹿妈妈的记录
    log_tp = CarryLog.objects.get_or_create(xlmm=xlmm.id,
                                   order_num=trade.id,
                                   log_type=CarryLog.DEPOSIT,
                                   value=diposit_cash,
                                   buyer_nick= weikefu,
                                   carry_type=CarryLog.CARRY_IN,
                                   status=CarryLog.CONFIRMED)
    if not log_tp[1]:
        return HttpResponse('reject')
    
    xlmm.cash = F('cash') + diposit_cash # 分单位
    xlmm.referal_from = referal_mobile
    xlmm.agencylevel = 2
    xlmm.charge_status = XiaoluMama.CHARGED
    xlmm.manager = request.user.id
    xlmm.weikefu = weikefu
    xlmm.charge_time = datetime.datetime.now()
    xlmm.user_group_id = user_group
    xlmm.save()
    
    if referal_mama:
        CarryLog.objects.get_or_create(xlmm=referal_mama.id,
                                       order_num=xlmm.id,
                                        log_type=CarryLog.MAMA_RECRUIT,
                                        value=recruit_rebeta,
                                        buyer_nick=referal_mama.weikefu,
                                        carry_type=CarryLog.CARRY_IN,
                                        status=CarryLog.PENDING)
        
    return HttpResponse('ok')



# 小鹿妈妈代理的点击前50 ，每天，上周，前四周
from view_top50 import xlmm_Click_Top_By_Day, xlmm_Order_Top_By_Day, xlmm_Conversion_Top_By_Week,\
    xlmm_Click_Top_By_Week, xlmm_Order_Top_By_Week, xlmm_Click_Top_By_Month, xlmm_Order_Top_By_Month,\
    xlmm_Convers_Top_By_Month


@csrf_exempt
def xlmm_Click_Top(request):
    # 过滤出昨天的点击前50名
    data, date_dict = xlmm_Click_Top_By_Day(request)
    return render_to_response("top_click_50.html", {'data': data, 'date_dict': date_dict},
                              context_instance=RequestContext(request))


@csrf_exempt
def xlmm_Order_Top(request):
    # 过滤出昨天的订单前50名
    data, date_dict = xlmm_Order_Top_By_Day(request)
    return render_to_response("top_order_50.html", {'data': data, 'date_dict': date_dict},
                              context_instance=RequestContext(request))


@csrf_exempt
def xlmm_Conversion_Top(request):
    data, date_dict = xlmm_Conversion_Top_By_Week(request)
    return render_to_response("top_convers.html", {'data': data, 'date_dict': date_dict},
                              context_instance=RequestContext(request))


@csrf_exempt
def xlmm_Click_Top_Week(request):
    data, date_dict = xlmm_Click_Top_By_Week(request)
    return render_to_response("top_click_50_week.html", {'data': data, 'date_dict': date_dict},
                              context_instance=RequestContext(request))


@csrf_exempt
def xlmm_Order_Top_Week(request):
    data, date_dict = xlmm_Order_Top_By_Week(request)
    return render_to_response("top_order_50_week.html", {'data': data, 'date_dict': date_dict},
                              context_instance=RequestContext(request))


@csrf_exempt
def xlmm_Click_Top_Month(request):
    data, date_dict = xlmm_Click_Top_By_Month(request)
    return render_to_response("top_click_50_month.html", {'data': data, 'date_dict': date_dict},
                              context_instance=RequestContext(request))


@csrf_exempt
def xlmm_Order_Top_Month(request):
    data, date_dict = xlmm_Order_Top_By_Month(request)
    return render_to_response("top_order_50_month.html", {'data': data, 'date_dict': date_dict},
                              context_instance=RequestContext(request))


@csrf_exempt
def xlmm_Convers_Top_Month(request):
    data, date_dict = xlmm_Convers_Top_By_Month(request)
    return render_to_response("top_convers_50_month.html", {'data': data, 'date_dict': date_dict},
                              context_instance=RequestContext(request))


