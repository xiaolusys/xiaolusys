from django.conf.urls.defaults import patterns, include, url
from django.views.generic import TemplateView
from supplychain.wavepick.views import WaveView, AllocateView

urlpatterns = patterns('supplychain.wavepick.views',
    #url('^$',csrf_exempt(WeixinAcceptView.as_view())),
    
    url(r'^createwave/$', TemplateView.as_view(
        template_name="create_wave.html"), 
        name='wavepick_create_wave'),

    url(r'^wave/(?P<wave_id>\d+)/$', WaveView.as_view(), 
        name='wave_detail'),

    url(r'^allocate/(?P<wave_id>\d+)/$', AllocateView.as_view(), 
        name='Allocate_detail'),
                       

)


