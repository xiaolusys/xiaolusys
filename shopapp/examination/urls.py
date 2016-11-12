# -*- coding: utf-8 -*-

from django.conf.urls import url
from shopapp.examination.views import *

urlpatterns = [
    url(r'^examination_user/$', examination_user),
    url(r'^start_exam/$', start_exam),
    url(r'^write_select_paper/$', write_select_paper),
    #    url(r'^correct_problem_count/$','correct_problem_count'),
]
