#-*- coding:utf-8 -*-
from django.conf import settings
from django.shortcuts import redirect
from django.core.urlresolvers import reverse

from rest_framework.views import APIView
from rest_framework import authentication
from rest_framework import permissions
from rest_framework import renderers 
from rest_framework.response import Response

from core.weixin.mixins import WeixinAuthMixin
from .models import MamaDressResult
from . import constants

class DressView(WeixinAuthMixin, APIView):
    
    authentication_classes = ()
    permission_classes = ()
    renderer_classes = (renderers.TemplateHTMLRenderer,)
    template_name = "mmdress/dress_entry.html"
        
    def get(self, request, *args, **kwargs):
        
        content = request.REQUEST
        self.set_appid_and_secret(settings.WXPAY_APPID,settings.WXPAY_SECRET)
        user_infos = self.get_auth_userinfo(request)
        unionid = user_infos.get('unionid')
        openid  = user_infos.get('openid')
        if not self.valid_openid(unionid):
            redirect_url = self.get_snsuserinfo_redirct_url(request)
            return redirect(redirect_url)
        
        mama_dress,state = MamaDressResult.objects.get_or_create(user_unionid=unionid)
        referal_id  = content.get('referal_id',0)
        referal_dresses    = MamaDressResult.objects.filter(id=referal_id)
        referal_dress = None
        if referal_dresses.exists():
            referal_dress = referal_dresses[0]
        
        response = Response({
                    'user_info':user_infos,
                    'mama_dress':mama_dress,
                    'referal_dress':referal_dress,
                })
        
        self.set_cookie_openid_and_unionid(response,openid,unionid)
        return response
    
    def post(self, request, *args, **kwargs):
        content = request.REQUEST
        user_unionid = content.get('user_unionid')
        mm_dress,state = MamaDressResult.objects.get_or_create(user_unionid=user_unionid)
        for k,v in content.iteritems():
            if hasattr(mm_dress, k):
                setattr(mm_dress,k,v)
        mm_dress.save()
        return redirect(reverse('dress_question',kwargs={'active':1,'dressid':mm_dress.id,'question_id':1}))
    

class DressQuestionView(WeixinAuthMixin, APIView):
    
    authentication_classes = ()
    permission_classes = ()
    renderer_classes = (renderers.TemplateHTMLRenderer,)
    template_name = "mmdress/active_{0}/question.html"
    
    def get_question(self,question_id):
        question = constants.ACTIVES[int(question_id)-1].copy()
        return question
    
    def unserializer_scores(self,score_string):
        score_l = score_string.strip().split(',')
        return [s.split('_') for s in score_l if s]
        
    def serializer_scores(self,score_list):
        if isinstance(score_list,list):
            return ','.join(['%s_%s'%st for st in score_list])
        elif isinstance(score_list,dict):
            return ','.join(['%s_%s'%st for st in score_list.iteritems()])
        else:
            return ''
    
    def calc_score(self,score_list):
        def tsum(x,y):
            if isinstance(x,tuple):
                return int(x[1]) + int(y[1])
            else:
                return x + int(y[1])
        return reduce(tsum ,score_list)
        
    def get(self, request, active, dressid, *args, **kwargs):
        
        mama_dresses = MamaDressResult.objects.filter(id=dressid)
        if not mama_dresses.exists() :
            return redirect(reverse('dress_home'))
        
        mama_dress = mama_dresses[0]
        if mama_dress.is_finished():
            return redirect('./')
        
        question_id = 1
        question = self.get_question(question_id)
        self.template_name = self.template_name.format(active)
        
        return Response({
            'dressid':dressid,
            'active':1,
            'question_id':question_id,
            'question':question,
            'pre_question_id':question_id,
            'post_question_id':question_id + 1,
            'score_string':''
        })
        
    def post(self, request, active, dressid, question_id, *args, **kwargs):
        
        score_string = request.POST.get('scores','')
        mama_dresses = MamaDressResult.objects.filter(id=dressid)
        if not mama_dresses.exists() :
            return redirect(reverse('dress_home'))
        
        mama_dress = mama_dresses[0]
        score_choices = dict(self.unserializer_scores(score_string))
        if question_id in score_choices:
            score_choices.pop(question_id)
        
        self.template_name = self.template_name.format(active)
        question_id = int(question_id)
        if question_id > len(constants.ACTIVES) :
            score = self.calc_score(score_choices.items())
            mama_dress.confirm_finished(score)
            return redirect(reverse('dress_result'))
        
        question = self.get_question(question_id)
        return Response({
            'dressid':int(dressid),
            'active':int(active),
            'question_id':question_id,
            'question':question,
            'pre_question_id':question_id - 1,
            'post_question_id':question_id + 1,
            'score_string':self.serializer_scores(score_choices)
        })

class DressResultView(WeixinAuthMixin, APIView):
    
    authentication_classes = ()
    permission_classes = ()
    renderer_classes = (renderers.TemplateHTMLRenderer,)
    template_name = "mmdress/dress_result.html"
        
    def get(self, request, *args, **kwargs):
        
        content = request.REQUEST
        self.set_appid_and_secret(settings.WXPAY_APPID,settings.WXPAY_SECRET)
        openid,unionid = self.get_openid_and_unionid(request)
        if not self.valid_openid(unionid):
            redirect_url = self.get_snsuserinfo_redirct_url(request)
            return redirect(redirect_url)
        
        mama_dress,state = MamaDressResult.objects.get_or_create(user_unionid=unionid)
        referal_id = content.get('referal_id',0)
        dresult = MamaDressResult.objects.filter(referal_from=referal_id)
        referal_info = None
        if dresult.exists():
            referal_info = dresult[0]
        
        response = Response({
                    'mama_dress':mama_dress,
                    'referal_dress':referal_info,
                    'age_range':range(1976,2001)
                })
        self.set_cookie_openid_and_unionid(response,openid,unionid)
        return response
    
    def post(self, request, *args, **kwargs):
        content = request.REQUEST
        user_unionid = content.get('user_unionid')
        mm_dress,state = MamaDressResult.objects.get_or_create(user_unionid=user_unionid)
        for k,v in content.iteritems():
            if hasattr(mm_dress, k):
                setattr(mm_dress,k,v)
        mm_dress.save()
        return redirect(reverse('dress_question',kwargs={'active':1,'dressid':mm_dress.id,'question_id':1}))

