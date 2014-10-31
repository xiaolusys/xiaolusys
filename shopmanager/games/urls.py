from django.conf.urls.defaults import patterns, include, url


urlpatterns = patterns('',
    
    (r'^paint/',include('games.paint.urls')),
)
