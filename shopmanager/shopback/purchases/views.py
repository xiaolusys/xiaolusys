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
from shopback.base.models import NORMAL,DELETE

class PurchaseItemView(InstanceModelView):
    """ docstring for PurchaseItemView """
    queryset = None
    
    def get(self, request, *args, **kwargs):
        #获取单库存商品信息
        model = self.resource.model

        try:
            if args:
                # If we have any none kwargs then assume the last represents the primrary key
                self.model_instance = model.objects.get(pk=args[-1], **kwargs)
            else:
                # Otherwise assume the kwargs uniquely identify the model
                filtered_keywords = kwargs.copy()
                if BaseRenderer._FORMAT_QUERY_PARAM in filtered_keywords:
                    del filtered_keywords[BaseRenderer._FORMAT_QUERY_PARAM]
                self.model_instance = model.objects.get(**filtered_keywords)
        except model.DoesNotExist:
            raise ErrorResponse(status.HTTP_404_NOT_FOUND)
        
        item_dict = {}
        item_dict['purchase_item'] =  Serializer().serialize(self.model_instance)
        item_dict['purchase_item']['purchase_productskus'] = Serializer().serialize(self.model_instance.purchase_productskus.all())
        item_dict['layer_table'] = render_to_string('purchases/purchaseitemtable.html', { 'object':item_dict['purchase_item']})
        
        return item_dict
 
    
    def get_queryset(self):
        return self.queryset
    
    