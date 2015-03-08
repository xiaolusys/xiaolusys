# -*- coding: utf-8 -*-

from django.conf.urls.defaults import patterns, url
from .views import (picture_review,
                    AwardView,
                    AwardNotifyView,
                    AwardRemindView,
                    AwardApplyView,
                    AwardShareView)


urlpatterns = patterns('',
    url(r'^review/$',picture_review),
    url(r'^award/$', AwardView.as_view()),
    url(r'^award/notify/$', AwardNotifyView.as_view()),
    url(r'^award/remind/$', AwardRemindView.as_view()),
    url(r'^award/apply/$', AwardApplyView.as_view()),
    url(r'^award/share/(?P<pk>\d+)/$', AwardShareView.as_view()),
    
    
)


