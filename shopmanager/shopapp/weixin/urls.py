from django.conf.urls.defaults    import patterns, include, url
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.views.generic import TemplateView
from shopback.base.proxy  import ProxyView
from shopapp.weixin.views import WeixinAcceptView,WeixinAddReferalView,ReferalView

urlpatterns = patterns('',

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

#    url(r'^referal/$', TemplateView.as_view(
#        template_name="weixin/referal.html"), 
#        name='weixin_referal'),

    url(r'^referal/$', ReferalView.as_view()),
    
    url(r'^addreferal/$', WeixinAddReferalView.as_view()),
    

)
