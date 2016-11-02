__author__ = 'timi06'
# coding: utf-8
import html_to_pdf
import views
from django.conf.urls import patterns, url

urlpatterns = patterns('',

                       url(r'^scan/$', views.ztprint, name="ztprint"),
                       url(r'^ztdd/$', views.orderlist, name="ztdd"),
                       url(r'^ztoprint/$', html_to_pdf.ztoprint, name="ztoprint"),
                       )
