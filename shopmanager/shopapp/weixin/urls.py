from django.conf.urls.defaults    import patterns, include, url
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.views.generic import TemplateView
from shopback.base.proxy  import ProxyView
from shopapp.weixin.views import WeixinAcceptView

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
        name='weixin_baby_archive') ,                  

    url(r'^validmobile/$', TemplateView.as_view(
        template_name="weixin/valid_mobile.html"), 
        name='weixin_valid_mobile'),
    
    url(r'^warn/$','warn',name='weixin_warn'),
    url(r'^rights/$','maintian',name='weixin_feedback'),
    url(r'^napay/$','napay',name='weixin_napay'),
    url(r'^wxpay/$','wxpay',name='weixin_wxpay'),

)
