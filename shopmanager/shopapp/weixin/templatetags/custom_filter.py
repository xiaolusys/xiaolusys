#!/usr/bin/env python 
#coding:utf-8
import re
from django import template

register = template.Library()
@register.filter(name='displayName')
def displayName(value, arg):
    if not value:
        return ''
    return apply(eval('value.get_'+arg+'_display'), ())

@register.filter(name='regexReplace')
def regexReplace(value, arg=''):
    if not value:
        return ''
    reg = re.compile(arg)
    return re.sub(reg,'*',value)

