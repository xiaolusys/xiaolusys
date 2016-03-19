#-*- coding:utf-8 -*-
import urlparse
import json
from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.core.urlresolvers import reverse

from rest_framework.views import APIView
from rest_framework import authentication
from rest_framework import permissions
from rest_framework import renderers 
from rest_framework.response import Response

from core.weixin.mixins import WeixinAuthMixin
from flashsale.pay.models_user import Customer
from .models import MamaDressResult
from . import constants

class DressView(WeixinAuthMixin, APIView):
    
    authentication_classes = ()
    permission_classes = ()
    renderer_classes = (renderers.TemplateHTMLRenderer,renderers.JSONRenderer)
    template_name = "mmdress/dress_entry.html"
        
    def get(self, request, *args, **kwargs):
        return Response({'active_id':1})
    
        

class DressQuestionView(WeixinAuthMixin, APIView):
    
    authentication_classes = (authentication.SessionAuthentication,)
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
    
        
    def get(self, request, active_id, *args, **kwargs):
        
        customer = get_object_or_404(Customer, user=request.user.id)
        unionid  = customer.unionid
        if not unionid:
            self.set_appid_and_secret(settings.WXPAY_APPID,settings.WXPAY_SECRET)
            user_infos = self.get_auth_userinfo(request)
            unionid = user_infos.get('unionid');openid = user_infos.get('openid')
            if not self.valid_openid(unionid):
                redirect_url = self.get_snsuserinfo_redirct_url(request)
                return redirect(redirect_url)
        else:
            openid = customer.openid
            user_infos = {
              'openid':customer.openid,
              'unionid':customer.unionid,
              'nickname':customer.nick,
              'headimgurl':customer.thumbnail,
            }
            
        referal_id = request.GET.get('referal_id')
        referal_dress = None
        if referal_id :
            if not referal_id.isdigit():
                raise Http404('404')
            referal_dress = get_object_or_404(MamaDressResult,id=referal_id)

        mama_dress,state = MamaDressResult.objects.get_or_create(user_unionid=unionid)
        if state:
            mama_dress.openid = user_infos.get('openid') 
            mama_dress.referal_from = referal_dress and referal_dress.user_unionid or ''
            mama_dress.mama_headimg = user_infos.get('headimgurl') or ''
            mama_dress.mama_nick = user_infos.get('nick') or ''
            mama_dress.save()
        
        replay = request.GET.get('replay','')
        if  mama_dress.is_finished():
            if not replay:
                response = redirect(reverse('dress_result'))
                self.set_cookie_openid_and_unionid(response,openid,unionid)
                return response
            else:
                mama_dress.replay()
        
        question_id = 1
        question = self.get_question(question_id)
        self.template_name = self.template_name.format(active_id)
        
        response = Response({
            'dress_id':mama_dress.id,
            'active_id':active_id,
            'question_id':question_id,
            'question':question,
            'pre_question_id':question_id,
            'post_question_id':question_id + 1,
            'score_string':''
        })

        self.set_cookie_openid_and_unionid(response,openid,unionid)
        return response
        
    def post(self, request, active_id, *args, **kwargs):
        
        score_string = request.POST['scores']
        dress_id = request.POST['dress_id']
        question_id = request.POST['question_id']
        
        mama_dresses = MamaDressResult.objects.filter(id=dress_id)
        if not mama_dresses.exists() :
            return HttpResponse('|'.join(['302',reverse('dress_result')]))
        
        mama_dress = mama_dresses[0]
        score_choices = dict(self.unserializer_scores(score_string))
        if question_id in score_choices:
            score_choices.pop(question_id)
        
        self.template_name = self.template_name.format(active_id)
        question_id = int(question_id)
        if question_id > len(constants.ACTIVES) :
            score = self.calc_score(score_choices.items())
            mama_dress.confirm_finished(score)
            return HttpResponse('|'.join(['302',reverse('dress_result')]))
        
        question = self.get_question(question_id)
        return Response({
            'dress_id':int(dress_id),
            'active_id':int(active_id),
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
    
    def gen_wxshare_signs(self,openid ,share_url):
        """ 生成微信分享参数 """
        from shopapp.weixin.weixin_apis import WeiXinAPI
        wx_api     = WeiXinAPI()
        wx_api.setAccountId(appKey=settings.WXPAY_APPID)
        signparams = wx_api.getShareSignParams(share_url)
        return {'openid': openid,
                'wx_singkey': signparams}
    
    def render_share_params(self, mama_dress, **kwargs):
        active =  constants.ACITVES[0]
        share_url = urlparse.urljoin(settings.M_SITE_URL,
                                     reverse('dress_share',kwargs={'dress_id':mama_dress.id}))
        resp = {
            'share_link':share_url,
            'share_title':active['share_title'].format(mama_dress=mama_dress,**kwargs),
            'share_desc':active['share_desc'].format(mama_dress=mama_dress,**kwargs),
            'share_img':active['share_img'],
            'callback_url':share_url
        }
        resp.update(self.gen_wxshare_signs(mama_dress.openid, share_url))
        return resp
    
    def get(self, request, *args, **kwargs):
        
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

        resp_params = {
            'mama_dress':mama_dress,
            'dress_age':dress_age,
            'dress_star':dress_star,
            'referal_dress':referal_dress,
            'referal_age':referal_age,
            'referal_star':referal_star,
            'age_tag':age_tag
        }
        resp_params.update({'share_params':self.render_share_params(**resp_params)})
        
        response = Response(resp_params)
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
    
    def get_dress_age_and_star(self, mama_dress):
        dress_score = self.calc_score(mama_dress)
        for ages in constants.SCORE_AGES:
            if dress_score == ages[0]:
                return ages[1],constants.DRESS_STARS[ages[2]]
        return 
    
    def calc_score(self,mama_dress):
        return (100 - mama_dress.exam_score) / 10
    
    def get(self, request, dress_id, *args, **kwargs):
        
        mama_dress,state = MamaDressResult.objects.get_or_create(id=dress_id)
        dress_age, dress_star = self.get_dress_age_and_star(mama_dress)
        
        response = Response({
                    'referal_dress':mama_dress,
                    'dress_age':dress_age,
                    'dress_star':dress_star
                })
        return response
    
    def post(self, request, dress_id, *args, **kwargs):
        share_type = request.POST.get('share_type')
        first_sendenvelop = False
        mama_dress= MamaDressResult.objects.get(id=dress_id)
        if not mama_dress.is_sendenvelop():
            mama_dress.send_envelop()
            first_sendenvelop = True
        mama_dress.add_share_type(share_type)
        
        return HttpResponse(json.dumps({
                'code':0,
                'is_sendenvelop':first_sendenvelop,
                'info':'红包领取成功'}),
                content_type="application/json")

