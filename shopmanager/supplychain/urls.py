from django.conf.urls.defaults import patterns, include, url


urlpatterns = patterns('',
    
    (r'^wavepick/',include('supplychain.wavepick.urls')),
    (r'^temai/',include('supplychain.temai.urls')),
)
