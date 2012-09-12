__author__ = 'meixqhi'
from djangorestframework.resources import ModelResource
from shopback.base.serializer import ChartSerializer

class ChartsResource(ModelResource):
    """ docstring for TradeResource ModelResource """

    fields = (('charts','ChartSerializer'),('item_dict',None),('skus',None))
    #exclude = ('url',)
    
class BaseResource(ModelResource):
    """ docstring for TradeResource ModelResource """

    #fields = (('charts','ChartSerializer'),('item_dict',None))
    exclude = ('url',) 