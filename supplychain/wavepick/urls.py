from django.conf.urls import include, url
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt

from supplychain.wavepick.views import *

urlpatterns = [
    #url('^$',csrf_exempt(WeixinAcceptView.as_view())),
    
    url(r'^createwave/$', csrf_exempt(WaveView.as_view()), 
        name='wavepick_create_wave'),
    url(r'^wave/(?P<wave_id>\d+)/$', csrf_exempt(WaveDetailView.as_view()), 
        name='wave_detail'),
    url(r'^allocate/(?P<wave_id>\d+)/$', csrf_exempt(AllocateView.as_view()), 
        name='Allocate_detail'),
    url(r'^publish/(?P<group_id>\d+)/$', PublishView.as_view(), 
        name='Allocate_detail'),
]


