# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url
from django.views.decorators.csrf import csrf_exempt

from .views import (picture_review,
                    AwardView,
                    AwardNotifyView,
                    AwardRemindView,
                    AwardApplyView,
                    AwardShareView,
                    LinkShareView)

urlpatterns = patterns('',
                       url(r'^review/$', picture_review),
                       url(r'^award/$', AwardView.as_view()),
                       url(r'^award/notify/$', AwardNotifyView.as_view()),
                       url(r'^award/remind/$', AwardRemindView.as_view()),
                       url(r'^award/apply/$', AwardApplyView.as_view()),
                       url(r'^award/share/(?P<pk>\d+)/$', AwardShareView.as_view()),

                       url(r'^link/share/$', csrf_exempt(LinkShareView.as_view())),
                       )
