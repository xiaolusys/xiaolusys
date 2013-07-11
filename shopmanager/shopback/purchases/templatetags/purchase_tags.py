#-*- coding:utf8 -*-
from django import template
from django.contrib.admin.templatetags.admin_list import result_headers,result_hidden_fields,results
from shopback import paramconfig as pcfg
from shopback.trades import permissions as perms
from shopback.purchases.models import Purchase,PurchaseItem,PurchaseStorage,PurchaseStorageItem


register = template.Library()

@register.filter    
def subtract(value, arg):
    return value - arg