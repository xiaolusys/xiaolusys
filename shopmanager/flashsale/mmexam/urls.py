# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, url
from django.views.generic import TemplateView

from . import views
from . import views_dress

urlpatterns = patterns('',
    # url(r'^examination_user/$','examination_user'),
    # url(r'^start_exam/$','start_exam'),
    url(r'^$', views.index, name='index'),
    url(r'^mmexam/(?P<question_id>\d+)/$', views.exam, name='exam'),
    # url(r'^correct_problem_count/$','correct_problem_count'),
    
    url(r'^dress/$',TemplateView.as_view(template_name="mmdress/dress_entry.html")),
    url(r'^dress/userinfo/$',views_dress.DressUserinfoView.as_view(),name="dress_userinfo")
)


