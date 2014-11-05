#-*- coding:utf8 -*-
import os,re,json
import datetime
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.db.models import Sum,Count,Max
from djangorestframework import status
from djangorestframework.response import Response,ErrorResponse
from shopback import paramconfig as pcfg
from shopback.base import log_action, ADDITION, CHANGE
from shopback.base.views import ModelView,FileUploadView
from .models import InterceptTrade

class InterceptByCsvFileView(FileUploadView):
    
    file_path     = 'trade'
    filename_save = 'intercept_%s.csv'
    
    def get(self, request, *args, **kwargs):
        pass
    
    def getNick(self,row):
        return row[0]
    
    def getMobile(self,row):
        return row[1]
    
    def getSerial(self,row):
        return row[2]
    
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
                
        return {'success':True,
                'redirect_url':reverse('admin:intercept_intercepttrade_changelist')}
    
    
    