# coding:utf-8
__author__ = 'yann'
from django.shortcuts import render_to_response
import datetime
from django.template import RequestContext
from django.views.generic import View
from django.db import connection
import functions


class RecordPointView(View):

    def get(self, request):
        print "eeeeeee"
        return render_to_response("dinghuo/data_of_point.html",
                                  {},
                                  context_instance=RequestContext(request))