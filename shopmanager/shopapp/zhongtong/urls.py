__author__ = 'timi06'
# coding: utf-8
from django.conf.urls import patterns,url
import views,html_to_pdf

urlpatterns = patterns('',

    url(r'^scan/$',views.ztprint, name="ztprint"),
    url(r'^ztdd/$', views.orderlist, name="ztdd"),
    url(r'^ztoprint/$', html_to_pdf.ztoprint, name="ztoprint"),
)