#-*- coding:utf8 -*-
import os,re,json
import datetime
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.db.models import Sum,Count,Max
#from djangorestframework import status
#from djangorestframework.response import Response,ErrorResponse
from shopback import paramconfig as pcfg
from shopback.base import log_action, ADDITION, CHANGE
from shopback.base.views import FileUploadView_intercept
from .models import InterceptTrade


from rest_framework.response import Response
from rest_framework import authentication
from rest_framework import permissions
from rest_framework.compat import OrderedDict
from rest_framework.renderers import JSONRenderer,TemplateHTMLRenderer,BrowsableAPIRenderer
from rest_framework.views import APIView
from rest_framework import filters
from rest_framework import authentication
from . import serializers 
from shopback.base.new_renders import new_BaseJSONRenderer

class InterceptByCsvFileView(FileUploadView_intercept):
    
    serializer_class = serializers.InterceptTradeSerializer
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (new_BaseJSONRenderer,BrowsableAPIRenderer)
    authentication_classes = (authentication.BasicAuthentication,)
    #print "444hhh666"
    file_path     = 'trade'
    filename_save = 'intercept_%s.csv'
    
    def get(self, request, *args, **kwargs):
        pass
        #print "get"
        return Response({"nofunction":"get---function"})
    def getNick(self,row):
        return Response(row[0])
    
    def getMobile(self,row):
        return Response(row[1])
    
    def getSerial(self,row):
        return Response(row[2])
    
    def createInterceptRecord(self,row):
        
        if not (self.getNick(row) or self.getMobile(row) or self.getSerial(row)):
            return 
        
        InterceptTrade.objects.create(buyer_nick=self.getNick(row),
                                      buyer_mobile=self.getMobile(row),
                                      serial_no=self.getSerial(row),)
    
    def handle_post(self,request,csv_iter):
        
        encoding = self.getFileEncoding(request)
        
        for row in csv_iter:
            row = [r.strip().decode(encoding) for r in row]
            self.createInterceptRecord(row)
                
        return Response({'success':True,
                'redirect_url':reverse('admin:intercept_intercepttrade_changelist')})
    
    
    