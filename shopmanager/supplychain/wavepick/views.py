# Create your views here.

from django.views.generic import View
from django.http import Http404,HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext

import json


class WaveView(View):
    def get(self, request, wave_id):

        response = render_to_response('wave_detail.html', 
                                      {"wave_id":wave_id}, 
                                      context_instance=RequestContext(request))
        return response


class AllocateView(View):
    def get(self, request, wave_id):

        response = render_to_response('allocate_detail.html', 
                                      {"wave_id":wave_id}, 
                                      context_instance=RequestContext(request))
        return response
