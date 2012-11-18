#-*- coding:utf8 -*-
from django.db import models
from django.db.models.query import QuerySet
from django.db.models.fields.related import RelatedField
from djangorestframework.serializer import Serializer,_RegisterSerializer,_SkipField
from django.utils.encoding import smart_unicode, is_protected_type, smart_str
from shopback.items.models import ProductSku


import decimal
import inspect
import types
import json
import datetime

class ProductSerializer(Serializer):
    """ docstring for class ChartSerializer """

    __metaclass__ = _RegisterSerializer

    def serialize_model(self, instance):
        """
        Given a model instance or dict, serialize it to a dict..
        """
        data = {}
        fields = self.get_fields(instance)

        # serialize each required field 
        for fname in fields:
            if fname == 'product':
                continue
            elif hasattr(self, smart_str(fname)):
                # check first for a method 'fname' on self first
                meth = getattr(self, fname)
                if inspect.ismethod(meth) and len(inspect.getargspec(meth)[0]) == 2:
                    obj = meth(instance)

            elif hasattr(instance, '__contains__') and fname in instance:
                # check for a key 'fname' on the instance
                obj = instance[fname]
            elif hasattr(instance, smart_str(fname)):
                # finally check for an attribute 'fname' on the instance
                obj = getattr(instance, fname)
            else:
                continue
            
            try:
                key = self.serialize_key(fname)
                val = self.serialize_val(fname, obj)
                data[key] = val
            except _SkipField:
                pass

        return data


class ItemSerializer(Serializer):
    """ docstring for class ChartSerializer """

    __metaclass__ = _RegisterSerializer

    def serialize_model(self, instance):
        """
        Given a model instance or dict, serialize it to a dict..
        """
        data = {}

        fields = self.get_fields(instance)

        # serialize each required field 
        for fname in fields:
            if fname in ('buyer_credit','seller_credit','top_session','top_parameters',
                         'top_appkey','user_permissions','password','groups'):
                continue
            elif fname == 'skus':
                skus = instance.get(fname,'null') or 'null'
                obj=json.loads(skus)
            elif fname == 'user':
                user = instance.get(fname,None)
                if user and user.has_key('top_session'):
                    obj = user
            elif fname in ('list_time','delist_time'):
                dt = instance.get(fname)
                if isinstance(dt,datetime.datetime):
                    obj = '%s%d,%s'%('周',dt.date().isoweekday(),dt.strftime("%H时%M分"))
            elif hasattr(self, smart_str(fname)):
                # check first for a method 'fname' on self first
                meth = getattr(self, fname)
                if inspect.ismethod(meth) and len(inspect.getargspec(meth)[0]) == 2:
                    obj = meth(instance)

            elif hasattr(instance, '__contains__') and fname in instance:
                # check for a key 'fname' on the instance
                obj = instance[fname]
            elif hasattr(instance, smart_str(fname)):
                # finally check for an attribute 'fname' on the instance
                obj = getattr(instance, fname)
            else:
                continue
            
            try:
                key = self.serialize_key(fname)
                val = self.serialize_val(fname, obj)
                data[key] = val
            except _SkipField:
                pass

        return data
    
    