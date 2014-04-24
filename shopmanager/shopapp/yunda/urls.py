from django.conf.urls.defaults    import patterns, include, url
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

urlpatterns = patterns('shopapp.yunda.views',

    url('^$',csrf_exempt(WeixinAcceptView.as_view())),
)
