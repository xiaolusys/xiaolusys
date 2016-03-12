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
            return redirect(reverse('dress_result'))
        
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
        
        score_string = request.POST['scores']
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
    
    def calc_score(self,mama_dress):
        return (100 - mama_dress.exam_score) / 10
    
    def get_dress_age_and_star(self, mama_dress):
        dress_score = self.calc_score(mama_dress)
        for ages in constants.SCORE_AGES:
            if dress_score == ages[0]:
                return ages[1],constants.DRESS_STARS[ages[2]]
        return 
            
    def get_age_tag(self,differ_age):
        
        age_tags_dict = dict(constants.AGE_TAGS)
        min_age = min(age_tags_dict.keys())
        max_age = max(age_tags_dict.keys())
        if differ_age < min_age:
            differ_age = min_age
        if differ_age > max_age:
            differ_age = min_age
        return (differ_age ,age_tags_dict.get(differ_age))
        
    def get(self, request, *args, **kwargs):
        
        content = request.REQUEST
        self.set_appid_and_secret(settings.WXPAY_APPID,settings.WXPAY_SECRET)
        openid,unionid = self.get_openid_and_unionid(request)
        if not self.valid_openid(unionid):
            redirect_url = self.get_snsuserinfo_redirct_url(request)
            return redirect(redirect_url)
        
        mama_dress,state = MamaDressResult.objects.get_or_create(user_unionid=unionid)
        if not mama_dress.is_finished():
            return redirect(reverse('dress_home'))
        
        if not mama_dress.is_aged():
            return redirect(reverse('dress_age'))
        
        referal_dress = mama_dress.get_referal_mamadress()
        dress_age, dress_star = self.get_dress_age_and_star(mama_dress)
        
        age_tag = None
        referal_age, referal_star = (0, 0)
        if referal_dress:
            referal_age, referal_star = self.get_dress_age_and_star(referal_dress)
            age_tag = self.get_age_tag(abs(dress_age - referal_age))
            
        response = Response({
                    'mama_dress':mama_dress,
                    'dress_age':dress_age,
                    'dress_star':dress_star,
                    'referal_dress':referal_dress,
                    'referal_age':referal_age,
                    'referal_star':referal_star,
                    'age_tag':age_tag
                })
        self.set_cookie_openid_and_unionid(response,openid,unionid)
        return response
    
    
class DressAgeView(WeixinAuthMixin, APIView):
    
    authentication_classes = ()
    permission_classes = ()
    renderer_classes = (renderers.TemplateHTMLRenderer,)
    template_name = "mmdress/dress_age.html"
        
    def get(self, request, *args, **kwargs):
        
        self.set_appid_and_secret(settings.WXPAY_APPID,settings.WXPAY_SECRET)
        openid,unionid = self.get_openid_and_unionid(request)
        if not self.valid_openid(unionid):
            redirect_url = self.get_snsuserinfo_redirct_url(request)
            return redirect(redirect_url)
        
        mama_dress,state = MamaDressResult.objects.get_or_create(user_unionid=unionid)
        if not mama_dress.is_finished():
            return redirect(reverse('dress_home'))
        
        response = Response({
                    'mama_dress':mama_dress,
                    'age_range':range(1976,2001)
                })
        self.set_cookie_openid_and_unionid(response,openid,unionid)
        return response
    
    def post(self, request, *args, **kwargs):
        user_unionid = request.POST['user_unionid']
        mama_age = request.POST['mama_age']
        mm_dress,state = MamaDressResult.objects.get_or_create(user_unionid=user_unionid)
        mm_dress.mama_age = mama_age
        mm_dress.save()
        return redirect(reverse('dress_result'))

class DressShareView(WeixinAuthMixin, APIView):
    
    authentication_classes = ()
    permission_classes = ()
    renderer_classes = (renderers.TemplateHTMLRenderer,)
    template_name = "mmdress/dress_share.html"
        
    def get(self, request, *args, **kwargs):
        
        self.set_appid_and_secret(settings.WXPAY_APPID,settings.WXPAY_SECRET)
        openid,unionid = self.get_openid_and_unionid(request)
        if not self.valid_openid(unionid):
            redirect_url = self.get_snsuserinfo_redirct_url(request)
            return redirect(redirect_url)
        
        mama_dress,state = MamaDressResult.objects.get_or_create(user_unionid=unionid)
        if not mama_dress.is_finished():
            return redirect(reverse('dress_home'))
        
        
        
        response = Response({
                    'mama_dress':mama_dress,
                    'age_range':range(1976,2001)
                })
        self.set_cookie_openid_and_unionid(response,openid,unionid)
        return response
    
    def post(self, request, *args, **kwargs):
#         user_unionid = request.POST['user_unionid']
#         mm_dress,state = MamaDressResult.objects.get_or_create(user_unionid=user_unionid)
#         mm_dress.mama_age = mama_age
#         mm_dress.save()
        return redirect(reverse('dress_result'))

