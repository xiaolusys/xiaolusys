# -*- coding: utf-8 -*-

from django.conf.urls.defaults import patterns, url
from .views import picture_review,AwardView,AwardNotifyView


urlpatterns = patterns('',
    url(r'^review/$',picture_review),
    url(r'^award/(?P<uid>\d+)/$', AwardView.as_view()),
    url(r'^referal/notify/$', AwardNotifyView.as_view()),
)


