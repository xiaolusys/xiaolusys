__author__ = 'timi06'
# coding: utf-8
from django.conf.urls import patterns,url
from shopmanager.shopapp.zhongtong import html_to_pdf
import views

urlpatterns = patterns('',

    url(r'^scan/$',views.ztprint, name="ztprint"),
    url(r'^dzmd/$', html_to_pdf.runprint, name="dzmd")
)