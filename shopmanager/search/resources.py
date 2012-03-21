from djangorestframework.resources import ModelResource
from shopback.base.serializer import ChartSerializer

class SearchResource(ModelResource):
    """ docstring for SearchResource ModelResource """

    fields = (('charts','ChartSerializer'),('item_dict',None))
    #exclude = ('url',)


  