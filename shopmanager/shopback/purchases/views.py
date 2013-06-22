#-*- coding:utf8 -*-
import datetime
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.template.loader import render_to_string
from djangorestframework.serializer import Serializer
from djangorestframework.utils import as_tuple
from djangorestframework import status
from djangorestframework.renderers import BaseRenderer
from djangorestframework.response import Response
from djangorestframework.mixins import CreateModelMixin
from djangorestframework.views import ModelView,ListOrCreateModelView,InstanceModelView
from shopback.archives.models import Deposite,Supplier,PurchaseType
from shopback import paramconfig as pcfg

class PurchaseItemView(InstanceModelView):
    """ docstring for PurchaseItemView """
    queryset = None
    
    def get(self, request, *args, **kwargs):
        #获取单库存商品信息
        
        
        return item_dict
    
    def post(self, request, *args, **kwargs):
        
        pass
    
    def get_queryset(self):
        return self.queryset
    
    
class PurchaseInstanceView(ModelView):
    
    def get(self, request, *args, **kwargs):
        
        params = {}
        params['suppliers']      = Supplier.objects.filter(in_use=True)
        params['deposites']      = Deposite.objects.filter(in_use=True)
        params['purchase_types'] = PurchaseType.objects.filter(in_use=True)
        
        return params
    
    def post(self, request, *args, **kwargs):
        
        pass
    
    