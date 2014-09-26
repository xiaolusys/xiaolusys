# -*- coding: utf-8 -*-

from django.conf.urls.defaults import patterns, url
from .views import picture_review

urlpatterns = patterns('',
    url(r'^review/$',picture_review),
)


