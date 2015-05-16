# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('flashsale.mmexam.views',
    #url(r'^examination_user/$','examination_user'),
    
   # url(r'^start_exam/$','start_exam'),
    url(r'^$','index',name='index'),
    url(r'^mmexam/(?P<question_id>\d+)/$','exam',name='exam'),
#    url(r'^correct_problem_count/$','correct_problem_count'),


    
)


