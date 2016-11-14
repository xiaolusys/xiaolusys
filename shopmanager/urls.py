import json
from django.conf.urls import include, url
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseRedirect, HttpResponse
from django.views.generic import TemplateView
from django.contrib import admin
from django.conf import settings
from django.views.static import serve
from django.contrib.admin.views.decorators import staff_member_required
from celery.result import AsyncResult
from httpproxy.views import HttpProxy

admin.autodiscover()


def home(request):
    return HttpResponseRedirect('/admin/')


def celery_state(request, task_id):
    result = AsyncResult(task_id)
    if not result or not result.id:
        return HttpResponse(json.dumps({'tasks': {}}), content_type="application/json")

    return HttpResponse(json.dumps({
            "task": {
                "status": result.status,
                "result": result.result,
                "id": result.id
            }
        }),
        content_type="application/json"
    )


urlpatterns = [
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^accounts/', include('shopapp.taobao.urls')),
    url(r'^category/', include('shopback.categorys.urls')),
    url(r'^fenxiao/', include('shopback.fenxiao.urls')),
    url(r'^items/', include('shopback.items.urls')),
    url(r'^logistics/', include('shopback.logistics.urls')),
    url(r'^orders/', include('shopback.orders.urls')),
    url(r'^trades/', include('shopback.trades.urls')),
    url(r'^warehouse/', include('shopback.warehouse.urls')),
    url(r'^refunds/', include('shopback.refunds.urls')),
    url(r'^purchases/', include('shopback.purchases.urls')),
    url(r'^users/', include('shopback.users.urls')),
    url(r'^weixin/', include('shopapp.weixin.urls')),
    url(r'^wx/', include('shopapp.weixin.urls')),
    url(r'^supplychain/', include('supplychain.urls')),
    url(r'^games/', include('games.urls')),
    url(r'^mm/', include('flashsale.pay.urls')),
    url(r'^coupon/', include('flashsale.coupon.urls')),
    url(r'^m/', include('flashsale.xiaolumm.urls')),
    url(r'^luntan/', include('flashsale.luntan.urls')),
    url(r'^thermal/', include('shopapp.STOthermal.urls')),
    url(r'^sale/', include('flashsale.urls')),
    url(r'^statistics/', include('statistics.urls')),
    url(r'^djcelery/(?P<task_id>.*)/status/$', celery_state, name="task_state"),

    url(r'^app/', include('shopapp.urls')),
    url(r'^lucky/', include('games.luckyawards.urls')),
    url(r'^home/$', home, name='home_page'),
    url(r'^$', home),
    url(r'^top_monitor\.html$', csrf_exempt(TemplateView.as_view(template_name='top_monitor.html'))),

    url(r'^download/(?P<path>.*)$', staff_member_required(serve),
        {'document_root': settings.DOWNLOAD_ROOT, 'show_indexes': True}),

    url(r'^rest/', include('flashsale.restpro.urls')),
    url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    url(r'^apis/', include('shopmanager.urls_api')),
    url(r'^qrcode/(?P<url>.*)',
        HttpProxy.as_view(base_url='http://%s/qrcode' % settings.QINIU_PUBLIC_DOMAIN)),
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url('', include('django_prometheus.urls')),
    url(r'^admin/', include(admin.site.urls)),
]

if settings.DEBUG == True:
    from django.views.static import serve

    urlpatterns += [
        url(r'^static/(?P<path>.*)$', serve,
            {'document_root': settings.STATIC_DOC_ROOT}),
        url(r'^media/(?P<path>.*)$', serve,
            {'document_root': settings.MEDIA_ROOT}),
        url(r'^download/(?P<path>.*)$', serve,
            {'document_root': settings.DOWNLOAD_ROOT, 'show_indexes': True}),
    ]
    try:
        import debug_toolbar

        urlpatterns += [url(r'^__debug__/', include(debug_toolbar.urls)), ]
    except ImportError:
        pass
