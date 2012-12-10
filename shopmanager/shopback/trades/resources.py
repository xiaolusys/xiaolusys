__author__ = 'meixqhi'
from djangorestframework.resources import ModelResource
from shopback.trades.serializer import MergeTradetSerializer

class TradeResource(ModelResource):
    """ docstring for TradeResource TradeResource """

    fields = ('trade','logistics')
    exclude = ('url',) 
    
class OrderPlusResource(ModelResource):
    """ docstring for TradeResource ModelResource """

    #fields = (('charts','ChartSerializer'),('item_dict',None))
    exclude = ('url',) 