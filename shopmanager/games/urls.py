from django.conf.urls import patterns, include, url


urlpatterns = patterns('',
    
    (r'^paint/',include('games.paint.urls')),
)
