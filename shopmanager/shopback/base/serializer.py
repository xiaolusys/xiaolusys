from djangorestframework.serializer import Serializer,_RegisterSerializer
from chartit import Chart,PivotChart


class ChartSerializer(Serializer):
    """ docstring for class ChartSerializer """

    __metaclass__ = _RegisterSerializer

    def serialize(self, obj):
        """
        Convert any object into a serializable representation.
        """
        if isinstance(obj,(PivotChart,Chart)):
            #Char instances & PivotChart instances
            return  obj
        elif isinstance(obj,(tuple,list)):
            return self.serialize_iter(obj)
        else:
            super(ChartSerializer,self).serialize(obj)

  