#-*- coding:utf8 -*-
import datetime

from django.db import models
from django.utils.encoding import smart_unicode, force_unicode

from shopback import paramconfig as pcfg
from shopback.base.options import SimpleListFilter
from shopback.items.models import Product

class ChargerFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    title = u'接管状态'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'charger'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return (('mycharge',u'我接管的'),
                ('uncharge',u'未接管的'),)
    

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        status_name  = self.value()
        myuser_name  = request.user.username
        if not status_name:
            return queryset
        elif status_name == 'mycharge':
            return queryset.filter(models.Q(sale_charger=myuser_name)|models.Q(storage_charger=myuser_name))
                                   
        else:
            return queryset.exclude(sale_charger=myuser_name).exclude(storage_charger=myuser_name)
        
        
        
        