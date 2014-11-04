#-*- encoding:utf-8 -*-
import json
import datetime
from django.http import HttpResponse
from django.conf import settings
from django.db.models import F
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django.template import RequestContext 
from django.shortcuts import render_to_response

from shopback.base.authentication import login_required_ajax
from shopapp.weixin.views import WeiXinUser,VipCode,get_user_openid
from .models import WeixinUserPicture,WeixinUserAward
from .tasks import NotifyReferalAwardTask
from shopapp.signals import weixin_referal_signal
from django.shortcuts import redirect


@csrf_exempt
@login_required_ajax
def picture_review(request):
    
    content = request.REQUEST
    
    rows    =  WeixinUserPicture.objects.filter(id = content.get('pid'))\
                .update(status=WeixinUserPicture.COMPLETE)
    
    return  HttpResponse(json.dumps({'code':(1,0)[rows]}),mimetype="application/json")


class AwardView(View):
    
    def post(self, request):
        content    = request.REQUEST
        award_val  = content.get('award_val','')
#        user_openid = 'oMt59uJJBoNRC7Fdv1b5XiOAngdU'
        user_openid = request.COOKIES.get('openid')
        try:
            wx_user = WeiXinUser.objects.get(openid=user_openid)
            referal_from_openid = wx_user.referal_from_openid
            
            wx_award,state = WeixinUserAward.objects.get_or_create(user_openid=user_openid)
            if award_val.isdigit() and award_val in ('1','2','3','4','5','6'):
                wx_award.award_val  = award_val
                wx_award.referal_from_openid  = referal_from_openid
                wx_award.save()
                
                weixin_referal_signal.send(sender=WeixinUserAward,
                                           user_openid=user_openid,
                                           referal_from_openid=referal_from_openid)
                
                rep_json = {'success':True}
            elif wx_award.is_receive:
                rep_json = {'success':False,'err_msg':u'不能重复提交'}
            else:
                rep_json = {'success':False,'err_msg':u'选择奖励物品不对'}
        except:
            rep_json = {'success':False,'err_msg':u'系统错误，请联系管理员'}
            
        return HttpResponse(json.dumps(rep_json),mimetype="application/json") 
    
    
class AwardNotifyView(View):
    def get(self, request):
        content = request.REQUEST
        code = content.get('code')
        user_openid = get_user_openid(request, code)
        
        response = render_to_response('weixin/sales/gift.html', 
                                      context_instance=RequestContext(request))
        response.set_cookie("openid",user_openid)
        return response

    def post(self, request):

        content = request.REQUEST
        award_val = content.get('award_val')
        user_openid = request.COOKIES.get('openid')
        notify_num = 0
        
        
        wx_award,state = WeixinUserAward.objects.get_or_create(user_openid=user_openid)

        referal_ships = WeiXinUser.objects.filter(referal_from_openid=user_openid)
        
        if referal_ships.count() > 0 and not wx_award.is_share:
            notify_num = referal_ships.count()
            NotifyReferalAwardTask().delay(user_openid) 
            
            wx_award.is_share     = True
            wx_award.award_val    = award_val
            wx_award.remind_time  = datetime.datetime.now()
            wx_award.remind_count = 0
            wx_award.save()
                
        wx_user = WeiXinUser.objects.get(openid=user_openid)
        return redirect("/weixin/sampleads/%s/"%wx_user.pk)
        
        rep_json = {'success':False,'notify_num':0}
            
        return  HttpResponse(json.dumps(rep_json),mimetype="application/json")  
    
    
class AwardRemindView(View):
    
    def post(self, request):
        
        try:
            content = request.REQUEST
            code  = content.get('code')
            fcode = content.get('fcode')
#            user_openid = 'oMt59uJJBoNRC7Fdv1b5XiOAngdU'
            user_openid = get_user_openid(request, code)
            
            vipcode = VipCode.objects.get(code=fcode)
            referal_from_openid = vipcode.owner_openid.openid
            
            if referal_from_openid != user_openid:
                wx_award,state = WeixinUserAward.objects.get_or_create(user_openid=referal_from_openid)
                
                wx_award.remind_count = F('remind_count') + 1
                wx_award.remind_time  = datetime.datetime.now()
                wx_award.save()
                
            rep_json = {'success':True}
        except:
            rep_json = {'success':False}
            
        return  HttpResponse(json.dumps(rep_json),mimetype="application/json")   

    
