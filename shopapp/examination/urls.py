# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url

urlpatterns = patterns('shopapp.examination.views',
                       url(r'^examination_user/$', 'examination_user'),

                       url(r'^start_exam/$', 'start_exam'),
                       url(r'^write_select_paper/$', 'write_select_paper'),
                       #    url(r'^correct_problem_count/$','correct_problem_count'),

                       )
