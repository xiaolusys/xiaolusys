#-*- coding:utf8 -*-
from django import template

register = template.Library()

@register.filter(name='format_dt')  
def format_dt(dt): 
    return '%s%d,%s'%('周',dt.date().isoweekday(),dt.strftime("%H时%M分"))

@register.filter(name='int_to_list')  
def int_to_list(value): 
    assert isinstance(value,int)
    return range(0,value)  