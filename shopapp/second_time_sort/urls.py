# -*- coding: utf-8 -*-

from django.conf.urls import url
from django.contrib import admin

from shopapp.second_time_sort.views import *

admin.autodiscover()

urlpatterns = [
    url(r'^batch_number/$', batch_number),
    url(r'^batch_pick/$', batch_pick),
    url(r'^out_sid_batch/', out_sid_batch),
    url(r'^drop_out_batch/', drop_out_batch),
    url(r'^merger_out_sid/', merger_out_sid),
    #    url(r'^start_exam/$','start_exam'),
    #    url(r'^write_select_paper/$','write_select_paper'),
    #    url(r'^correct_problem_count/$','correct_problem_count'),
]
