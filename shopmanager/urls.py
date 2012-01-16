from django.conf.urls.defaults import patterns, include, url
from auth.accounts.views import home,login_taobo
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^sentry/', include('sentry.web.urls')),
    (r'^accounts/', include('auth.accounts.urls')),
    (r'^task/',include('shopback.task.urls')),
    url(r'^home/$',home,name='home_page'),
    (r'^$',login_taobo),
    (r'^admin/', include(admin.site.urls)),
)
