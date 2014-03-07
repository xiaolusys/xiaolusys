from django.conf.urls.defaults import patterns, include, url
from django.views.decorators.csrf import csrf_exempt
from shopapp.weixin.views import WeixinAcceptView

urlpatterns = patterns('',

    url('^$',csrf_exempt(WeixinAcceptView.as_view())),
)
