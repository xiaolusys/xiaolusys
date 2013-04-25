#-*- coding:utf8 -*-
from django.conf.urls import patterns
from django.views.generic import TemplateView

urlpatterns = patterns('',
    (r'^', TemplateView.as_view(template_name="fullcalendar/default.html")),
)