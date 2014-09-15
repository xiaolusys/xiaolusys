#!/usr/bin/env python 
#coding:utf-8

from django import template

register = template.Library()
@register.filter(name='displayName')
def displayName(value, arg):
    if not value:
        return ''
    return apply(eval('value.get_'+arg+'_display'), ())

