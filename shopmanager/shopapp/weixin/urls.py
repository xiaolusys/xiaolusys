from django.conf.urls.defaults    import patterns, include, url
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from shopback.base.proxy  import ProxyView
from shopapp.weixin.views import WeixinAcceptView

urlpatterns = patterns('',

    url('^$',csrf_exempt(WeixinAcceptView.as_view())),
    url(r'^qr/(?P<url>.*)$', csrf_exempt(ProxyView.as_view(
        proxy_format='%s/%%s' % settings.WEIXIN_QRCODE_HOST)), name='weixin_show_qrcode'),
    url(r'^fm/(?P<url>.*)$', csrf_exempt(ProxyView.as_view(
        proxy_format='%s/%%s' % settings.WEIXIN_MEDIA_HOST)), name='weixin_media_updown'),
)
