

class ChartSerializer(object):
    """ docstring for class ChartSerializer """

    #     __metaclass__ = _RegisterSerializer

    def serialize(self, obj):
        """
        Convert any object into a serializable representation.
        """
        pass
        # if isinstance(obj, (PivotChart, Chart)):
        #     # Char instances & PivotChart instances
        #     return obj
        # elif isinstance(obj, (tuple, list)):
        #     return self.serialize_iter(obj)
        # else:
        #     return super(ChartSerializer, self).serialize(obj)
