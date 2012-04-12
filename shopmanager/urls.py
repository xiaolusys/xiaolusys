from django.conf.urls.defaults import patterns, include, url
from auth.accounts.views import home,login_taobo
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from django.conf import settings
admin.autodiscover()

urlpatterns = patterns('',
    (r'^sentry/', include('sentry.web.urls')),
    (r'^accounts/', include('auth.accounts.urls')),
    (r'^task/',include('shopback.task.urls')),
    (r'^items/',include('shopback.items.urls')),
    (r'^cats/',include('shopback.categorys.urls')),
    (r'^search/', include('search.urls')),
    (r'^autolist/', include('autolist.urls')),
    url(r'^home/$',home,name='home_page'),
    (r'^$',login_taobo),
    (r'^static/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.STATIC_DOC_ROOT}),
    (r'^admin/', include(admin.site.urls)),

    (r'^tb/', include('tbsubway.category.urls')),

)
