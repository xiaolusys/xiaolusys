from django.conf.urls import include, url
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.cache import cache_page

from django.views.generic import TemplateView
from shopback.base.proxy import ProxyView
from shopapp.weixin_sales.decorators import record_weixin_clicks
from shopapp.weixin.views import views, proxy


# from core.options.renderers  import BaseJsonRenderer
# from core.options.permissions import IsAuthenticated
# from core.options.authentication import UserLoggedInAuthentication
# from .resources import WeixinProductResource
# from .renderers import WeixinProductHtmlRenderer


urlpatterns = [

    url('^$', csrf_exempt(views.WeixinAcceptView.as_view())),
    url(r'^qr/(?P<url>.*)$', csrf_exempt(ProxyView.as_view(
       proxy_format='%s/%%s' % settings.WEIXIN_QRCODE_HOST)),
       name='weixin_show_qrcode'),
    url(r'^fm/(?P<url>.*)$', csrf_exempt(ProxyView.as_view(
       proxy_format='%s/%%s' % settings.WEIXIN_MEDIA_HOST)),
       name='weixin_media_updown'),

    url(r'^baby/archive/$', TemplateView.as_view(
       template_name="weixin/baby_archives.html"),
       name='weixin_baby_archive'),

    url(r'^charge/(?P<pk>\d+)/$', views.chargeWXUser),
    url(r'^user/(?P<pk>\d+)/$', views.WeixinUserModelView.as_view()),

    url(r'^referal/$', views.ReferalView.as_view()),
    url(r'^referalrules/$', TemplateView.as_view(
       template_name="weixin/referal_rules.html")),
    url(r'^ambassintention/$', TemplateView.as_view(
       template_name="weixin/ambass_intention.html")),
    url(r'^unistory/$', TemplateView.as_view(
       template_name="weixin/unilittles_story.html")),

    url(r'^freesamples/$', views.FreeSampleView.as_view()),
    url(r'^sampleapply/$', views.SampleApplyView.as_view()),
    url(r'^sampleconfirm/$', views.SampleConfirmView.as_view()),
    url(r'^vipcodeverify/$', views.VipCodeVerifyView.as_view()),
    url(r'^sampleads/(?P<pk>\d+)/$',
       views.SampleAdsView.as_view(),
       #         record_weixin_clicks(views.SampleAdsView.as_view(),validated_in=48*60*60),
       name="weixin_sampleads"),
    url(r'^inviteresult/$', views.ResultView.as_view()),
    url(r'^finallist/(?P<batch>\d+)/(?P<page>\d+)/(?P<month>\d+)/$',
       cache_page(96 * 60 * 60)(views.FinalListView.as_view())),

    url(r'^babyinfo/$', views.BabyInfoView.as_view()),
    url(r'^orderinfo/$', views.OrderInfoView.as_view()),
    url(r'^addreferal/$', views.WeixinAddReferalView.as_view()),
    url(r'^requestcode/$', views.RequestCodeView.as_view()),
    url(r'^verifycode/$', views.VerifyCodeView.as_view()),
    url(r'^refundsubmit/$', views.RefundSubmitView.as_view()),
    url(r'^refundreview/$', staff_member_required(views.RefundReviewView.as_view())),
    url(r'^refundrecord/$', staff_member_required(views.RefundRecordView.as_view())),
    url(r'^payguide/$', views.PayGuideView.as_view()),
    url(r'^coupon/(?P<user_pk>\d+)/(?P<coupon_pk>\d+)/$', views.CouponView.as_view()),
    url(r'^vipcoupon/$', views.VipCouponView.as_view()),
    url(r'^requestcoupon/$', views.RequestCouponView.as_view()),
    url(r'^couponfaq/$', views.CouponFaqView.as_view()),
    url(r'^survey/$', views.SurveyView.as_view()),
    url(r'^samplechoose/$', views.SampleChooseView.as_view()),
    url(r'^score/(?P<user_pk>\d+)/$', cache_page(5 * 60)(views.ScoreView.as_view())),
    url(r'^clickscore/(?P<id>\d+)/$', views.ClickScoreView.as_view()),
    url(r'^scorerule/$', TemplateView.as_view(
       template_name="weixin/scorerule.html")),
    url(r'^couponrule/$', TemplateView.as_view(
       template_name="weixin/sales/couponrule.html")),

    url(r'^scoremenu/$', views.ScoreMenuView.as_view()),
    url(r'^gift/$', views.GiftView.as_view()),

    url(r'^test/$', record_weixin_clicks(views.TestView.as_view())),

    url(r'^validmobile/$', TemplateView.as_view(
       template_name="weixin/valid_mobile.html"),
       name='weixin_valid_mobile'),

    url(r'^examination/', include('shopapp.weixin_examination.urls')),
    url(r'^sales/', include('shopapp.weixin_sales.urls')),
    url(r'^score/', include('shopapp.weixin_score.urls')),

    url(r'^product/sync/$', csrf_exempt(views.WeixinProductView.as_view()),
       name='weixin_product_modify'),
    url(r'^product/verify/$', csrf_exempt(views.WeixinProductVerifyView.as_view()),
       name='weixin_product_verify'),

    url(r'^checkqr/', views.TestCodeView.as_view()),

    url(r'^warn/$', views.warn, name='weixin_warn'),
    url(r'^rights/$', views.rights, name='weixin_feedback'),
    url(r'^napay/$', views.napay, name='weixin_napay'),
    url(r'^wxpay/$', views.wxpay, name='weixin_wxpay'),

    url(r'^wxorder_detail/$', views.weixinorder_detail, name='weixinorder_detail'),
]


urlpatterns += [
    url(r'^proxy/token/$', proxy.WXTokenProxy.as_view()),
    url(r'^proxy/item/$', proxy.SaleProductSearch.as_view()),
    url(r'^proxy/u/(?P<pub_id>\w+)/$',
        proxy.WXMessageHttpProxy.as_view(base_url=settings.NTALKER_NOTIFY_URL), {'url': ''}),
    url(r'^proxy/ntalker/$',
        proxy.WXCustomAndMediaProxy.as_view(base_url=settings.WX_MESSAGE_URL), {'url': ''}),
    url(r'^proxy/upload/$',
        proxy.WXCustomAndMediaProxy.as_view(base_url=settings.WX_MEDIA_UPLOAD_URL), {'url': ''}),
    url(r'^proxy/down/$', proxy.WXCustomAndMediaProxy.as_view(base_url=settings.WX_MEDIA_GET_URL), {'url': ''}),
]
