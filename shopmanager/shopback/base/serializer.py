from django.db import models
from django.db.models.query import QuerySet
from django.db.models.fields.related import RelatedField
from django.utils.encoding import smart_unicode, is_protected_type, smart_str

import decimal
import inspect
import types
from chartit import Chart, PivotChart


class ChartSerializer(object):
    """ docstring for class ChartSerializer """

    #     __metaclass__ = _RegisterSerializer

    def serialize(self, obj):
        """
        Convert any object into a serializable representation.
        """
        if isinstance(obj, (PivotChart, Chart)):
            # Char instances & PivotChart instances
            return obj
        elif isinstance(obj, (tuple, list)):
            return self.serialize_iter(obj)
        else:
            return super(ChartSerializer, self).serialize(obj)
