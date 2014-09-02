from django.conf.urls.defaults    import patterns, include, url
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.cache import cache_page

from django.views.generic import TemplateView
from shopback.base.proxy  import ProxyView
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
                                  TestView)

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
    url(r'^sampleads/(?P<pk>\d+)/$', SampleAdsView.as_view()),
    url(r'^inviteresult/$', ResultView.as_view()),
    url(r'^finallist/(?P<batch>\d+)/(?P<page>\d+)/(?P<month>\d+)/$', cache_page(FinalListView.as_view(),24*60*60)),

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
    url(r'^test/$', TestView.as_view()),    
                     
    url(r'^validmobile/$', TemplateView.as_view(
        template_name="weixin/valid_mobile.html"), 
        name='weixin_valid_mobile'),
    
    url(r'^warn/$','warn',name='weixin_warn'),
    url(r'^rights/$','rights',name='weixin_feedback'),
    url(r'^napay/$','napay',name='weixin_napay'),
    url(r'^wxpay/$','wxpay',name='weixin_wxpay'),

)
