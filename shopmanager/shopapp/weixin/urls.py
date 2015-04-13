from django.conf.urls.defaults    import patterns, include, url
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.cache import cache_page

from django.views.generic import TemplateView
from shopback.base.proxy  import ProxyView
from shopapp.weixin_sales.decorators import record_weixin_clicks
from shopapp.weixin.views import (WeixinAcceptView,
                                  WeixinAddReferalView,
                                  ReferalView,
                                  OrderInfoView,
                                  BabyInfoView,
                                  RequestCodeView,
                                  VerifyCodeView,
                                  RefundSubmitView,
                                  RefundReviewView,
                                  RefundRecordView,
                                  FreeSampleView,
                                  SampleApplyView,
                                  SampleAdsView,
                                  WeixinUserModelView,
                                  SampleConfirmView,
                                  VipCodeVerifyView,
                                  ResultView,
                                  FinalListView,
                                  PayGuideView,
                                  CouponView,
                                  VipCouponView,
                                  RequestCouponView,
                                  CouponFaqView,
                                  SurveyView,
                                  SampleChooseView,
                                  ScoreView,
                                  ClickScoreView,
                                  ScoreMenuView,
                                  GiftView,
                                  WeixinProductView,
                                  TestView,
                                  TestCodeView)

from shopback.base.renderers  import BaseJsonRenderer
from shopback.base.permissions import IsAuthenticated
from shopback.base.authentication import UserLoggedInAuthentication
from .resources import WeixinProductResource
from .renderers import WeixinProductHtmlRenderer


urlpatterns = patterns('shopapp.weixin.views',

    url('^$',csrf_exempt(WeixinAcceptView.as_view())),
    url(r'^qr/(?P<url>.*)$', csrf_exempt(ProxyView.as_view(
        proxy_format='%s/%%s' % settings.WEIXIN_QRCODE_HOST)), 
        name='weixin_show_qrcode'),
    url(r'^fm/(?P<url>.*)$', csrf_exempt(ProxyView.as_view(
        proxy_format='%s/%%s' % settings.WEIXIN_MEDIA_HOST)), 
        name='weixin_media_updown'),
                       
    url(r'^baby/archive/$', TemplateView.as_view(
        template_name="weixin/baby_archives.html"), 
        name='weixin_baby_archive'),

    url(r'^charge/(?P<pk>\d+)/$', 'chargeWXUser'),
    url(r'^user/(?P<pk>\d+)/$', WeixinUserModelView.as_view()),
    
    url(r'^referal/$', ReferalView.as_view()),
    url(r'^referalrules/$', TemplateView.as_view(
            template_name="weixin/referal_rules.html")),
    url(r'^ambassintention/$', TemplateView.as_view(
            template_name="weixin/ambass_intention.html")),
    url(r'^unistory/$', TemplateView.as_view(
            template_name="weixin/unilittles_story.html")),
                    
    url(r'^freesamples/$', FreeSampleView.as_view()),
    url(r'^sampleapply/$', SampleApplyView.as_view()),
    url(r'^sampleconfirm/$', SampleConfirmView.as_view()),
    url(r'^vipcodeverify/$', VipCodeVerifyView.as_view()),                       
    url(r'^sampleads/(?P<pk>\d+)/$', 
#         SampleAdsView.as_view(),
         record_weixin_clicks(SampleAdsView.as_view(),validated_in=48*60*60),
        name="weixin_sampleads"),
    url(r'^inviteresult/$', ResultView.as_view()),
    url(r'^finallist/(?P<batch>\d+)/(?P<page>\d+)/(?P<month>\d+)/$', 
        cache_page(FinalListView.as_view(),96*60*60)),

    url(r'^babyinfo/$', BabyInfoView.as_view()),
    url(r'^orderinfo/$', OrderInfoView.as_view()),
    url(r'^addreferal/$', WeixinAddReferalView.as_view()),
    url(r'^requestcode/$', RequestCodeView.as_view()),
    url(r'^verifycode/$', VerifyCodeView.as_view()),
    url(r'^refundsubmit/$', RefundSubmitView.as_view()),                       
    url(r'^refundreview/$', staff_member_required(RefundReviewView.as_view())),
    url(r'^refundrecord/$', staff_member_required(RefundRecordView.as_view())),
    url(r'^payguide/$', PayGuideView.as_view()),
    url(r'^coupon/(?P<user_pk>\d+)/(?P<coupon_pk>\d+)/$', CouponView.as_view()),
    url(r'^vipcoupon/$', VipCouponView.as_view()),
    url(r'^requestcoupon/$', RequestCouponView.as_view()),
    url(r'^couponfaq/$', CouponFaqView.as_view()),
    url(r'^survey/$', SurveyView.as_view()),
    url(r'^samplechoose/$', SampleChooseView.as_view()),
    url(r'^score/(?P<user_pk>\d+)/$', cache_page(ScoreView.as_view(),5*60)),
    url(r'^clickscore/(?P<id>\d+)/$', ClickScoreView.as_view()),
    url(r'^scorerule/$', TemplateView.as_view(
            template_name="weixin/scorerule.html")),
    url(r'^couponrule/$', TemplateView.as_view(
            template_name="weixin/sales/couponrule.html")),
                       
    url(r'^scoremenu/$', ScoreMenuView.as_view()),
    url(r'^gift/$', GiftView.as_view()),
        
    url(r'^test/$', record_weixin_clicks(TestView.as_view())),    
                     
    url(r'^validmobile/$', TemplateView.as_view(
        template_name="weixin/valid_mobile.html"), 
        name='weixin_valid_mobile'),
    
    (r'^examination/',include('shopapp.weixin_examination.urls')),
    (r'^sales/',include('shopapp.weixin_sales.urls')),
    (r'^score/',include('shopapp.weixin_score.urls')),
    
    url(r'^product/sync/$',WeixinProductView.as_view(
        resource=WeixinProductResource,
        renderers=(BaseJsonRenderer,WeixinProductHtmlRenderer),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)),name='weixin_product_modify'),
    
    (r'^checkqr/',TestCodeView.as_view()),
    
    url(r'^warn/$','warn',name='weixin_warn'),
    url(r'^rights/$','rights',name='weixin_feedback'),
    url(r'^napay/$','napay',name='weixin_napay'),
    url(r'^wxpay/$','wxpay',name='weixin_wxpay'),

)
