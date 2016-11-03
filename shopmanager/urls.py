from django.conf.urls import patterns, include, url
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView
from django.contrib import admin
from django.conf import settings
from django.views.static import serve
from django.contrib.admin.views.decorators import staff_member_required

from httpproxy.views import HttpProxy

admin.autodiscover()

def home(request):
    return HttpResponseRedirect('/admin/')

urlpatterns = patterns(
    '',
   (r'^admin/doc/', include('django.contrib.admindocs.urls')),
   (r'^accounts/', include('shopapp.taobao.urls')),
   (r'^category/', include('shopback.categorys.urls')),
   (r'^fenxiao/', include('shopback.fenxiao.urls')),
   (r'^items/', include('shopback.items.urls')),
   (r'^logistics/', include('shopback.logistics.urls')),
   (r'^orders/', include('shopback.orders.urls')),
   (r'^trades/', include('shopback.trades.urls')),
   (r'^warehouse/',include('shopback.warehouse.urls')),
   (r'^refunds/', include('shopback.refunds.urls')),
   (r'^purchases/', include('shopback.purchases.urls')),
   (r'^users/', include('shopback.users.urls')),
   (r'^weixin/', include('shopapp.weixin.urls')),
   (r'^wx/', include('shopapp.weixin.urls')),
   (r'^supplychain/', include('supplychain.urls')),
   (r'^games/', include('games.urls')),
   (r'^mm/', include('flashsale.pay.urls')),
   (r'^coupon/', include('flashsale.coupon.urls')),
   (r'^m/', include('flashsale.xiaolumm.urls')),
    (r'^luntan/', include('flashsale.luntan.urls')),
    (r'^thermal/', include('shopapp.STOthermal.urls')),
   (r'^sale/', include('flashsale.urls')),
   (r'^statistics/', include('statistics.urls')),
   url(r'^djcelery/', include('djcelery.urls'), name="task_state"),

   (r'^app/', include('shopapp.urls')),
   (r'^lucky/', include('games.luckyawards.urls')),
   url(r'^home/$', home, name='home_page'),
   (r'^$', home),
   (r'^top_monitor\.html$', csrf_exempt(TemplateView.as_view(template_name='top_monitor.html'))),

   (r'^download/(?P<path>.*)$', staff_member_required(serve),
    {'document_root': settings.DOWNLOAD_ROOT, 'show_indexes': True}),

   url(r'^rest/', include('flashsale.restpro.urls')),
   url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
   url(r'^apis/', include('shopmanager.urls_api')),
   url(r'^qrcode/(?P<url>.*)',
       HttpProxy.as_view(base_url='http://%s/qrcode' % settings.QINIU_PUBLIC_DOMAIN)),
   # (r'^admin/doc/', include('django.contrib.admindocs.urls')),
   url('', include('django_prometheus.urls')),
   (r'^admin/', include(admin.site.urls)),

)

if settings.DEBUG == True:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve',
         {'document_root': settings.STATIC_DOC_ROOT}),
        (r'^media/(?P<path>.*)$', 'django.views.static.serve',
         {'document_root': settings.MEDIA_ROOT}),
        (r'^download/(?P<path>.*)$', 'django.views.static.serve',
         {'document_root': settings.DOWNLOAD_ROOT, 'show_indexes': True}),
    )
    try:
        import debug_toolbar
        urlpatterns += patterns('', url(r'^__debug__/', include(debug_toolbar.urls)),)
    except ImportError:
        pass
