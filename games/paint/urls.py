from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView

from games.paint.views import CreateAccountView

urlpatterns = patterns('supplychain.wavepick.views',
                       # url('^$',csrf_exempt(WeixinAcceptView.as_view())),

                       url(r'^createaccount/$', CreateAccountView.as_view(),
                           name='paint_create_account'),
                       )
