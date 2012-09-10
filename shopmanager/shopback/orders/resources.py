__author__ = 'meixqhi'
from djangorestframework.resources import ModelResource

class ChartJsonResource(ModelResource):
    """ docstring for TradeResource ModelResource """

    #fields = (('charts','ChartSerializer'),('item_dict',None))
    exclude = ('url',) 
    
 