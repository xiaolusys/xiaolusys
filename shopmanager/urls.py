from django.conf.urls.defaults import patterns, include, url
from django.views.decorators.csrf import csrf_exempt
from auth.accounts.views import home,login_taobo
from django.views.generic import TemplateView
from django.contrib import admin
from django.conf import settings
from django.views.static import serve
from django.contrib.admin.views.decorators import staff_member_required
admin.autodiscover()


urlpatterns = patterns('',

    (r'^accounts/', include('auth.accounts.urls')),
    (r'^category/',include('shopback.categorys.urls')),
    (r'^fenxiao/',include('shopback.fenxiao.urls')),
    (r'^items/',include('shopback.items.urls')),
    (r'^logistics/',include('shopback.logistics.urls')),
    (r'^orders/',include('shopback.orders.urls')),
    (r'^trades/',include('shopback.trades.urls')),
    (r'^refunds/',include('shopback.refunds.urls')),
    (r'^purchases/',include('shopback.purchases.urls')),
    (r'^users/',include('shopback.users.urls')),
    
    (r'^app/',include('shopapp.urls')),
    url(r'^home/$',home,name='home_page'),

    (r'^top_monitor\.html$',csrf_exempt(TemplateView.as_view(template_name='top_monitor.html'))),
    (r'^$',login_taobo),

    (r'^download/(?P<path>.*)$',staff_member_required(serve),
            {'document_root': settings.DOWNLOAD_ROOT,'show_indexes':True}),
    
    #(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),
    
)

if settings.DEBUG == True:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.STATIC_DOC_ROOT}),
        (r'^media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT}),
        (r'^download/(?P<path>.*)$','django.views.static.serve',
            {'document_root': settings.DOWNLOAD_ROOT,'show_indexes':True}),
    )
